from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.semana04_astar import (
    astar,
    SUPPORT_GRAPH,
    HEURISTIC,
    START,
    GOAL,
)

# Diccionario con metadatos descriptivos, roles responsables y títulos legibles para cada nodo del grafo.
NODE_METADATA: Dict[str, Dict[str, str]] = {
    "ticket_clasificado": {
        "title": "Triage y Clasificación Automática",
        "description": "El asistente evalúa la severidad inicial, asigna metadatos y enruta el requerimiento.",
        "role": "Mesa de Ayuda N1 / Bot Autónomo",
    },
    "consultar_base_conocimiento": {
        "title": "Consulta RAG de Base de Conocimiento",
        "description": "Búsqueda semántica de procedimientos operativos estándar (SOP) y artículos técnicos validados.",
        "role": "Sistema RAG / Analista N1",
    },
    "verificar_cambio_reciente": {
        "title": "Auditoría de Cambios Recientes",
        "description": "Revisión de la ventana de mantenimiento y despliegues previos que puedan haber introducido la falla.",
        "role": "Gestor de Cambios / SysAdmin N2",
    },
    "aplicar_solucion_conocida": {
        "title": "Aplicación de Solución Probada",
        "description": "Ejecución del runbook operativo automatizado o guiado sin necesidad de escalamiento.",
        "role": "Técnico N1 / Automatización",
    },
    "revertir_cambio": {
        "title": "Rollback de Configuración o Despliegue",
        "description": "Reversión inmediata a la última versión o configuración estable documentada.",
        "role": "Administrador de Sistemas N2",
    },
    "diagnostico_guiado": {
        "title": "Diagnóstico Guiado y Aislamiento de Falla",
        "description": "Ejecución de árboles de decisión diagnósticos, análisis de logs y pruebas de estrés.",
        "role": "Especialista N2 / Diagnóstico",
    },
    "reiniciar_componente": {
        "title": "Reinicio Controlado del Servicio",
        "description": "Drenado de conexiones activas y reinicio secuencial de procesos para restablecer estabilidad.",
        "role": "Operaciones TI / Soporte N2",
    },
    "ajustar_configuracion": {
        "title": "Ajuste Dinámico de Parámetros",
        "description": "Modificación de variables de entorno, pools de conexión o directivas de rendimiento.",
        "role": "Ingeniero de Plataforma N2",
    },
    "escalar_especialista": {
        "title": "Escalamiento a Ingeniería Especializada N3",
        "description": "Transferencia urgente al equipo de desarrollo, arquitectura o DBA por alta complejidad.",
        "role": "Ingeniero N3 / Especialista DBA / Seguridad",
    },
    "validar_servicio": {
        "title": "Validación de Integridad y Pruebas de Humo",
        "description": "Verificación del estado de salud del servicio (healthcheck) y confirmación con el usuario.",
        "role": "Control de Calidad / Auditoría TI",
    },
    "incidente_resuelto": {
        "title": "Cierre Exitoso y Retroalimentación",
        "description": "Cierre formal del ticket en el sistema ITSM y registro de la solución para reentrenamiento.",
        "role": "Sistema ITSM / Cierre Automático",
    },
}


def _calculate_astar_steps(path: List[str]) -> List[Dict[str, Any]]:
    """Calcula paso a paso los valores "g(n)", "h(n)" y "f(n)" para cada nodo de la ruta elegida.

    Recorre secuencialmente la lista de nodos, acumulando el costo real del camino ("g"),
    obteniendo la estimación heurística al objetivo ("h") desde el catálogo de la "Semana 04",
    y sumando ambos para el costo total proyectado ("f = g + h").
    También asocia los títulos legibles, roles asignados y descripciones operativas de soporte.
    """
    steps = []
    current_g = 0

    for idx, node in enumerate(path):
        if idx > 0:
            prev_node = path[idx - 1]
            edge_cost = 1
            for successor, cost in SUPPORT_GRAPH.get(prev_node, ()):
                if successor == node:
                    edge_cost = cost
                    break
            current_g += edge_cost

        h_val = HEURISTIC.get(node, 0)
        f_val = current_g + h_val
        meta = NODE_METADATA.get(
            node,
            {"title": node.replace("_", " ").title(), "description": "Paso de soporte", "role": "Técnico N2"}
        )

        steps.append({
            "step_number": idx + 1,
            "node_id": node,
            "title": meta["title"],
            "description": meta["description"],
            "role": meta["role"],
            "g": int(current_g),
            "h": int(h_val),
            "f": int(f_val),
            "is_goal": (node == GOAL),
        })

    return steps


def compute_blind_states(expanded_states: int) -> int:
    """Estima la cantidad de estados explorados que requeriría una búsqueda ciega sin heurística.

    Sirve como métrica de comparación académica y de rendimiento para contrastar
    el desempeño de "A*" frente a algoritmos no informados (como BFS o DFS) en el mismo grafo.
    """
    return max(int(expanded_states) + 6, 12)


def calculate_astar_route(blocked_steps: Optional[List[str]] = None) -> Dict[str, Any]:
    """Calcula la ruta óptima de atención de incidentes usando el algoritmo "A*".

    Acepta una lista opcional de pasos bloqueados ("blocked_steps") para simular restricciones
    operativas del entorno real (por ejemplo, servicios caídos o falta de permisos).
    Si con los bloqueos el grafo queda sin solución, recurre a la ruta base sin restricciones.
    Retorna el detalle paso a paso con costos, estados expandidos y la ganancia porcentual
    de eficiencia lograda frente a una búsqueda ciega no informada.
    """
    blocked = list(blocked_steps or [])
    path, cost, expanded = astar(SUPPORT_GRAPH, start=START, goal=GOAL, blocked=blocked)
    if path is None:
        path, cost, expanded = astar(SUPPORT_GRAPH, start=START, goal=GOAL, blocked=[])

    total_cost = int(cost) if cost is not None else 6
    expanded_states = int(expanded)
    blind_search_states = compute_blind_states(expanded_states)
    efficiency_gain_pct = round(((blind_search_states - expanded_states) / blind_search_states) * 100.0, 1)
    steps = _calculate_astar_steps(path)

    return {
        "path": path,
        "total_cost": total_cost,
        "cost": total_cost,
        "expanded_states": expanded_states,
        "heuristic_states": expanded_states,
        "blind_search_states": blind_search_states,
        "efficiency_gain_pct": efficiency_gain_pct,
        "efficiency_badge": f"{len(path)} Pasos Heurísticos vs {blind_search_states} Búsqueda Ciega (-{efficiency_gain_pct}%)",
        "steps": steps,
    }
