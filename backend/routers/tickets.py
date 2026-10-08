from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Metemos la raíz al "sys.path" para resolver "src" y paquetes hermanos sin lío
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from pydantic import ValidationError

from backend.schemas import (
    TemplateItem,
    TicketRequest,
    TicketResponse,
    VisionPipelineResponse,
)
from backend.services import (
    analyze_ticket,
    procesar_captura_multimodal,
    procesar_captura_semana08,
    procesar_pipeline_vision_semana09,
    train_model,
)

router = APIRouter(
    prefix="/api/tickets",
    tags=["Tickets"],
)

# Plantillas predefinidas con casos típicos de mesa de ayuda para pruebas rápidas
PREDEFINED_TEMPLATES: List[TemplateItem] = [
    TemplateItem(
        id="db_crash",
        subject="Caída de Base de Datos Producción",
        description=(
            "El cluster de base de datos PostgreSQL de producción se detuvo repentinamente con alarma "
            "de timeout en el pool de conexiones. Todas las operaciones de facturación y ERP quedaron congeladas."
        ),
        category="Base de Datos / Infraestructura",
        priority="CRÍTICA",
    ),
    TemplateItem(
        id="vpn_fail",
        subject="Problema de VPN y Acceso Remoto",
        description=(
            "Múltiples colaboradores de la sede remota reportan que el cliente VPN FortiClient "
            "rechaza la autenticación con error de certificado vencido y desconexión recurrente en el túnel."
        ),
        category="Redes & Comunicaciones",
        priority="ALTA",
    ),
    TemplateItem(
        id="erp_lag",
        subject="Lentitud Crítica en ERP y Facturación",
        description=(
            "Los usuarios de tesorería y contabilidad experimentan congelamiento y tiempos de espera superiores "
            "a 90 segundos al intentar emitir recibos y facturas electrónicas con la base de datos."
        ),
        category="Software & Aplicaciones",
        priority="ALTA",
    ),
    TemplateItem(
        id="phishing",
        subject="Ataque o Sospecha de Phishing",
        description=(
            "Se detectó un correo fraudulento suplantando a la gerencia financiera solicitando transferencias "
            "bancarias urgentes y cambio inmediato de contraseñas de dominio a varios empleados."
        ),
        category="Seguridad & Accesos",
        priority="CRÍTICA",
    ),
    TemplateItem(
        id="printer",
        subject="Falla en Servidor de Impresión",
        description=(
            "La cola de impresión de la gerencia general está trabada con múltiples documentos pendientes "
            "y el servicio spooler no procesa las solicitudes de contratos urgentes."
        ),
        category="Hardware & Periféricos",
        priority="MEDIA",
    ),
]


@router.get(
    "/templates",
    response_model=List[TemplateItem],
    summary="Catálogo de plantillas predefinidas de tickets de TI",
    tags=["Tickets"],
)
def get_templates() -> List[TemplateItem]:
    """Devuelve las 5 plantillas predefinidas de incidentes para pruebas directas en la interfaz."""
    return PREDEFINED_TEMPLATES


@router.post(
    "/train",
    summary="Entrenar modelos de IA (alias)",
    tags=["Modelos"],
)
def train_tickets_alias(require_db: bool = False) -> Dict[str, Any]:
    """Ruta alias para lanzar el reentrenamiento de modelos desde "/api/tickets/train"."""
    try:
        res = train_model(require_db=require_db)
        return {
            "status": "success",
            "message": "Entrenamiento completado exitosamente desde la base de datos SQL.",
            "data": res,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo durante el entrenamiento desde la base de datos SQL: {str(exc)}",
        )


from backend.utils.form_helpers import parse_blocked_steps, process_upload_image


