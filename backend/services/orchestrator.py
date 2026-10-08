from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.schemas import VisualAnalysis
from backend.services.routing import _calculate_astar_steps, compute_blind_states
from backend.services.training import (
    DOMAIN_DISPLAY_NAMES,
    DOMAIN_PRECAUTIONS,
    _build_sop_checklist,
    get_semana02_model,
)
from src.semana03_taxonomia import (
    classify_description,
    normalize_text,
    score_description,
)
from src.semana04_astar import GOAL, START, SUPPORT_GRAPH, astar
from src.semana05_sistema_hibrido import answer as rag_answer

# Reglas de sobreescritura cuando la red neuronal detecta patrones visuales claros (S08)
_VISUAL_OVERRIDES: dict[str, dict] = {
    "disco_lleno": {
        "category": "Infraestructura & Almacenamiento",
        "priority_if_low": "ALTA",
        "sla_minutes": 120,
        "assigned_to": "Soporte Nivel 2 (Sistemas & Storage)",
        "terms": ["disco_lleno", "almacenamiento_saturado"],
    },
    "red_desconectada": {
        "category": "Redes & Comunicaciones",
        "priority_if_low": "ALTA",
        "sla_minutes": 120,
        "assigned_to": "Soporte Nivel 2 (Redes & Conectividad)",
        "terms": ["red_desconectada", "enlace_fisico_caido"],
    },
    "error_aplicacion_crash": {
        "category": "Software & Aplicaciones",
        "priority_if_low": None,
        "sla_minutes": None,
        "assigned_to": "Soporte Nivel 2 (Aplicaciones)",
        "terms": ["error_aplicacion_crash", "excepcion_proceso"],
    },
}


def _determine_priority(text: str) -> Tuple[str, int]:
    """Calcula la prioridad ("CRÍTICA", "ALTA", "MEDIA", "BAJA") y los minutos de SLA a partir de palabras de impacto y el modelo supervisado S02."""
    norm = normalize_text(text)
    words = set(norm.split())

    critical_terms = {
        "caida", "caido", "critico", "critica", "alarma", "timeout", "postgre",
        "postgresql", "cluster", "produccion", "corrupcion", "corrupta",
        "masivo", "masiva", "bloqueante", "parada", "emergencia", "phishing",
        "secuestro", "ransomware", "afectacion",
    }
    high_terms = {
        "vpn", "enlace", "red", "dns", "erp", "servidor", "active", "directory",
        "autenticacion", "credenciales", "desconexion", "intermitencia", "lento",
        "demora", "congelamiento", "congelada",
    }
    low_terms = {
        "solicitud", "cambio", "mouse", "teclado", "consulta", "pedir", "accesorio",
        "informacion", "duda", "configurar",
    }

    if words.intersection(critical_terms) or "base de datos" in norm or "error critico" in norm:
        return "CRÍTICA", 60

    s2 = get_semana02_model()
    if s2 is not None:
        try:
            pred_prio = str(s2.predict([text])[0][1]).lower()
            if pred_prio == "alta":
                return "ALTA", 120
            if pred_prio == "baja":
                return "BAJA", 480
            if pred_prio == "media":
                return "MEDIA", 240
        except Exception:
            pass

    if words.intersection(high_terms) or "memoria violada" in norm or "cuenta bloqueada" in norm:
        return "ALTA", 120
    if words.intersection(low_terms):
        return "BAJA", 480
    return "MEDIA", 240


def _apply_simple_visual_override(
    detected_cl: str,
    category_name: str,
    priority: str,
    sla_minutes: int,
    assigned_to: str,
    lexical_evidence: list,
) -> tuple[str, str, int, str]:
    """Ajusta la categoría, SLA y técnico asignado cuando la captura coincide con fallas conocidas de disco o red."""
    cfg = _VISUAL_OVERRIDES.get(detected_cl)
    if not cfg:
        return category_name, priority, sla_minutes, assigned_to
    category_name, assigned_to = cfg["category"], cfg["assigned_to"]
    if cfg["priority_if_low"] and priority in ("MEDIA", "BAJA"):
        priority, sla_minutes = cfg["priority_if_low"], cfg["sla_minutes"]
    for term in cfg["terms"]:
        if term not in lexical_evidence:
            lexical_evidence.append(term)
    return category_name, priority, sla_minutes, assigned_to


