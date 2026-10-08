from __future__ import annotations

# Módulo de base de conocimiento y consulta de manuales RAG
from backend.services.knowledge import (
    get_knowledge_manuals,
    get_manuals_from_kb,
)

# Algoritmo de planificación A* y catálogo de fases de soporte
from backend.services.routing import (
    NODE_METADATA,
    SUPPORT_GRAPH,
    _calculate_astar_steps,
    calculate_astar_route,
)

# Clasificación supervisada, reentrenamiento y checklist de SOPs
from backend.services.training import (
    DOMAIN_DISPLAY_NAMES,
    DOMAIN_PRECAUTIONS,
    _build_sop_checklist,
    _training_state,
    get_semana02_model,
    get_training_state,
    train_model,
    train_vision_model,
)

# Visión artificial, OCR con Tesseract y auditoría de capturas
from backend.services.vision import (
    VISUAL_CLASS_METADATA,
    _guardar_archivo_captura,
    _inferir_categoria_desde_ocr,
    _persistir_captura_y_auditoria,
    get_semana08_model,
    procesar_captura_multimodal,
    procesar_captura_semana08,
    procesar_pipeline_vision_semana09,
    reload_semana08_model,
)

# Orquestador principal que fusiona los pipelines de IA
from backend.services.orchestrator import (
    _VISUAL_OVERRIDES,
    _apply_simple_visual_override,
    _determine_priority,
    analyze_ticket,
    analyze_ticket_pipeline,
    rag_answer,
)

__all__ = [
    # Entrenamiento y modelos
    "_training_state",
    "train_model",
    "train_vision_model",
    "get_training_state",
    "get_semana02_model",
    "DOMAIN_DISPLAY_NAMES",
    "DOMAIN_PRECAUTIONS",
    "_build_sop_checklist",
    # Visión y OCR
    "VISUAL_CLASS_METADATA",
    "get_semana08_model",
    "reload_semana08_model",
    "_guardar_archivo_captura",
    "_persistir_captura_y_auditoria",
    "procesar_captura_semana08",
    "_inferir_categoria_desde_ocr",
    "procesar_captura_multimodal",
    "procesar_pipeline_vision_semana09",
    # Búsqueda heurística A*
    "NODE_METADATA",
    "SUPPORT_GRAPH",
    "_calculate_astar_steps",
    "calculate_astar_route",
    # Base de conocimiento
    "get_knowledge_manuals",
    "get_manuals_from_kb",
    # Orquestación transversal
    "analyze_ticket",
    "analyze_ticket_pipeline",
    "rag_answer",
    "_determine_priority",
    "_VISUAL_OVERRIDES",
    "_apply_simple_visual_override",
]
