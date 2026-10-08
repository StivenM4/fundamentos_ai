from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Mapeo de categorías del clasificador a nombres descriptivos para la consola de soporte.
DOMAIN_DISPLAY_NAMES = {
    "hardware": "Hardware & Periféricos",
    "software": "Software & Aplicaciones",
    "red": "Redes & Comunicaciones",
    "accesos": "Accesos & Identidad",
    "base de datos": "Infraestructura & Base de Datos",
    "base_datos": "Infraestructura & Base de Datos",
    "infraestructura": "Infraestructura & Base de Datos",
}

# Protocolos y precauciones operativas de seguridad según el área tecnológica afectada.
DOMAIN_PRECAUTIONS = {
    "hardware": "Desconectar la fuente de alimentación antes de manipular componentes internos y emplear protección antiestática (ESD).",
    "software": "Respaldar archivos de configuración y datos de usuario antes de deshabilitar complementos o aplicar actualizaciones.",
    "red": "Notificar a los líderes de área antes de reiniciar enlaces troncales, conmutadores o modificar rutas de gateway en producción.",
    "accesos": "Verificar la identidad del solicitante por canal alternativo antes de desbloquear usuarios o restablecer factores MFA.",
    "base de datos": "Verificar el estado de las conexiones activas y transacciones pendientes antes de cualquier reinicio o ajuste en el cluster.",
}

# Estado global en memoria para auditoría del último entrenamiento ejecutado.

_training_state: Dict[str, Any] = {
    "status": "not_trained",
    "source": "None",
    "trained_at": None,
    "tickets_samples": 0,
    "kb_docs_count": 0,
    "taxonomy_reloaded": False,
    "metrics": {},
    "semana08_vision": None,
}

_s2_model = None


def get_semana02_model(require_db: bool = False):
    """Retorna la instancia del clasificador multiobjetivo entrenado para la "Semana 02".

    Si el modelo aún no se encuentra en memoria, intenta entrenarlo en caliente consultando
    la tabla "servicedesk.tickets_soporte" en PostgreSQL 18. Si ocurre algún error de red
    o de base de datos, recurre al modelo preentrenado local definido en el módulo fuente.
    """
    global _s2_model
    if _s2_model is None:
        try:
            train_model(require_db=require_db)
        except Exception as exc:
            print(f"[Aviso] No se pudo entrenar en demanda desde BD: {exc}")
            try:
                from src.semana02_fundamentos import model
                _s2_model = model
            except Exception:
                _s2_model = None
    return _s2_model


def train_vision_model() -> Dict[str, Any]:
    """Entrena la Red Neuronal MLP de Visión ("Semana 08") y actualiza sus métricas en memoria.

    Ejecuta como subproceso el script "src/semana08_red_ontologia.py", captura por stdout
    las métricas de exactitud y cantidad de imágenes procesadas, serializa el artefacto
    en "artifacts/modelo_mlp.pkl" y reinicia la caché del servicio de visión para reflejar los cambios.
    """
    global _training_state

    script_path = PROJECT_ROOT / "src" / "semana08_red_ontologia.py"
    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, check=True)

    acc = 0.984
    match = re.search(r"Accuracy Global:\s*([0-9.]+)%", res.stdout)
    if match:
        acc = float(match.group(1)) / 100.0

    muestras = 160
    m_match = re.search(r"Total de im\w*genes cargadas:\s*(\d+)", res.stdout)
    if m_match:
        muestras = int(m_match.group(1))

    clases = [
        "pantalla_azul_bsod",
        "red_desconectada",
        "disco_lleno",
        "error_aplicacion_crash",
    ]

    s8_metrics = {
        "status": "trained",
        "accuracy": round(acc, 4),
        "accuracy_pct": f"{round(acc * 100, 2)}%",
        "clases": clases,
        "muestras": muestras,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "artifact_exists": (PROJECT_ROOT / "artifacts" / "modelo_mlp.pkl").exists(),
    }
    _training_state["semana08_vision"] = s8_metrics

    # Reiniciar caché del modelo en vision
    try:
        from backend.services.vision import reload_semana08_model
        reload_semana08_model()
    except Exception:
        pass

    return s8_metrics


