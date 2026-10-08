from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Metemos la raíz al "sys.path" para que resuelva paquetes sin importar desde dónde se invoque
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import APIRouter, HTTPException, Query, status

from backend.schemas import KnowledgeManualsResponse
from backend.services import get_knowledge_manuals

router = APIRouter(
    prefix="/api/knowledge",
    tags=["Knowledge Base"],
)


@router.get(
    "/manuals",
    response_model=KnowledgeManualsResponse,
    summary="Catálogo de manuales y procedimientos operativos (RAG)",
    tags=["Knowledge Base"],
)
def get_knowledge_manuals_endpoint(
    q: Optional[str] = Query(None, description="Término o palabra clave de búsqueda para filtrar manuales de soporte"),
    limit: int = Query(50, ge=1, le=200, description="Cantidad máxima de manuales a retornar"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
) -> KnowledgeManualsResponse:
    """Consulta los procedimientos estándar (SOP) guardados en la base de conocimiento RAG.

    Filtra por palabra clave con "q" y pagina resultados usando "limit" y "offset".
    Devuelve el total de artículos encontrados y el listado con sus contenidos y precauciones.
    """
    try:
        res = get_knowledge_manuals(query=q, limit=limit, offset=offset)
        return KnowledgeManualsResponse(**res)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recuperando manuales de la base de conocimiento: {str(exc)}",
        )


__all__ = [
    "router",
    "get_knowledge_manuals_endpoint",
]