@router.post(
    "/analyze",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Análisis integral de ticket con pipeline de IA multimodal",
    tags=["Tickets"],
)
async def analyze_ticket_endpoint(request: Request) -> TicketResponse:
    """Procesa un ticket de soporte a través de todos los motores de IA del sistema.

    Acepta tanto JSON ("application/json") como formularios multipart ("multipart/form-data") con imagen adjunta.
    """
    content_type = request.headers.get("content-type", "").lower()

    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error decodificando formulario multipart: {err}",
            )

        subject = form.get("subject")
        description = form.get("description")

        if not subject or not str(subject).strip() or not description or not str(description).strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=[
                    {
                        "loc": ["body", "subject"],
                        "msg": "Los campos 'subject' y 'description' son obligatorios y no pueden ser vacíos.",
                        "type": "value_error.missing",
                    }
                ],
            )

        blocked_steps = parse_blocked_steps(form.get("blocked_steps"))
        visual_analysis = await process_upload_image(form.get("image"))

        try:
            raw_result = analyze_ticket(
                subject=str(subject),
                description=str(description),
                blocked_steps=blocked_steps,
                visual_analysis=visual_analysis,
            )
            return TicketResponse(**raw_result)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error durante el análisis del ticket con los motores IA: {str(exc)}",
            )

    else:
        # Si no es multipart, parseamos el payload como JSON estándar
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=[{"loc": ["body"], "msg": "JSON inválido o cuerpo vacío", "type": "value_error.json"}],
            )

        try:
            ticket_req = TicketRequest(**body)
        except ValidationError as ve:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=ve.errors(),
            )

        try:
            raw_result = analyze_ticket(
                subject=ticket_req.subject,
                description=ticket_req.description,
                blocked_steps=ticket_req.blocked_steps,
                visual_analysis=None,
            )
            return TicketResponse(**raw_result)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error durante el análisis del ticket con los motores IA: {str(exc)}",
            )


@router.post(
    "/analyze-multipart",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
    summary="Análisis interactivo con captura de pantalla (Swagger / Form Data)",
    tags=["Tickets"],
)
async def analyze_ticket_multipart_endpoint(
    subject: str = Form(..., description="Asunto o título representativo del incidente"),
    description: str = Form(..., description="Descripción detallada del incidente reportado"),
    blocked_steps: Optional[str] = Form(
        None, description="Nodos bloqueados para A* en formato JSON o lista separada por comas"
    ),
    image: Optional[UploadFile] = File(
        None, description="Captura de pantalla adjunta (BSOD, disco lleno, red, crash)"
    ),
) -> TicketResponse:
    """Endpoint para probar la subida de tickets con archivo adjunto directo desde Swagger o formularios web."""
    if not subject.strip() or not description.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Los campos 'subject' y 'description' son obligatorios y no pueden estar vacíos.",
        )

    blocked_list = parse_blocked_steps(blocked_steps)
    visual_analysis = await process_upload_image(image)

    try:
        raw_result = analyze_ticket(
            subject=subject,
            description=description,
            blocked_steps=blocked_list,
            visual_analysis=visual_analysis,
        )
        return TicketResponse(**raw_result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el análisis del ticket con los motores IA: {str(exc)}",
        )


@router.post(
    "/vision-pipeline",
    response_model=VisionPipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Diagnóstico interactivo de visión por computador (Semana 09)",
    tags=["Tickets"],
)
async def vision_pipeline_endpoint(
    image: UploadFile = File(..., description="Archivo de imagen para análisis de visión por computador"),
) -> VisionPipelineResponse:
    """Corre el pipeline completo de visión artificial (Semana 09) sobre la captura del incidente.

    - Filtro Canny con comparación multi-sigma.
    - Segmentación automática y binarización con método de Otsu.
    - Conteo y etiquetado de regiones conexas.
    - Extracción de texto de error mediante OCR con Tesseract.
    - Generación de artefactos visuales y diagnóstico sugerido.
    """
    if not image or not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere un archivo de imagen válido para ejecutar el pipeline de visión.",
        )

    file_bytes = await image.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo de imagen recibido está vacío.",
        )

    try:
        resultado = procesar_pipeline_vision_semana09(file_bytes, image.filename)
        return VisionPipelineResponse(**resultado)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo durante la ejecución del pipeline de visión de Semana 09: {str(exc)}",
        )


__all__ = [
    "router",
    "PREDEFINED_TEMPLATES",
    "get_templates",
    "analyze_ticket_endpoint",
    "analyze_ticket_multipart_endpoint",
    "vision_pipeline_endpoint",
    "train_tickets_alias",
]