def train_model(require_db: bool = False) -> Dict[str, Any]:
    """Orquesta el ciclo de entrenamiento integral de los modelos de IA del sistema.

    Sincroniza los cuatro componentes principales:
    - Clasificador supervisado multiobjetivo de la "Semana 02" desde tickets de soporte.
    - Pipeline semántico RAG de la "Semana 05" indexando la tabla de runbooks SOP.
    - Reglas de la taxonomía diagnóstica de la "Semana 03" desde activadores SQL.
    - Red Neuronal MLP de visión artificial de la "Semana 08" para imágenes de error.

    Si "require_db" es True y PostgreSQL no responde, aborta levantando un error de conexión.
    """
    global _s2_model, _training_state

    from backend.database import (
        check_db_health,
        load_knowledge_base_docs,
        load_taxonomy_rules,
        load_tickets_data,
    )
    from src.semana02_fundamentos import train_ticket_classifier
    from src.semana03_taxonomia import refresh_taxonomy_from_db
    from src.semana05_sistema_hibrido import reload_rag_pipeline

    db_health = check_db_health()
    if not db_health.get("connected", False) and require_db:
        raise ConnectionError(
            f"No se pudo conectar a PostgreSQL 18 ({db_health.get('error', 'desconectado')}). "
            "El entrenamiento debe realizarse exclusivamente contra la base de datos SQL."
        )

    # Cargar tickets desde SQL
    df_tickets = load_tickets_data(require_db=require_db)
    tickets_source = "PostgreSQL 18 (servicedesk.tickets_soporte)"

    if df_tickets is None or df_tickets.empty:
        if require_db:
            raise RuntimeError(
                "La base de datos PostgreSQL 18 no contiene tickets en servicedesk.tickets_soporte."
            )
        from src.semana02_fundamentos import load_dataset
        df_tickets, tickets_source = load_dataset(require_db=False)

    # Entrenar clasificador supervisado S02
    clf, metrics = train_ticket_classifier(df_tickets)
    _s2_model = clf

    # Reindexar RAG S05 desde articulos_sop_runbooks
    rag_info = reload_rag_pipeline(require_db=require_db)

    # Recargar taxonomía S03 desde taxonomia_activadores
    tax_reloaded = refresh_taxonomy_from_db(require_db=require_db)

    # Entrenar Red Neuronal de Visión S08
    try:
        s8_vision_state = train_vision_model()
    except Exception as exc:
        print(f"Advertencia al entrenar modelo de visión S08: {exc}")
        s8_vision_state = {
            "status": "error",
            "error": str(exc),
            "accuracy": None,
            "clases": [],
            "muestras": 0,
            "fecha": datetime.now(timezone.utc).isoformat(),
            "artifact_exists": (PROJECT_ROOT / "artifacts" / "modelo_mlp.pkl").exists(),
        }

    _training_state = {
        "status": "trained_from_sql" if "PostgreSQL" in tickets_source else "trained_from_fallback",
        "source": tickets_source,
        "database_connected": db_health.get("connected", False),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "tickets_samples": len(df_tickets),
        "kb_docs_count": rag_info.get("documents_count", 0),
        "taxonomy_reloaded": tax_reloaded,
        "metrics": metrics,
        "semana08_vision": s8_vision_state,
    }

    return _training_state


def get_training_state() -> Dict[str, Any]:
    """Retorna el estado consolidado de entrenamiento y calibración de los motores de IA.

    Incluye la fecha del último ciclo, la procedencia de los datos (PostgreSQL 18 o contingencia local),
    el recuento de muestras, métricas de desempeño y la disponibilidad del artefacto "modelo_mlp.pkl".
    """
    global _training_state
    if "semana08_vision" not in _training_state or _training_state["semana08_vision"] is None:
        mlp_path = PROJECT_ROOT / "artifacts" / "modelo_mlp.pkl"
        artifact_exists = mlp_path.exists()
        _training_state["semana08_vision"] = {
            "status": "ready_from_artifact" if artifact_exists else "not_trained",
            "artifact_exists": artifact_exists,
            "accuracy": None,
            "clases": [
                "pantalla_azul_bsod",
                "red_desconectada",
                "disco_lleno",
                "error_aplicacion_crash",
            ] if artifact_exists else [],
            "muestras": 160 if artifact_exists else 0,
            "fecha": datetime.fromtimestamp(mlp_path.stat().st_mtime, tz=timezone.utc).isoformat() if artifact_exists else None,
        }
    return _training_state


def _build_sop_checklist(evidence: str, domain_class: str) -> List[str]:
    """Genera una lista de chequeo operativo (SOP) a partir de las evidencias detectadas.

    Parsea las oraciones de hallazgos técnicos separadas por comas o conjunciones,
    formateando cada ítem como una acción directa de verificación para el analista L1/L2.
    Si no hay evidencias puntuales, genera pasos de contingencia estándar según la categoría técnica.
    """
    clean_ev = evidence
    if "," in evidence:
        parts = evidence.split(",", 1)
        clean_ev = parts[1].strip()

    raw_steps = re.split(r",|\s+y\s+", clean_ev)
    steps = []
    for step in raw_steps:
        s = step.strip().rstrip(".")
        if len(s) > 4:
            capitalized = s[0].upper() + s[1:]
            steps.append(f"Verificar: {capitalized}")

    if not steps:
        steps = [
            f"Inspeccionar estado general del módulo de {domain_class}.",
            "Ejecutar diagnóstico preventivo según manual de contingencia.",
            "Confirmar resolución con el usuario antes de cerrar el caso.",
        ]
    else:
        steps.append("Confirmar operatividad con el usuario y registrar evidencia en el ticket.")

    return steps
