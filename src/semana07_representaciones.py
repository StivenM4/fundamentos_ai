from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

METRICAS_DOMINIO: List[str] = [
    "temperatura_cpu_c",
    "carga_servidor_pct",
    "tasa_errores_min",
]

DESCRIPCION_METRICAS: Dict[str, str] = {
    "temperatura_cpu_c": "Temperatura termica del procesador (C)",
    "carga_servidor_pct": "Uso de CPU/RAM (fraccion decimal 0.0 - 1.0)",
    "tasa_errores_min": "Tasa de errores del sistema por minuto",
}

BASELINE_REFERENCIA = np.array([70.0, 0.80, 2.0])
UMBRAL_DISTANCIA_ALERTA = 1.5

UMBRAL_TEMPERATURA_ALTA = 71.0
UMBRAL_CARGA_ALTA = 0.82
UMBRAL_ERRORES_PRESENTES = 2.5


def calcular_distancia_telemetria(
    sample: np.ndarray,
    reference: np.ndarray = BASELINE_REFERENCIA,
) -> float:
    sample_arr = np.asarray(sample, dtype=float)
    ref_arr = np.asarray(reference, dtype=float)
    if sample_arr.shape != ref_arr.shape:
        raise ValueError(
            f"Dimensiones incompatibles: sample {sample_arr.shape} vs reference {ref_arr.shape}"
        )
    return float(np.linalg.norm(sample_arr - ref_arr))


REGLAS_DIAGNOSTICO: List[Tuple[Set[str], str]] = [
    ({"temperatura_alta", "carga_alta"}, "riesgo_termico"),
    ({"carga_alta", "errores_presentes"}, "degradacion_servicio"),
    ({"temperatura_alta", "errores_presentes"}, "inestabilidad_hardware"),
    ({"temperatura_alta", "carga_alta", "errores_presentes"}, "incidente_critico_p1"),
]


def evaluar_reglas_simbolicas(facts: Set[str]) -> List[str]:
    conclusiones: List[str] = []
    for premisas, conclusion in REGLAS_DIAGNOSTICO:
        if premisas.issubset(facts):
            if conclusion not in conclusiones:
                conclusiones.append(conclusion)
    return conclusiones


def accepts_01(text: str) -> bool:
    state = "q0"
    transitions: Dict[Tuple[str, str], str] = {
        ("q0", "0"): "q1",
        ("q0", "1"): "q0",
        ("q1", "0"): "q1",
        ("q1", "1"): "q2",
        ("q2", "0"): "q1",
        ("q2", "1"): "q0",
    }
    for symbol in text:
        if (state, symbol) not in transitions:
            return False
        state = transitions[(state, symbol)]
    return state == "q2"


def discretizar_telemetria(sample: np.ndarray) -> Set[str]:
    temp, carga, errores = sample[0], sample[1], sample[2]
    facts: Set[str] = set()

    if temp >= UMBRAL_TEMPERATURA_ALTA:
        facts.add("temperatura_alta")
    if carga >= UMBRAL_CARGA_ALTA:
        facts.add("carga_alta")
    if errores >= UMBRAL_ERRORES_PRESENTES:
        facts.add("errores_presentes")

    return facts


def generar_ticket_soporte(
    equipo_id: str,
    telemetria: np.ndarray,
    distancia: float,
    diagnosticos: List[str],
    alerta_automata: bool,
    secuencia_logs: str,
) -> Dict[str, Any]:
    if "incidente_critico_p1" in diagnosticos or (alerta_automata and distancia > 2.0):
        prioridad = "alta"
        categoria = "hardware"
        subcategoria = "hardware_estaciones_trabajo"
    elif "riesgo_termico" in diagnosticos or "inestabilidad_hardware" in diagnosticos:
        prioridad = "alta"
        categoria = "hardware"
        subcategoria = "hardware_estaciones_trabajo"
    elif "degradacion_servicio" in diagnosticos:
        prioridad = "media"
        categoria = "software"
        subcategoria = "sistema_operativo_mantenimiento"
    else:
        prioridad = "media"
        categoria = "hardware"
        subcategoria = "hardware_estaciones_trabajo"

    acciones: List[str] = []
    if "riesgo_termico" in diagnosticos:
        acciones.append("Verificar pasta termica, limpieza de disipador y ventilador de CPU.")
    if "degradacion_servicio" in diagnosticos:
        acciones.append("Inspeccionar procesos fugitivos de alta carga y liberar memoria RAM.")
    if "inestabilidad_hardware" in diagnosticos:
        acciones.append("Ejecutar diagnostico SMART de disco y test de modulos de memoria.")
    if alerta_automata:
        acciones.append("Alerta automata (01): aislar equipo para evitar corte abrupto no programado.")

    if not acciones:
        acciones.append("Inspeccion preventiva de rutina por desvio de metricas SLA.")

    ticket = {
        "ticket_id": f"TCK-{abs(hash(equipo_id + secuencia_logs)) % 90000 + 10000}",
        "equipo_id": equipo_id,
        "categoria": categoria,
        "subcategoria": subcategoria,
        "prioridad": prioridad,
        "incidente": "si",
        "distancia_sla": round(float(distancia), 3),
        "telemetria_observada": {
            "temperatura_cpu_c": float(telemetria[0]),
            "carga_cpu_ram_pct": float(telemetria[1]),
            "tasa_errores_min": float(telemetria[2]),
        },
        "diagnosticos_simbolicos": diagnosticos,
        "alerta_automata_01": alerta_automata,
        "secuencia_analizada": secuencia_logs,
        "accion_recomendada": " | ".join(acciones),
    }
    return ticket


