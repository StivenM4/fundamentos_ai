"""Endpoints de autoservicio para creación y edición de tickets por el usuario final.

Permite radicar nuevos incidentes (en formato JSON o formulario multipart con imagen de evidencia),
actualizar datos del reporte y consultar el estado actual del ticket.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError

from backend.database import (
    create_ticket_usuario,
    get_ticket_usuario,
    update_ticket_usuario,
)
from backend.schemas import (
    TicketDetalleResponse,
    TicketUsuarioCreate,
    TicketUsuarioUpdate,
)
from backend.services import analyze_ticket, procesar_captura_multimodal

router = APIRouter(
    prefix="/api/usuario/tickets",
    tags=["Usuario - Tickets"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOADS_DIR = PROJECT_ROOT / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


from backend.utils.form_helpers import process_form_image_with_fallback


@router.post(
    "",
    response_model=TicketDetalleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo ticket de soporte por el usuario",
)
async def crear_ticket_usuario_endpoint(request: Request) -> TicketDetalleResponse:
    """Crea un nuevo ticket de soporte reportado por el usuario final.

    Soporta JSON ("application/json") y formularios ("multipart/form-data") con captura adjunta ("imagen", "file" o "image").
    """
    content_type = request.headers.get("content-type", "").lower()
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    v_analysis = None
    sugerencia_ia = None

    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error decodificando formulario multipart: {exc}",
            )

        titulo = form.get("titulo")
        descripcion = form.get("descripcion")
        imagen_url = form.get("imagen_url")
        image_file = form.get("imagen") or form.get("file") or form.get("image")

        img_url_res, v_analysis, descripcion = await process_form_image_with_fallback(image_file, descripcion)
        if img_url_res:
            imagen_url = img_url_res

    else:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=[{"loc": ["body"], "msg": "JSON inválido o cuerpo vacío", "type": "value_error.json"}],
            )
        try:
            schema_data = TicketUsuarioCreate(**body)
            titulo = schema_data.titulo
            descripcion = schema_data.descripcion
            imagen_url = schema_data.imagen_url
        except ValidationError as ve:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=ve.errors(),
            )

    if not titulo or not str(titulo).strip() or not descripcion or not str(descripcion).strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[
                {
                    "loc": ["body", "titulo"],
                    "msg": "Los campos 'titulo' y 'descripcion' son obligatorios y no pueden estar vacíos.",
                    "type": "value_error.missing",
                }
            ],
        )

    if v_analysis is None and imagen_url:
        img_p = PROJECT_ROOT / str(imagen_url).lstrip("/\\")
        if img_p.is_file() and img_p.exists():
            try:
                v_analysis = procesar_captura_multimodal(img_p.read_bytes(), img_p.name)
            except Exception:
                pass

    if v_analysis is not None:
        try:
            ai_res = analyze_ticket(
                subject=str(titulo).strip(),
                description=str(descripcion).strip(),
                visual_analysis=v_analysis,
            )
            sugerencia_ia = ai_res
        except Exception as exc:
            print(f"Advertencia ejecutando analyze_ticket al crear ticket: {exc}")

    ticket = create_ticket_usuario(
        titulo=str(titulo).strip(),
        descripcion=str(descripcion).strip(),
        imagen_url=str(imagen_url).strip() if imagen_url else None,
        sugerencia_ia=sugerencia_ia,
    )

    return TicketDetalleResponse(**ticket)


@router.put(
    "/{ticket_id}",
    response_model=TicketDetalleResponse,
    status_code=status.HTTP_200_OK,
    summary="Editar información de un ticket por el usuario",
)
async def editar_ticket_usuario_endpoint(
    ticket_id: int,
    request: Request,
) -> TicketDetalleResponse:
    """Actualiza el título, la descripción o la imagen adjunta de un ticket ya radicado."""
    content_type = request.headers.get("content-type", "").lower()
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None

    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error decodificando formulario multipart: {exc}",
            )
        titulo = form.get("titulo")
        descripcion = form.get("descripcion")
        imagen_url = form.get("imagen_url")
        image_file = form.get("imagen") or form.get("file") or form.get("image")
        img_url_res, _, descripcion = await process_form_image_with_fallback(image_file, descripcion)
        if img_url_res:
            imagen_url = img_url_res

    else:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=[{"loc": ["body"], "msg": "JSON inválido o cuerpo vacío", "type": "value_error.json"}],
            )
        try:
            update_data = TicketUsuarioUpdate(**body)
            titulo = update_data.titulo
            descripcion = update_data.descripcion
            imagen_url = update_data.imagen_url
        except ValidationError as ve:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=ve.errors(),
            )

    updated = update_ticket_usuario(
        ticket_id=ticket_id,
        titulo=str(titulo).strip() if titulo is not None else None,
        descripcion=str(descripcion).strip() if descripcion is not None else None,
        imagen_url=str(imagen_url).strip() if imagen_url is not None else None,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket con ID {ticket_id} no fue encontrado.",
        )

    return TicketDetalleResponse(**updated)


@router.get(
    "/{ticket_id}",
    response_model=TicketDetalleResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de un ticket por ID",
)
def obtener_ticket_usuario_endpoint(ticket_id: int) -> TicketDetalleResponse:
    """Consulta la información detallada de un ticket para la vista del usuario final."""
    ticket = get_ticket_usuario(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket con ID {ticket_id} no fue encontrado.",
        )
    return TicketDetalleResponse(**ticket)

