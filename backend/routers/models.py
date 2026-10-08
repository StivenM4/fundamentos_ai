from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

# Metemos la raíz al "sys.path" para que resuelva módulos de "src" y "backend"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import APIRouter, HTTPException, status

from backend.database import check_db_health
from backend.services import get_training_state, train_model, train_vision_model

router = APIRouter(
    prefix="/api/models",
    tags=["Modelos"],
)


@router.post(
    "/train",
    summary="Entrenar modelos de IA consumiendo datos de PostgreSQL 18",
    tags=["Modelos"],
)
def train_models_endpoint(require_db: bool = False) -> Dict[str, Any]:
    """Reentrena los clasificadores supervisados y reindexa el motor RAG tomando los datos de "PostgreSQL 18"."""
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


@router.post(
    "/train-vision",
    summary="Entrenar específicamente la Red Neuronal MLP de Visión (Semana 08)",
    tags=["Modelos"],
)
def train_vision_endpoint() -> Dict[str, Any]:
    """Lanza el script de entrenamiento de la red neuronal MLP de visión (Semana 08) y recarga el artefacto en memoria."""
    try:
        metrics = train_vision_model()
        return {
            "status": "success",
            "message": "Entrenamiento de la Red Neuronal de Visión (Semana 08) completado exitosamente.",
            "data": metrics,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo durante el entrenamiento de la Red Neuronal de Visión: {str(exc)}",
        )


@router.get(
    "/status",
    summary="Consultar estado de entrenamiento y procedencia de datos",
    tags=["Modelos"],
)
def models_status_endpoint() -> Dict[str, Any]:
    """Consulta el estado del clasificador, del pipeline RAG, de la base de datos y del modelo MLP de visión."""
    mlp_path = PROJECT_ROOT / "artifacts" / "modelo_mlp.pkl"
    artifact_exists = mlp_path.exists()
    training_state = get_training_state()
    vision_state = training_state.get("semana08_vision") or {}

    return {
        "database": check_db_health(),
        "training": training_state,
        "semana08_vision": {
            "artifact_exists": artifact_exists,
            "artifact_file": "modelo_mlp.pkl",
            "status": vision_state.get("status", "ready_from_artifact" if artifact_exists else "not_trained"),
            "accuracy": vision_state.get("accuracy"),
            "accuracy_pct": vision_state.get("accuracy_pct"),
            "clases": vision_state.get("clases", []),
            "muestras": vision_state.get("muestras", 0),
            "fecha": vision_state.get("fecha"),
        },
    }


__all__ = [
    "router",
    "train_models_endpoint",
    "train_vision_endpoint",
    "models_status_endpoint",
]

