from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, List, Optional, Tuple
from fastapi import HTTPException, status
from backend.schemas import VisualAnalysis
from backend.services.vision import procesar_captura_multimodal

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_blocked_steps(blocked_raw: Any) -> List[str]:
    """Parsea y normaliza la lista de pasos bloqueados recibida desde el frontend.

    Acepta entradas en múltiples formatos para tolerar diferentes clientes HTTP:
    - Lista nativa de strings.
    - Cadena JSON serializada (ej. '["verificar_cambio_reciente"]').
    - Cadena separada por comas (CSV clásico).
    Retorna una lista de identificadores de nodo limpios para alimentar el algoritmo "A*".
    """
    if not blocked_raw:
        return []
    if isinstance(blocked_raw, list):
        return [str(x) for x in blocked_raw]
    if isinstance(blocked_raw, str):
        try:
            parsed = json.loads(blocked_raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
        return [s.strip() for s in blocked_raw.split(",") if s.strip()]
    return []


async def process_upload_image(
    image: Optional[Any],
    default_name: str = "captura.png",
) -> Optional[VisualAnalysis]:
    """Lee el flujo de bytes de un archivo subido ("UploadFile") y ejecuta la inferencia multimodal.

    Valida que el archivo contenga datos legibles y llama a "procesar_captura_multimodal".
    Si ocurre alguna excepción durante la decodificación o clasificación de la imagen,
    eleva un error HTTP 400 semántico para retroalimentar al cliente.
    """
    if image is None or not hasattr(image, "read"):
        return None
    file_bytes = await image.read()
    if not file_bytes:
        return None
    filename = getattr(image, "filename", default_name) or default_name
    try:
        return procesar_captura_multimodal(file_bytes, filename)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error durante el procesamiento visual de la captura: {str(exc)}",
        )


def save_fallback_upload_file(file_bytes: bytes, orig_filename: str) -> str:
    """Almacena la imagen en disco como mecanismo de contingencia cuando falla la inferencia de IA.

    Genera un nombre único con prefijo "ticket_usr_" en la carpeta "uploads/capturas_tickets"
    para no perder la evidencia gráfica enviada por el usuario final, retornando su URL pública.
    """
    capturas_dir = PROJECT_ROOT / "uploads" / "capturas_tickets"
    capturas_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(orig_filename).suffix or ".png"
    safe_name = f"ticket_usr_{uuid.uuid4().hex[:8]}{ext}"
    dest_path = capturas_dir / safe_name
    dest_path.write_bytes(file_bytes)
    return f"/uploads/capturas_tickets/{safe_name}"


async def process_form_image_with_fallback(
    image_file: Optional[Any],
    descripcion: Optional[str] = None,
) -> Tuple[Optional[str], Optional[VisualAnalysis], Optional[str]]:
    """Procesa la imagen adjunta de un formulario integrando el análisis visual y el texto OCR.

    Retorna una tupla de tres elementos:
    1. "imagen_url": URL pública del archivo guardado en el servidor.
    2. "v_analysis": Objeto "VisualAnalysis" con la clasificación y métricas (o None si falló).
    3. "desc_res": Descripción enriquecida concatenando el texto extraído por OCR ("Semana 09")
       para que los clasificadores de NLP aprovechen la información textual de la pantalla.
    Si el motor de visión falla por cualquier motivo, aplica la contingencia de guardado pasivo en disco.
    """
    if image_file is None or not hasattr(image_file, "read"):
        return None, None, descripcion
    file_bytes = await image_file.read()
    if not file_bytes:
        return None, None, descripcion

    orig_filename = getattr(image_file, "filename", "evidencia.png") or "evidencia.png"
    v_analysis = None
    imagen_url = None
    desc_res = descripcion

    try:
        v_analysis = procesar_captura_multimodal(file_bytes, orig_filename)
        imagen_url = v_analysis.image_url
        if v_analysis.ocr_text and str(v_analysis.ocr_text).strip():
            ocr_clean = str(v_analysis.ocr_text).strip()
            desc_base = str(descripcion).strip() if descripcion else ""
            desc_res = f"{desc_base}\n\n[Evidencia OCR S09]:\n{ocr_clean}".strip()
    except Exception:
        imagen_url = save_fallback_upload_file(file_bytes, orig_filename)

    return imagen_url, v_analysis, desc_res

