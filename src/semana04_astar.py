import heapq


SUPPORT_GRAPH = {
    "ticket_clasificado": (
        ("consultar_base_conocimiento", 2),
        ("verificar_cambio_reciente", 2),
        ("diagnostico_guiado", 3),
    ),
    "consultar_base_conocimiento": (
        ("aplicar_solucion_conocida", 2),
        ("diagnostico_guiado", 2),
    ),
    "verificar_cambio_reciente": (
        ("revertir_cambio", 3),
        ("diagnostico_guiado", 2),
    ),
    "aplicar_solucion_conocida": (("validar_servicio", 1),),
    "revertir_cambio": (("validar_servicio", 1),),
    "diagnostico_guiado": (
        ("reiniciar_componente", 2),
        ("ajustar_configuracion", 3),
        ("escalar_especialista", 6),
    ),
    "reiniciar_componente": (("validar_servicio", 2),),
    "ajustar_configuracion": (("validar_servicio", 1),),
    "escalar_especialista": (("validar_servicio", 2),),
    "validar_servicio": (("incidente_resuelto", 1),),
    "incidente_resuelto": (),
}

HEURISTIC = {
    "ticket_clasificado": 6,
    "consultar_base_conocimiento": 4,
    "verificar_cambio_reciente": 5,
    "aplicar_solucion_conocida": 2,
    "revertir_cambio": 2,
    "diagnostico_guiado": 5,
    "reiniciar_componente": 3,
    "ajustar_configuracion": 2,
    "escalar_especialista": 3,
    "validar_servicio": 1,
    "incidente_resuelto": 0,
}

START = "ticket_clasificado"
GOAL = "incidente_resuelto"


def neighbors(graph, node, blocked):
    """Genera las acciones disponibles desde el estado actual."""

    for successor, cost in graph.get(node, ()):
        if successor not in blocked:
            yield successor, cost


def astar(graph, start=START, goal=GOAL, blocked=None):
    """Devuelve la secuencia de menor costo, su costo y estados explorados."""

    blocked = set(blocked or ())
    frontier = [(HEURISTIC[start], 0, start)]
    came_from = {start: None}
    cost = {start: 0}
    expanded = 0

    while frontier:
        _, current_cost, current = heapq.heappop(frontier)
        if current_cost != cost[current]:
            continue
        expanded += 1
        if current == goal:
            break

        for nxt, step_cost in neighbors(graph, current, blocked):
            new_cost = cost[current] + step_cost
            if nxt not in cost or new_cost < cost[nxt]:
                cost[nxt] = new_cost
                priority = new_cost + HEURISTIC[nxt]
                heapq.heappush(frontier, (priority, new_cost, nxt))
                came_from[nxt] = current

    if goal not in came_from:
        return None, None, expanded

    path, current = [], goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    return list(reversed(path)), cost[goal], expanded


def change_cost(graph, origin, destination, new_cost):
    """Copia el grafo y modifica el costo de una transición para una prueba."""

    modified = {node: list(edges) for node, edges in graph.items()}
    modified[origin] = [
        (successor, new_cost if successor == destination else cost)
        for successor, cost in modified[origin]
    ]
    return modified


def run_cases():
    """Ejecuta los tres casos mínimos solicitados en la guía."""

    expensive_known_solution = change_cost(
        SUPPORT_GRAPH,
        "consultar_base_conocimiento",
        "aplicar_solucion_conocida",
        8,
    )
    cases = (
        ("Caso 1 - solución conocida disponible", SUPPORT_GRAPH, set()),
        ("Caso 2 - solución conocida costosa", expensive_known_solution, set()),
        (
            "Caso 3 - incidente complejo con restricciones",
            SUPPORT_GRAPH,
            {
                "aplicar_solucion_conocida",
                "revertir_cambio",
                "reiniciar_componente",
                "ajustar_configuracion",
            },
        ),
    )

    results = []
    for name, graph, blocked in cases:
        path, cost, expanded = astar(graph, blocked=blocked)
        results.append((name, path, cost, expanded))
        print(name)
        print("Ruta:", " -> ".join(path) if path else "No existe")
        print("Costo:", cost)
        print("Estados explorados:", expanded)
        print()
    return results


if __name__ == "__main__":
    run_cases()
