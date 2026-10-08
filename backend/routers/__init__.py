from backend.routers.knowledge import (
    get_knowledge_manuals_endpoint,
    router as knowledge_router,
)
from backend.routers.models import (
    models_status_endpoint,
    router as models_router,
    train_models_endpoint,
    train_vision_endpoint,
)
from backend.routers.monitoreo import router as monitoreo_router
from backend.routers.tecnico_tickets import router as tecnico_router
from backend.routers.tickets import (
    PREDEFINED_TEMPLATES,
    analyze_ticket_endpoint,
    analyze_ticket_multipart_endpoint,
    get_templates,
    router as tickets_router,
    train_tickets_alias,
    vision_pipeline_endpoint,
)
from backend.routers.usuario_tickets import router as usuario_router

__all__ = [
    "knowledge_router",
    "models_router",
    "monitoreo_router",
    "tecnico_router",
    "tickets_router",
    "usuario_router",
    "PREDEFINED_TEMPLATES",
    "analyze_ticket_endpoint",
    "analyze_ticket_multipart_endpoint",
    "get_knowledge_manuals_endpoint",
    "get_templates",
    "models_status_endpoint",
    "train_models_endpoint",
    "train_vision_endpoint",
    "train_tickets_alias",
    "vision_pipeline_endpoint",
]