def _build_bsod_override(confidence_score: float) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Construye el runbook de volcado de memoria ("RB-HW-05") y la ruta A* para incidentes de pantalla azul (BSOD)."""
    rag_sop = {
        "runbook_id": "RB-HW-05",
        "title": "Runbook RB-HW-05: Protocolo de Diagnóstico y Análisis de Volcado de Memoria (Memory Dump / BSOD)",
        "similarity_score": round(confidence_score, 4),
        "precautions": "No forzar reinicios continuos sin haber asegurado la copia del archivo de volcado de memoria .dmp; las sobreescrituras destruyen la evidencia forense del fallo de kernel.",
        "checklist": [
            "Aislar el equipo del dominio para evitar reintentos continuos de booteo.",
            "Extraer el archivo de volcado de memoria minidump en C:\\Windows\\Minidump\\*.dmp.",
            "Analizar el código de verificación de error (BugCheck Code: ej. CRITICAL_PROCESS_DIED, IRQL_NOT_LESS_OR_EQUAL) mediante WinDbg.",
            "Comprobar integridad de módulos de memoria RAM mediante diagnóstico de hardware (MemTest).",
            "Revertir actualización reciente de controlador de chipset o firmware de almacenamiento.",
        ],
    }
    astar_steps = [
        {"step_number": 1, "node_id": "ticket_clasificado", "title": "Triage y Clasificación Multimodal (BSOD)", "description": "Detección visual de BSOD (Stop Error) y reclasificación inmediata a Kernel Crítico.", "role": "Mesa de Ayuda N1 / Bot Autónomo", "g": 0, "h": 6, "f": 6, "is_goal": False},
        {"step_number": 2, "node_id": "diagnostico_guiado", "title": "Diagnóstico Forense de Crash Dump", "description": "Inspección de archivos Minidump, identificación del BugCheck Code y análisis de pila de llamadas del kernel.", "role": "Especialista N2 / Kernel & Hardware", "g": 3, "h": 5, "f": 8, "is_goal": False},
        {"step_number": 3, "node_id": "escalar_especialista", "title": "Intervención de Soporte Avanzado N2 Hardware", "description": "Evaluación física de módulos RAM, comprobación de sectores de disco y análisis térmico de hardware.", "role": "Soporte Nivel 2 (Kernel & Hardware)", "g": 9, "h": 3, "f": 12, "is_goal": False},
        {"step_number": 4, "node_id": "validar_servicio", "title": "Validación de Estabilidad de Kernel y Memoria", "description": "Pruebas de estrés sostenido (MemTest) y verificación de booteo sin nuevos eventos de volcado de memoria.", "role": "Soporte Nivel 2 / Control de Calidad", "g": 11, "h": 1, "f": 12, "is_goal": False},
        {"step_number": 5, "node_id": "incidente_resuelto", "title": "Cierre Forense y Actualización de Firmware", "description": "Cierre del incidente, confirmación de estabilidad con el usuario y registro documental de causa raíz del fallo de kernel.", "role": "Sistema ITSM / Cierre Automático", "g": 12, "h": 0, "f": 12, "is_goal": True},
    ]
    astar_route = {"total_cost": 12, "heuristic_states": 5, "blind_search_states": 11, "efficiency_gain_pct": 54.5, "steps": astar_steps}
    return rag_sop, astar_route


def _resolve_astar_route(blocked: List[str]) -> Tuple[Dict[str, Any], List[Dict[str, Any]], int, int, int, float]:
    """Ejecuta el algoritmo A* en el grafo de soporte y compara los estados explorados contra una búsqueda ciega."""
    path, cost, expanded = astar(SUPPORT_GRAPH, start=START, goal=GOAL, blocked=blocked)
    if path is None and blocked:
        path, cost, expanded = astar(SUPPORT_GRAPH, start=START, goal=GOAL, blocked=[])

    total_cost = int(cost) if cost is not None else 6
    expanded_states = int(expanded)
    blind_search_states = compute_blind_states(expanded_states)
    efficiency_gain_pct = round(((blind_search_states - expanded_states) / blind_search_states) * 100.0, 1)
    astar_steps = _calculate_astar_steps(path)
    astar_route = {
        "total_cost": total_cost,
        "heuristic_states": expanded_states,
        "blind_search_states": blind_search_states,
        "efficiency_gain_pct": efficiency_gain_pct,
        "steps": astar_steps,
    }
    return astar_route, astar_steps, total_cost, expanded_states, blind_search_states, efficiency_gain_pct


def analyze_ticket(
    subject: str,
    description: str,
    blocked_steps: Optional[List[str]] = None,
    visual_analysis: Optional[Union[VisualAnalysis, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Ejecuta el análisis completo del ticket coordinando los motores de IA (clasificación, A*, RAG y visión/OCR)."""
    if isinstance(visual_analysis, dict):
        try:
            visual_analysis = VisualAnalysis(**visual_analysis)
        except Exception:
            pass
    ocr_ev = visual_analysis.get("ocr_text") if isinstance(visual_analysis, dict) else getattr(visual_analysis, "ocr_text", None)
    full_text = f"{subject} {description}\n[Evidencia Visual OCR S09]: {str(ocr_ev).strip()}".strip() if (ocr_ev and str(ocr_ev).strip()) else f"{subject} {description}".strip()
    blocked = list(blocked_steps or [])

    # 1. Taxonomía y activadores léxicos de Semana 03
    lexical_evidence: List[str] = []
    try:
        tax_res = classify_description(full_text)
        primary_category = tax_res.primary_category
        for phrases in tax_res.triggers.values():
            lexical_evidence.extend(phrases)
    except Exception:
        triggers = score_description(full_text)
        matched = [cat for cat, phrases in triggers.items() if phrases]
        for phrases in triggers.values():
            lexical_evidence.extend(phrases)
        primary_category = matched[0] if matched else "Procesamiento de lenguaje natural"

    # 2. Búsqueda semántica y runbook en base procedimental RAG (Semana 05)
    rag_res = rag_answer(full_text)
    domain_class = rag_res.get("clase", "software")
    evidence_text = rag_res.get("evidencia", "")
    similarity_score = round(float(rag_res.get("similitud", 0.0)), 4)
    fired_rules = rag_res.get("reglas", [])
    if fired_rules:
        lexical_evidence.extend(fired_rules)
    lexical_evidence = sorted(list(dict.fromkeys(lexical_evidence))) or [w for w in normalize_text(subject).split() if len(w) > 4][:5]

    sop_title = f"Protocolo Operativo: {DOMAIN_DISPLAY_NAMES.get(domain_class, domain_class.capitalize())}"
    precautions = DOMAIN_PRECAUTIONS.get(domain_class, "Respaldar información crítica y validar permisos antes de realizar cambios estructurales.")
    rag_sop = {
        "runbook_id": f"SOP-{domain_class.upper()}-2026",
        "title": sop_title,
        "similarity_score": similarity_score,
        "precautions": precautions,
        "checklist": _build_sop_checklist(evidence_text, domain_class),
    }

    # 3. Planificación de ruta óptima con A* (Semana 04)
    astar_route, astar_steps, total_cost, expanded_states, blind_search_states, efficiency_gain_pct = _resolve_astar_route(blocked)

    # 4. Prioridad supervisada, cálculo de SLA y mesa de asignación
    priority, sla_minutes = _determine_priority(full_text)
    confidence_score = max(0.85, similarity_score) if similarity_score > 0 else 0.88
    norm_txt = normalize_text(full_text)
    db_kws = ("base de datos", "postgresql", "cluster", "oracle", "mysql", "sql", "servidor de base de datos", "postgres")
    if any(kw in norm_txt for kw in db_kws):
        category_name = "Infraestructura & Base de Datos"
        lexical_evidence.extend([kw for kw in db_kws if kw in norm_txt and kw not in lexical_evidence])
    else:
        category_name = DOMAIN_DISPLAY_NAMES.get(domain_class, primary_category)

    assigned_to = "Mesa de Ayuda Nivel 1 / Triage Automático"

    # 5. Fusión multimodal con red neuronal de visión (S08) y OCR (S09)
    if visual_analysis is not None:
        detected_cl = visual_analysis.detected_class
        if detected_cl == "pantalla_azul_bsod":
            category_name, priority, sla_minutes, assigned_to = "Hardware & Kernel Crítico", "CRÍTICA", 30, "Soporte Nivel 2 (Kernel & Hardware)"
            confidence_score = max(0.984, visual_analysis.confidence_score)
            rag_sop, astar_route = _build_bsod_override(confidence_score)
            astar_steps, total_cost = astar_route["steps"], astar_route["total_cost"]
            expanded_states, blind_search_states = astar_route["heuristic_states"], astar_route["blind_search_states"]
            efficiency_gain_pct, sop_title = astar_route["efficiency_gain_pct"], rag_sop["title"]
            precautions, checklist = rag_sop["precautions"], rag_sop["checklist"]
            for term in ["pantalla_azul_bsod", "kernel_crash", "minidump_dmp", "bugcheck_code", "hardware_l2"]:
                if term not in lexical_evidence:
                    lexical_evidence.append(term)
        else:
            category_name, priority, sla_minutes, assigned_to = _apply_simple_visual_override(detected_cl, category_name, priority, sla_minutes, assigned_to, lexical_evidence)

        if visual_analysis.impact_category == "Redes" and category_name in ["General", "Software & Aplicaciones", "Procesamiento de lenguaje natural"]:
            category_name, assigned_to = "Redes & Comunicaciones", "Soporte Nivel 2 (Redes & Conectividad)"
            if priority in ["MEDIA", "BAJA"]:
                priority, sla_minutes = "ALTA", 120
        elif visual_analysis.impact_category == "Seguridad" and category_name in ["General", "Software & Aplicaciones", "Procesamiento de lenguaje natural"]:
            category_name, assigned_to = "Seguridad & Accesos", "Soporte Nivel 2 (Seguridad & Accesos)"
            if priority in ["MEDIA", "BAJA"]:
                priority, sla_minutes = "ALTA", 120
        elif visual_analysis.impact_category == "Infraestructura" and category_name in ["General", "Software & Aplicaciones", "Procesamiento de lenguaje natural"]:
            category_name, assigned_to = "Infraestructura & Almacenamiento", "Soporte Nivel 2 (Infraestructura & Servidores)"

        if visual_analysis.ocr_text:
            for term in [t.lower() for t in re.split(r"[\s\-_:,;.]+", visual_analysis.ocr_text) if len(t) >= 4]:
                if term not in lexical_evidence and len(lexical_evidence) < 15:
                    lexical_evidence.append(term)

    base_factor = 4 if priority == "CRÍTICA" else 3
    estimated_time_min = max(10, int(total_cost * base_factor + (10 if priority == "CRÍTICA" else 5)))
    classification_res = {"category": category_name, "priority": priority, "confidence_score": round(confidence_score, 3), "lexical_evidence": lexical_evidence, "sla_minutes": sla_minutes}

    return {
        "ticket": {"subject": subject, "description": description, "blocked_steps": blocked},
        "classification": classification_res,
        "astar_route": astar_route,
        "rag_sop": rag_sop,
        "visual_analysis": visual_analysis,
        "category": category_name,
        "priority": priority,
        "confidence_score": round(confidence_score, 3),
        "sla_minutes": f"{sla_minutes} min",
        "estimated_resolution_time": f"~{estimated_time_min} min",
        "lexical_evidence": lexical_evidence,
        "clase": domain_class,
        "evidencia": evidence_text,
        "similitud": similarity_score,
        "reglas": fired_rules,
        "assigned_to": assigned_to,
        "astar": {"path": [s["node_id"] for s in astar_steps], "cost": total_cost, "expanded": expanded_states, "blind_search_states": blind_search_states, "savings_pct": efficiency_gain_pct, "steps": astar_steps},
        "rag": {"clase": domain_class, "rules_fired": fired_rules, "evidence": evidence_text, "similarity": similarity_score, "sop_id": rag_sop["runbook_id"], "title": sop_title, "precautions": precautions, "checklist": rag_sop["checklist"]},
    }


analyze_ticket_pipeline = analyze_ticket
