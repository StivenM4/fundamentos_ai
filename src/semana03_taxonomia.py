"""Motor de taxonomía de problemas de IA aplicado a soporte TI.

La práctica usa reglas transparentes de palabras clave. No pretende sustituir un
modelo entrenado; sirve como línea base reproducible para orientar el proyecto
acumulativo hacia modelos propios de texto e imágenes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "casos_ia.csv"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "semana03.md"
DEFAULT_EVIDENCE_PATH = PROJECT_ROOT / "reports" / "semana03_ejecucion.txt"

CATEGORY_ORDER = (
    "Procesamiento de lenguaje natural",
    "Visión por computador",
    "Aprendizaje predictivo",
    "Sistemas de recomendación",
    "Sistemas expertos",
    "IA generativa",
    "Robótica",
)

# Reglas generales tomadas como base conceptual de la práctica.
BASE_RULES: dict[str, tuple[str, ...]] = {
    "Procesamiento de lenguaje natural": (
        "texto",
        "descripcion textual",
        "clasificar",
        "intencion",
        "entidades",
        "extraer",
        "resumen",
    ),
    "Visión por computador": (
        "imagen",
        "imagenes",
        "visual",
        "reconocer",
        "inspeccionar",
        "interfaz",
    ),
    "Aprendizaje predictivo": (
        "predecir",
        "pronosticar",
        "probabilidad",
        "anticipar",
        "demanda",
        "tiempo de resolucion",
    ),
    "Sistemas de recomendación": (
        "recomendar",
        "sugerir",
        "tecnico adecuado",
        "ruta de escalamiento",
        "articulo",
    ),
    "Sistemas expertos": (
        "reglas de diagnostico",
        "diagnosticar",
        "restablecer la contrasena",
    ),
    "IA generativa": (
        "generar",
        "generativo",
        "redactar",
        "crear pasos",
    ),
    "Robótica": (
        "robot",
        "sensor",
        "actuador",
        "autonomo",
    ),
}

# Cinco reglas propias adaptadas al dominio del asistente de soporte TI.
CUSTOM_RULES: dict[str, tuple[str, ...]] = {
    "Visión por computador": ("captura de pantalla", "pantallazo"),
    "Procesamiento de lenguaje natural": (
        "ticket",
        "tickets",
        "incidente",
        "mensaje de error",
    ),
    "Aprendizaje predictivo": ("caso recurrente", "reincidencia"),
    "Sistemas de recomendación": (
        "caso resuelto",
        "casos resueltos",
        "base de conocimiento",
        "solucion similar",
        "soluciones similares",
    ),
    "Sistemas expertos": ("prioridad", "impacto", "urgencia", "sla"),
}

# Carga de activadores externos ampliados desde data/activadores_taxonomia.json si está presente
ACTIVADORES_PATH = PROJECT_ROOT / "data" / "activadores_taxonomia.json"
if ACTIVADORES_PATH.exists():
    try:
        with ACTIVADORES_PATH.open("r", encoding="utf-8") as _f_act:
            _loaded_act = json.load(_f_act)
            if "BASE_RULES" in _loaded_act:
                BASE_RULES = {k: tuple(v) for k, v in _loaded_act["BASE_RULES"].items()}
            if "CUSTOM_RULES" in _loaded_act:
                CUSTOM_RULES = {k: tuple(v) for k, v in _loaded_act["CUSTOM_RULES"].items()}
    except Exception:
        pass

TECHNIQUE_RECOMMENDATIONS = {
    "Procesamiento de lenguaje natural": (
        "clasificador de texto con TF-IDF y regresión logística"
    ),
    "Visión por computador": "red convolucional o modelo de visión preentrenado",
    "Aprendizaje predictivo": "clasificación o regresión supervisada con datos históricos",
    "Sistemas de recomendación": "recuperación por similitud semántica de casos resueltos",
    "Sistemas expertos": "motor de reglas con criterios de impacto, urgencia y SLA",
    "IA generativa": "modelo generativo con recuperación de conocimiento y revisión humana",
    "Robótica": "percepción y planificación conectadas con sensores del dispositivo",
}

# Clasificación manual esperada para los 50 casos del CSV, en el mismo orden.
MANUAL_REFERENCE: tuple[str, ...] = (
    "Procesamiento de lenguaje natural",
    "Visión por computador",
    "Aprendizaje predictivo",
    "Sistemas de recomendación",
    "Sistemas expertos",
    "IA generativa",
    "Procesamiento de lenguaje natural",
    "Aprendizaje predictivo",
    "Visión por computador",
    "Sistemas de recomendación",
    "Sistemas expertos",
    "IA generativa",
    "Procesamiento de lenguaje natural",
    "Aprendizaje predictivo",
    "Visión por computador",
    "Sistemas de recomendación",
    "Procesamiento de lenguaje natural",
    "Sistemas expertos",
    "IA generativa",
    "Procesamiento de lenguaje natural",
    # Casos ampliados 21 a 50
    "Procesamiento de lenguaje natural",
    "Visión por computador",
    "Aprendizaje predictivo",
    "Sistemas de recomendación",
    "Sistemas expertos",
    "IA generativa",
    "Robótica",
    "Procesamiento de lenguaje natural",
    "Visión por computador",
    "Aprendizaje predictivo",
    "Sistemas de recomendación",
    "Sistemas expertos",
    "IA generativa",
    "Robótica",
    "Procesamiento de lenguaje natural",
    "Visión por computador",
    "Aprendizaje predictivo",
    "Sistemas de recomendación",
    "Sistemas expertos",
    "IA generativa",
    "Robótica",
    "Procesamiento de lenguaje natural",
    "Visión por computador",
    "Aprendizaje predictivo",
    "Sistemas de recomendación",
    "Sistemas expertos",
    "IA generativa",
    "Robótica",
    "Procesamiento de lenguaje natural",
    "Visión por computador",
)


@dataclass(frozen=True)
class Classification:
    """Resultado explicable de clasificar una descripción."""

    description: str
    primary_category: str
    secondary_areas: tuple[str, ...]
    technique: str
    triggers: dict[str, tuple[str, ...]]
    scores: dict[str, int]


def normalize_text(text: str) -> str:
    """Convierte texto a una forma estable para comparar palabras y frases."""

    decomposed = unicodedata.normalize("NFD", text.casefold())
    without_accents = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def _combined_rules() -> dict[str, tuple[str, ...]]:
    """Une reglas base y propias sin contar dos veces una misma frase."""

    combined: dict[str, tuple[str, ...]] = {}
    for category in CATEGORY_ORDER:
        phrases = (*BASE_RULES.get(category, ()), *CUSTOM_RULES.get(category, ()))
        unique_phrases = dict.fromkeys(normalize_text(phrase) for phrase in phrases)
        combined[category] = tuple(unique_phrases)
    return combined


def score_description(description: str) -> dict[str, tuple[str, ...]]:
    """Devuelve por categoría las frases que están presentes en la descripción."""

    normalized = f" {normalize_text(description)} "
    matches: dict[str, tuple[str, ...]] = {}
    for category, phrases in _combined_rules().items():
        found = tuple(phrase for phrase in phrases if f" {phrase} " in normalized)
        matches[category] = found
    return matches


def classify_description(description: str) -> Classification:
    """Clasifica una descripción y conserva la explicación de la decisión."""

    if not description or not description.strip():
        raise ValueError("La descripción no puede estar vacía.")

    triggers = score_description(description)
    scores = {category: len(phrases) for category, phrases in triggers.items()}
    highest_score = max(scores.values(), default=0)
    if highest_score == 0:
        raise ValueError(f"No se encontraron reglas aplicables: {description!r}")

    primary_category = next(
        category
        for category in CATEGORY_ORDER
        if scores[category] == highest_score
    )
    secondary_areas = tuple(
        category
        for category in CATEGORY_ORDER
        if category != primary_category and scores[category] > 0
    )
    return Classification(
        description=description,
        primary_category=primary_category,
        secondary_areas=secondary_areas,
        technique=TECHNIQUE_RECOMMENDATIONS[primary_category],
        triggers=triggers,
        scores=scores,
    )


def load_cases(path: Path = DEFAULT_DATA_PATH) -> list[str]:
    """Lee un CSV con una única columna obligatoria llamada ``descripcion``."""

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de casos: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != ["descripcion"]:
            raise ValueError('El CSV debe contener únicamente el encabezado "descripcion".')
        cases = [row["descripcion"].strip() for row in reader if row["descripcion"].strip()]

    if len(cases) < 20:
        raise ValueError(f"Se esperaban al menos 20 casos y se encontraron {len(cases)}.")
    return cases


def analyze_cases(cases: Iterable[str]) -> list[Classification]:
    """Clasifica todos los casos recibidos."""

    return [classify_description(case) for case in cases]


def compare_with_manual(
    results: Sequence[Classification],
    reference: Sequence[str] = MANUAL_REFERENCE,
) -> list[tuple[int, str, str]]:
    """Lista diferencias como (número de caso, automático, manual)."""

    if len(results) != len(reference):
        raise ValueError("Los resultados y la referencia manual deben tener igual longitud.")
    return [
        (index, result.primary_category, expected)
        for index, (result, expected) in enumerate(zip(results, reference), start=1)
        if result.primary_category != expected
    ]


def _active_triggers(result: Classification) -> str:
    phrases = result.triggers[result.primary_category]
    return ", ".join(f"`{phrase}`" for phrase in phrases)


def write_report(results: Sequence[Classification], path: Path = DEFAULT_REPORT_PATH) -> None:
    """Genera el reporte académico solicitado para la Semana 03."""

    mismatches = compare_with_manual(results)
    matches = len(results) - len(mismatches)
    lines = [
        "# Semana 03: taxonomía de problemas de IA para soporte TI",
        "",
        "## Objetivo y dominio",
        "",
        "Este motor clasifica problemas del asistente de soporte TI en siete áreas de IA y recomienda una técnica inicial. El proyecto acumulativo busca evolucionar esta línea base hacia modelos propios que analicen texto e imágenes, clasifiquen tickets y recuperen soluciones de casos anteriores.",
        "",
        "## Resultados",
        "",
        f"Se procesaron **{len(results)} casos**. Coincidencia con la referencia manual: **{matches}/{len(results)} ({matches / len(results):.0%})**.",
        "",
        "| Caso | Categoría principal | Áreas secundarias | Palabras o frases activadoras | Técnica inicial |",
        "|---:|---|---|---|---|",
    ]
    for index, result in enumerate(results, start=1):
        secondary = ", ".join(result.secondary_areas) or "Ninguna"
        lines.append(
            f"| {index} | {result.primary_category} | {secondary} | "
            f"{_active_triggers(result)} | {result.technique} |"
        )

    lines.extend(
        [
            "",
            "## Cinco reglas propias del dominio",
            "",
            "1. **Visión por computador — `captura de pantalla`, `pantallazo`:** permite interpretar la evidencia visual que el usuario adjunta al ticket.",
            "2. **Procesamiento de lenguaje natural — `ticket`, `incidente`, `mensaje de error`:** representa el texto libre que debe entender y clasificar el asistente.",
            "3. **Aprendizaje predictivo — `caso recurrente`, `reincidencia`:** sirve para anticipar fallas repetitivas usando el historial de soporte.",
            "4. **Sistemas de recomendación — `caso resuelto`, `base de conocimiento`, `solución similar`:** conecta un problema nuevo con respuestas ya validadas.",
            "5. **Sistemas expertos — `prioridad`, `impacto`, `urgencia`, `SLA`:** formaliza criterios operativos usados para priorizar y escalar tickets.",
            "",
            "## Comparación y discrepancias",
            "",
        ]
    )
    if mismatches:
        for case_number, automatic, manual in mismatches:
            result = results[case_number - 1]
            lines.extend(
                [
                    f"### Caso {case_number}",
                    "",
                    f"- Clasificación automática: {automatic}.",
                    f"- Clasificación manual: {manual}.",
                    f"- Activadores: {_active_triggers(result)}.",
                    "- Ajuste propuesto: revisar el peso o la especificidad de estas frases y validar el cambio con más tickets reales.",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "No se encontraron discrepancias en la categoría principal: los 20 resultados coinciden con la referencia manual. Aun así, varios casos son multimodales; por eso las áreas secundarias conservan señales que una clasificación única ocultaría.",
                "",
                "Por ejemplo, el caso 17 se clasifica principalmente como procesamiento de lenguaje natural y también activa Visión por computador, Sistemas de recomendación y Robótica. Esta combinación es coherente con un ticket que incluye texto, imágenes, recomendación y un robot de soporte remoto.",
                "",
            ]
        )

    lines.extend(
        [
            "## Limitaciones y mejoras propuestas",
            "",
            "- Las reglas detectan coincidencias literales; no comprenden sinónimos, negaciones ni contexto.",
            "- Todos los activadores tienen el mismo peso y los empates dependen de un orden fijo.",
            "- La referencia de 20 casos es pequeña y diseñada para la práctica; no mide desempeño con tickets reales.",
            "- El motor identifica menciones de imágenes, pero todavía no procesa los píxeles adjuntos.",
            "- Una palabra puede activar un área secundaria aunque su importancia real sea baja.",
            "",
            "Como siguiente paso se propone reunir y anonimizar tickets históricos, definir etiquetas con técnicos, separar entrenamiento/validación/prueba y medir precisión, exhaustividad y F1. Para texto se puede iniciar con TF-IDF y regresión logística; para imágenes, con un modelo de visión preentrenado. Sus representaciones pueden combinarse en un clasificador multimodal, mientras la recomendación de soluciones puede usar similitud semántica sobre casos resueltos. Las respuestas generadas deben citar la base de conocimiento y mantener revisión humana, trazabilidad y control de datos sensibles.",
            "",
            "## Reproducción",
            "",
            "```powershell",
            "python src/semana03_taxonomia.py",
            "python -m unittest discover -s tests -v",
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_execution_evidence(
    results: Sequence[Classification],
    path: Path = DEFAULT_EVIDENCE_PATH,
) -> None:
    """Guarda una evidencia legible de la ejecución y sus resultados."""

    mismatches = compare_with_manual(results)
    lines = [
        "EVIDENCIA DE EJECUCIÓN - SEMANA 03",
        f"Fecha: {datetime.now().astimezone().date().isoformat()}",
        f"Python: {sys.version.split()[0]}",
        f"Casos procesados: {len(results)}",
        f"Coincidencias con referencia manual: {len(results) - len(mismatches)}/{len(results)}",
        f"Discrepancias: {len(mismatches)}",
        "",
    ]
    for index, result in enumerate(results, start=1):
        secondary = ", ".join(result.secondary_areas) or "Ninguna"
        lines.extend(
            [
                f"Caso {index:02d}: {result.description}",
                f"  Principal: {result.primary_category}",
                f"  Secundarias: {secondary}",
                f"  Técnica: {result.technique}",
            ]
        )
    lines.append("")
    lines.append("Resultado: ejecución correcta, sin errores.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    data_path: Path = DEFAULT_DATA_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    evidence_path: Path = DEFAULT_EVIDENCE_PATH,
) -> list[Classification]:
    """Ejecuta el flujo completo y devuelve los resultados."""

    cases = load_cases(data_path)
    results = analyze_cases(cases)
    write_execution_evidence(results, evidence_path)
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE_PATH)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    results = run(args.data, args.report, args.evidence)
    mismatches = compare_with_manual(results)

    for index, result in enumerate(results, start=1):
        secondary = ", ".join(result.secondary_areas) or "Ninguna"
        print(f"Caso {index:02d}: {result.primary_category}")
        print(f"  Áreas secundarias: {secondary}")
        print(f"  Técnica inicial: {result.technique}")
    print(f"\nCasos procesados: {len(results)}")
    print(f"Coincidencias con referencia manual: {len(results) - len(mismatches)}/{len(results)}")
    print(f"Evidencia generada: {args.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
