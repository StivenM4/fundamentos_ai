from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status

from backend.database import (
    get_ticket_usuario,
    list_tickets_usuario,
    save_guia_ia_ticket_usuario,
    update_ticket_tecnico,
)
from backend.schemas import (
    TicketDetalleResponse,
    TicketGuiaIaResponse,
    TicketTecnicoUpdate,
    VisualAnalysis,
)
from backend.services import analyze_ticket, procesar_captura_multimodal

router = APIRouter(
    prefix="/api/tecnico/tickets",
    tags=["Tecnico - Tickets"],
)

from backend.utils.media_helpers import (
    buscar_archivo_imagen,
    resolver_visual_analysis_ticket,
    _buscar_archivo_imagen,
    _resolver_visual_analysis_ticket,
)


@router.get(
    "",
    response_model=List[TicketDetalleResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todos los tickets de usuarios desde BD",
)
def listar_tickets_tecnico_endpoint() -> List[TicketDetalleResponse]:
    """Trae todos los tickets registrados en la mesa de ayuda ordenados por fecha descendente."""
    tickets = list_tickets_usuario()
    return [TicketDetalleResponse(**t) for t in tickets]


@router.get(
    "/{ticket_id}",
    response_model=TicketDetalleResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de un ticket en la consola técnica",
)
def obtener_ticket_tecnico_endpoint(ticket_id: int) -> TicketDetalleResponse:
    """Consulta la información completa de un ticket para la vista del técnico especialista."""
    ticket = get_ticket_usuario(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket con ID {ticket_id} no fue encontrado.",
        )

    sug_ia = ticket.get("sugerencia_ia") if isinstance(ticket.get("sugerencia_ia"), dict) else {}
    tiene_va_en_sug = bool(sug_ia.get("visual_analysis"))

    v_analysis = _resolver_visual_analysis_ticket(ticket)
    if v_analysis is not None:
        ticket["visual_analysis"] = v_analysis
        # Si el ticket no traía análisis visual en la sugerencia, corremos el análisis multimodal y persistimos
        if not tiene_va_en_sug:
            try:
                titulo = ticket.get("titulo", "")
                descripcion = ticket.get("descripcion", "")
                ai_res = analyze_ticket(
                    subject=titulo,
                    description=descripcion,
                    visual_analysis=v_analysis,
                )
                ticket["sugerencia_ia"] = ai_res
                classification = ai_res.get("classification", {})
                if not ticket.get("criticidad_sugerida"):
                    ticket["criticidad_sugerida"] = classification.get("priority")
                if not ticket.get("area_sugerida"):
                    ticket["area_sugerida"] = classification.get("category")
                if not ticket.get("confianza"):
                    ticket["confianza"] = float(classification.get("confidence_score", 0.9))
                # Guardamos la inferencia completa en PostgreSQL para que no toque recalcularla
                save_guia_ia_ticket_usuario(ticket_id=ticket_id, guia=ai_res)
            except Exception as exc:
                print(f"Error recalculando inferencia multimodal en obtener_ticket_tecnico: {exc}")
    else:
        if ticket.get("sugerencia_ia") and isinstance(ticket["sugerencia_ia"], dict):
            ticket["visual_analysis"] = ticket["sugerencia_ia"].get("visual_analysis")

    return TicketDetalleResponse(**ticket)


@router.put(
    "/{ticket_id}",
    response_model=TicketDetalleResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar solución y parámetros técnicos de un ticket",
)
def actualizar_ticket_tecnico_endpoint(
    ticket_id: int,
    data: TicketTecnicoUpdate,
) -> TicketDetalleResponse:
    """Guarda la solución documentada, reasigna área o criticidad y actualiza el estado operativo del ticket."""
    updated = update_ticket_tecnico(
        ticket_id=ticket_id,
        solucion_pasos=data.solucion_pasos,
        criticidad=data.criticidad,
        area_asignada=data.area_asignada,
        es_incidente=data.es_incidente,
        estado=data.estado,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket con ID {ticket_id} no fue encontrado.",
        )
    return TicketDetalleResponse(**updated)


@router.post(
    "/{ticket_id}/guia-ia",
    response_model=TicketGuiaIaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener y guardar la guía de resolución generada por los motores de IA",
)
def generar_guia_ia_endpoint(ticket_id: int) -> TicketGuiaIaResponse:
    """Calcula la recomendación integral de IA (clasificación, ruta A*, SOP y causa raíz) y la guarda en la base de datos."""
    ticket = get_ticket_usuario(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket con ID {ticket_id} no fue encontrado.",
        )

    titulo = ticket.get("titulo", "")
    descripcion = ticket.get("descripcion", "")

    # Si el ticket tiene captura adjunta, resolvemos el análisis visual y OCR
    v_analysis = _resolver_visual_analysis_ticket(ticket)

    # Pasamos el ticket y la evidencia visual por todo el pipeline de IA
    ai_res = analyze_ticket(
        subject=titulo,
        description=descripcion,
        visual_analysis=v_analysis,
    )

    classification = ai_res.get("classification", {})
    criticidad_sugerida = classification.get("priority", "MEDIA")
    area_sugerida = classification.get("category", "Soporte TI")
    confianza = float(classification.get("confidence_score", 0.90))

    # Evaluamos si califica como incidente según criticidad o palabras clave
    es_incidente_sugerido = bool(
        criticidad_sugerida.upper() in ("CRÍTICA", "CRITICA", "ALTA")
        or "incidente" in f"{titulo} {descripcion}".lower()
        or ai_res.get("es_incidente", True)
    )

    # Extraemos la secuencia de pasos calculada por la búsqueda A*
    pasos_solucion: List[str] = []
    astar_route = ai_res.get("astar_route", {})
    if astar_route and "steps" in astar_route:
        for s in astar_route["steps"]:
            title = s.get("title", "")
            desc = s.get("description", "")
            role = s.get("role", "")
            if desc and role:
                pasos_solucion.append(f"[{role}] {title}: {desc}")
            elif desc:
                pasos_solucion.append(f"{title}: {desc}")
            elif title:
                pasos_solucion.append(title)

    rag_sop = ai_res.get("rag_sop", {})
    if not pasos_solucion and rag_sop and "checklist" in rag_sop:
        pasos_solucion = list(rag_sop.get("checklist", []))

    # Consolidamos el análisis de causa raíz con los activadores léxicos y el costo A*
    lex_evidence = classification.get("lexical_evidence", [])
    lex_str = ", ".join(lex_evidence) if lex_evidence else "Análisis léxico contextual"
    analisis_causa = (
        f"Clasificado en '{area_sugerida}' con severidad '{criticidad_sugerida}'. "
        f"Activadores léxicos: {lex_str}. "
        f"Costo heurístico óptimo A*: {astar_route.get('total_cost', 6)}."
    )

    tiene_manual = bool(rag_sop and rag_sop.get("similarity_score", 0) > 0)
    manual_titulo = rag_sop.get("title") if tiene_manual else None
    manual_precauciones = rag_sop.get("precautions") if tiene_manual else None
    manual_checklist = rag_sop.get("checklist", []) if tiene_manual else []
    manual_id = rag_sop.get("runbook_id") if tiene_manual else None

    guia_dict: Dict[str, Any] = {
        "criticidad_sugerida": criticidad_sugerida,
        "area_sugerida": area_sugerida,
        "es_incidente_sugerido": es_incidente_sugerido,
        "confianza": confianza,
        "pasos_solucion": pasos_solucion,
        "analisis_causa": analisis_causa,
        "tiene_manual": tiene_manual,
        "manual_titulo": manual_titulo,
        "manual_precauciones": manual_precauciones,
        "manual_checklist": manual_checklist,
        "manual_id": manual_id,
        "visual_analysis": v_analysis,
    }

    # Guardamos la guía generada en la base de datos para consulta rápida del técnico
    save_guia_ia_ticket_usuario(ticket_id=ticket_id, guia=guia_dict)

    return TicketGuiaIaResponse(**guia_dict)