def evaluar_salud_equipo(
    equipo_id: str,
    sample: np.ndarray,
    secuencia_eventos: str,
    reference: np.ndarray = BASELINE_REFERENCIA,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    distancia = calcular_distancia_telemetria(sample, reference)
    hechos = discretizar_telemetria(sample)
    diagnosticos = evaluar_reglas_simbolicas(hechos)
    alerta_automata = accepts_01(secuencia_eventos)

    no_esta_sano = (
        distancia > UMBRAL_DISTANCIA_ALERTA
        or len(diagnosticos) > 0
        or alerta_automata
    )

    if no_esta_sano:
        ticket = generar_ticket_soporte(
            equipo_id=equipo_id,
            telemetria=sample,
            distancia=distancia,
            diagnosticos=diagnosticos,
            alerta_automata=alerta_automata,
            secuencia_logs=secuencia_eventos,
        )
        return False, ticket

    return True, None


def imprimir_ticket_consola(ticket: Dict[str, Any]) -> None:
    diag_str = ", ".join(ticket["diagnosticos_simbolicos"]) if ticket["diagnosticos_simbolicos"] else "desvio_sla"
    alerta_str = "SI (Patron 01 detectado)" if ticket["alerta_automata_01"] else "NO"
    print(f"  * Ticket generado: {ticket['ticket_id']} (Prioridad: {ticket['prioridad'].upper()})")
    print(f"  * Diagnostico:     {diag_str}")
    print(f"  * Alerta automata: {alerta_str}")
    print(f"  * Accion sugerida: {ticket['accion_recomendada']}")


def main() -> None:
    sample = np.array([72.0, 0.85, 3.0])
    distance = calcular_distancia_telemetria(sample, BASELINE_REFERENCIA)
    hechos = discretizar_telemetria(sample)
    diagnosticos = evaluar_reglas_simbolicas(hechos)

    print("=" * 70)
    print("MONITORIZACION Y RECONOCIMIENTO TI - SEMANA 07")
    print("=" * 70)
    print(f"1. Numerica (Distancia SLA): {round(distance, 3)} | Muestra: {sample.tolist()}")
    print(f"2. Simbolica (Diagnosticos): {diagnosticos}")
    print(f"3. Automata DFA (Patron 01): 1101->{accepts_01('1101')}, 1110->{accepts_01('1110')}, 0001->{accepts_01('0001')}")

    print("\n" + "=" * 70)
    print("ESTADO DE EQUIPOS EN TIEMPO REAL")
    print("=" * 70)

    casos_equipos = [
        ("PC-DIRECCION-01", np.array([70.0, 0.80, 2.0]), "0000"),
        ("WS-DISENO-CAD-03", np.array([72.0, 0.85, 3.0]), "1101"),
        ("SRV-BASE-DATOS-02", np.array([76.5, 0.92, 5.0]), "0001"),
    ]

    for equipo_id, telemetria, logs in casos_equipos:
        esta_sano, ticket = evaluar_salud_equipo(equipo_id, telemetria, logs)
        print(f"\n[EQUIPO: {equipo_id}]")
        print(f"  * Telemetria:      CPU: {telemetria[0]}C | Carga: {int(telemetria[1]*100)}% | Errores: {telemetria[2]}/min")
        print(f"  * Logs temporales: '{logs}'")
        if esta_sano:
            print("  * Estado:          [OK] SALUDABLE (Dentro de SLA)")
        else:
            print("  * Estado:          [ALERTA] NO SALUDABLE (Anomalia detectada)")
            if ticket:
                imprimir_ticket_consola(ticket)
        print("-" * 70)

    print("=" * 70)


if __name__ == "__main__":
    main()
