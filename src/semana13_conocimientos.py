"""Módulo de Ingeniería del Conocimiento y Sistemas Lógicos (Semana 13).

Implementa un motor de inferencia formal basado en encadenamiento hacia adelante
(Forward Chaining) con Cláusulas de Horn definidas para la gestión de incidentes
críticos y autorización de cambios de emergencia en infraestructura de TI (ITIL).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Regla:
    """Representación inmutable de una regla lógica de producción (Cláusula de Horn definida).

    Atributos:
        nombre: Identificador de la regla (ej. 'R1', 'R2').
        premisas: Conjunto inmutable de antecedentes (frozenset de hechos requeridos).
        conclusion: Consecuente deducido si todas las premisas están presentes en los hechos.
    """

    nombre: str
    premisas: frozenset[str]
    conclusion: str


def construir_reglas() -> list[Regla]:
    """Construye la base de conocimiento con reglas de Horn para soporte TI e ITIL.

    Reglas lógicas de producción (Horn Clauses):
        - R1: {"telemetria_critica_confirmada", "error_kernel_panic_ocr"} => "falla_hardware_severa"
        - R2: {"falla_hardware_severa", "servicio_core_afectado", "impacto_usuarios_masivo"} => "incidente_p1_mayor"
        - R3: {"incidente_p1_mayor", "sin_redundancia_activa"} => "requiere_cambio_emergencia"
        - R4: {"incidente_p1_mayor", "aprobacion_incident_manager"} => "activacion_comite_crisis_l3"
        - R5: {"requiere_cambio_emergencia", "activacion_comite_crisis_l3"} => "despliegue_hotfix_autorizado"

    Returns:
        list[Regla]: Colección ordenada de reglas de producción.
    """
    return [
        Regla(
            nombre="R1",
            premisas=frozenset({
                "telemetria_critica_confirmada",
                "error_kernel_panic_ocr",
            }),
            conclusion="falla_hardware_severa",
        ),
        Regla(
            nombre="R2",
            premisas=frozenset({
                "falla_hardware_severa",
                "servicio_core_afectado",
                "impacto_usuarios_masivo",
            }),
            conclusion="incidente_p1_mayor",
        ),
        Regla(
            nombre="R3",
            premisas=frozenset({
                "incidente_p1_mayor",
                "sin_redundancia_activa",
            }),
            conclusion="requiere_cambio_emergencia",
        ),
        Regla(
            nombre="R4",
            premisas=frozenset({
                "incidente_p1_mayor",
                "aprobacion_incident_manager",
            }),
            conclusion="activacion_comite_crisis_l3",
        ),
        Regla(
            nombre="R5",
            premisas=frozenset({
                "requiere_cambio_emergencia",
                "activacion_comite_crisis_l3",
            }),
            conclusion="despliegue_hotfix_autorizado",
        ),
    ]


def inferir(
    hechos_iniciales: set[str],
    reglas: list[Regla],
) -> tuple[set[str], list[str]]:
    """Aplica encadenamiento hacia adelante (Forward Chaining) basado en Cláusulas de Horn.

    Función matemática pura: no muta hechos_iniciales ni las reglas provistas.
    Garantiza terminación monótona en tiempo finito O(R * |H|).

    Args:
        hechos_iniciales: Conjunto de hechos o evidencias conocidas a priori.
        reglas: Colección de reglas de producción a contrastar.

    Returns:
        tuple[set[str], list[str]]:
            - Conjunto de hechos finales (hechos iniciales + deducciones inferidas).
            - Lista de trazas explicables en orden cronológico de activación.
    """
    hechos: set[str] = set(hechos_iniciales)
    trazas: list[str] = []
    cambios: bool = True

    while cambios:
        cambios = False
        for regla in reglas:
            if regla.premisas.issubset(hechos) and regla.conclusion not in hechos:
                hechos.add(regla.conclusion)
                detalle = ", ".join(sorted(regla.premisas))
                trazas.append(f"{regla.nombre}: {detalle} => {regla.conclusion}")
                cambios = True

    return hechos, trazas


def evaluar_caso_soporte(
    hechos_iniciales: set[str],
    meta: str = "despliegue_hotfix_autorizado",
    reglas: list[Regla] | None = None,
) -> dict[str, Any]:
    """Evalúa un caso de soporte ITIL determinando si una meta o acción crítica queda demostrada.

    Args:
        hechos_iniciales: Evidencias y telemetría observadas.
        meta: Meta a validar mediante encadenamiento hacia adelante.
        reglas: Base de reglas a utilizar (por defecto construir_reglas()).

    Returns:
        dict[str, Any]:
            {
                "hechos_iniciales": sorted(list(hechos_iniciales)),
                "hechos_finales": sorted(list(hechos_finales)),
                "trazabilidad": trazas,
                "meta": meta,
                "demostrada": bool,
                "estado": str ("DEMOSTRADA" | "NO DEMOSTRADA con los hechos disponibles")
            }
    """
    if reglas is None:
        reglas = construir_reglas()

    hechos_finales, trazas = inferir(hechos_iniciales, reglas)
    demostrada = meta in hechos_finales

    return {
        "hechos_iniciales": sorted(list(hechos_iniciales)),
        "hechos_finales": sorted(list(hechos_finales)),
        "trazabilidad": trazas,
        "meta": meta,
        "demostrada": demostrada,
        "estado": "DEMOSTRADA" if demostrada else "NO DEMOSTRADA con los hechos disponibles",
    }


def mostrar_escenario(nombre: str, hechos_iniciales: set[str], meta: str = "despliegue_hotfix_autorizado") -> None:
    """Función auxiliar para formatear la salida en terminal de un escenario de inferencia."""
    resultado = evaluar_caso_soporte(hechos_iniciales, meta=meta)
    print(f"\n{nombre}")
    print("Hechos iniciales:", ", ".join(resultado["hechos_iniciales"]))
    for paso in resultado["trazabilidad"]:
        print(f"Inferencia: {paso}")
    print(f"{meta}: {resultado['estado']}")


def main() -> None:
    """Punto de entrada de ejecución didáctica de la Semana 13."""
    print("=" * 80)
    print("SISTEMA EXPERTO DE INFERENCIA LÓGICA - SEMANA 13 (INGENIERÍA DEL CONOCIMIENTO)")
    print("Dominio: Gestión de Incidentes Críticos y Cambios de Emergencia ITIL")
    print("=" * 80)

    # CASO A: Evidencia completa
    caso_a = {
        "telemetria_critica_confirmada",
        "error_kernel_panic_ocr",
        "servicio_core_afectado",
        "impacto_usuarios_masivo",
        "sin_redundancia_activa",
        "aprobacion_incident_manager",
    }
    mostrar_escenario("CASO A (Evidencia completa y aprobaciones):", caso_a)

    # CASO B: Falta de aprobación de Incident Manager
    caso_b = {
        "telemetria_critica_confirmada",
        "error_kernel_panic_ocr",
        "servicio_core_afectado",
        "impacto_usuarios_masivo",
        "sin_redundancia_activa",
    }
    mostrar_escenario("CASO B (Sin aprobación del Incident Manager):", caso_b)
    print("=" * 80)


if __name__ == "__main__":
    main()
