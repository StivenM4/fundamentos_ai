from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# Garantizar resolución de rutas absolutas para paquete raíz y src
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import (
    PREDEFINED_TEMPLATES,
    analyze_ticket_endpoint,
    analyze_ticket_multipart_endpoint,
    get_knowledge_manuals_endpoint,
    get_templates,
    knowledge_router,
    models_router,
    models_status_endpoint,
    monitoreo_router,
    tecnico_router,
    tickets_router,
    train_models_endpoint,
    train_tickets_alias,
    train_vision_endpoint,
    usuario_router,
    vision_pipeline_endpoint,
)
from backend.schemas import HealthResponse
from backend.services import get_training_state, train_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Entrena e inicializa los modelos de IA al iniciar la aplicación consumiendo PostgreSQL 18."""
    try:
        res = train_model(require_db=False)
        print(f"[ServiceDesk AI] Modelos inicializados: {res.get('source')} ({res.get('tickets_samples')} tickets).")
    except Exception as exc:
        print(f"[ServiceDesk AI] Aviso inicializando modelos: {exc}")
    yield


# Inicialización de la aplicación FastAPI con metadatos OpenAPI estructurados
app = FastAPI(
    title="ServiceDesk AI Enterprise API",
    description=(
        "API REST de soporte técnico inteligente que integra clasificación explicable (S03), "
        "enrutamiento óptimo A* (S04), recuperación híbrida RAG (S05), monitoreo de equipos TI (S07), "
        "visión neuronal de errores (S08) y pipeline interactivo de visión por computador y OCR (S09)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Inclusión modular de todos los routers del sistema
app.include_router(tickets_router)
app.include_router(models_router)
app.include_router(knowledge_router)
app.include_router(usuario_router)
app.include_router(tecnico_router)
app.include_router(monitoreo_router)

# Configuración de directorio estático para servir capturas subidas
UPLOADS_DIR = PROJECT_ROOT / "uploads"
(UPLOADS_DIR / "capturas_tickets").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Configuración de directorio estático para servir artefactos generados (S08 y S09)
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=str(ARTIFACTS_DIR)), name="artifacts")

# Configuración de CORS para integración fluida con clientes frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    summary="Saludo e introspección de motores IA",
    tags=["General"],
)
def root() -> Dict[str, Any]:
    """Retorna información general de la API y los motores computacionales activos."""
    return {
        "message": "ServiceDesk AI Enterprise API operational",
        "version": "1.0.0",
        "status": "healthy",
        "docs_url": "/docs",
        "active_engines": [
            "Semana 02: Fundamentos y triaje de tickets",
            "Semana 03: Taxonomía de problemas IA y explicabilidad léxica",
            "Semana 04: Búsqueda heurística óptima de menor coste (A*)",
            "Semana 05: Sistema híbrido RAG con base procedimental y reglas de negocio",
            "Semana 08: Red neuronal de visión artificial y ontología para capturas de pantalla",
            "Semana 09: Visión computacional interactiva (Canny, Otsu, regiones conexas y OCR)",
        ],
    }


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Chequeo de salud del servicio y motores IA",
    tags=["General"],
)
def health_check() -> HealthResponse:
    """Verifica el estado de salud de la API y los módulos del Core de IA."""
    ts = get_training_state()
    source_tag = f" [{ts.get('source', 'SQL')}]" if ts.get("source") != "None" else ""

    return HealthResponse(
        status="ok",
        version="1.0.0",
        engines={
            "semana02_triaje": f"Clasificador Multi-output supervisado de tickets{source_tag}",
            "semana03_taxonomia": "Taxonomía explicable con activadores léxicos",
            "semana04_astar": "Planificación heurística de menor coste A*",
            "semana05_rag": "Sistema híbrido RAG (TF-IDF + Coseno + Reglas de producción)",
            "semana08_vision": "Red Neuronal MLP para análisis de capturas de pantalla de errores TI",
            "semana09_vision": "Pipeline de Visión por Computador (Otsu, Canny, Regiones y OCR)",
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
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

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
