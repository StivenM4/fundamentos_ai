from __future__ import annotations

import sys
from pathlib import Path

# Metemos la raíz del proyecto al "sys.path" para resolver bien "src" y paquetes hermanos
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reexportamos la instancia unificada de FastAPI y todos sus componentes desde "api.py"
from api import (
    PREDEFINED_TEMPLATES,
    analyze_ticket_endpoint,
    analyze_ticket_multipart_endpoint,
    app,
    get_knowledge_manuals_endpoint,
    get_templates,
    health_check,
    knowledge_router,
    models_router,
    models_status_endpoint,
    monitoreo_router,
    root,
    tecnico_router,
    tickets_router,
    train_models_endpoint,
    train_tickets_alias,
    train_vision_endpoint,
    usuario_router,
    vision_pipeline_endpoint,
)

__all__ = [
    "app",
    "PREDEFINED_TEMPLATES",
    "root",
    "health_check",
    "train_models_endpoint",
    "train_vision_endpoint",
    "train_tickets_alias",
    "models_status_endpoint",
    "get_templates",
    "analyze_ticket_endpoint",
    "analyze_ticket_multipart_endpoint",
    "vision_pipeline_endpoint",
    "get_knowledge_manuals_endpoint",
    "usuario_router",
    "tecnico_router",
    "monitoreo_router",
    "tickets_router",
    "models_router",
    "knowledge_router",
]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
