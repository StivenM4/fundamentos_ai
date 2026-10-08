from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]

from src.semana03_taxonomia import normalize_text


def get_knowledge_manuals(
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Recupera manuales y procedimientos operativos con soporte de búsqueda y paginación.

    Consulta en "PostgreSQL 18" y, si está desconectado, recurre al archivo local "data/base_conocimiento.txt".
    """
    from backend.database import query_knowledge_manuals

    # 1. Buscamos primero en la tabla "servicedesk.articulos_sop_runbooks" de PostgreSQL
    db_result = query_knowledge_manuals(query=query, limit=limit, offset=offset)
    if db_result is not None:
        total_count, manuals = db_result
        return {
            "total": total_count,
            "count": len(manuals),
            "query": query,
            "source": "PostgreSQL 18 (servicedesk.articulos_sop_runbooks)",
            "manuals": manuals,
        }

    # 2. Modo contingencia: leemos el archivo plano "data/base_conocimiento.txt"
    kb_file = PROJECT_ROOT / "data" / "base_conocimiento.txt"
    raw_lines: List[str] = []
    if kb_file.exists():
        raw_lines = [
            line.strip()
            for line in kb_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    if not raw_lines:
        from src.semana05_sistema_hibrido import DEFAULT_DOCS
        raw_lines = list(DEFAULT_DOCS)

    # Filtramos por coincidencia de texto normalizado si viene el parámetro "query"
    indexed_lines: List[Tuple[int, str]] = list(enumerate(raw_lines, start=1))
    if query and str(query).strip():
        q_norm = normalize_text(str(query))
        indexed_lines = [
            (idx, text)
            for (idx, text) in indexed_lines
            if q_norm in normalize_text(text)
        ]

    total_count = len(indexed_lines)
    paged = indexed_lines[offset : offset + limit]

    manuals = []
    for orig_idx, line in paged:
        parts = line.split(",", 1)
        title = parts[0].strip() if len(parts) > 1 else line[:70]
        manuals.append({
            "id": orig_idx,
            "code": f"SOP-KB-{orig_idx:03d}",
            "title": title,
            "content": line,
            "precautions": None,
            "category": None,
            "source": "data/base_conocimiento.txt (Local Fallback)",
        })

    return {
        "total": total_count,
        "count": len(manuals),
        "query": query,
        "source": "data/base_conocimiento.txt (Local Fallback)",
        "manuals": manuals,
    }


# Alias para retrocompatibilidad
get_manuals_from_kb = get_knowledge_manuals

