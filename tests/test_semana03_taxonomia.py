"""Pruebas del motor de taxonomía de la Semana 03."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from semana03_taxonomia import (  # noqa: E402
    DEFAULT_DATA_PATH,
    MANUAL_REFERENCE,
    analyze_cases,
    classify_description,
    compare_with_manual,
    load_cases,
    normalize_text,
)


class TaxonomiaSemana03Tests(unittest.TestCase):
    def test_normaliza_acentos_mayusculas_y_signos(self) -> None:
        self.assertEqual(normalize_text("¡URGENCIA y solución!"), "urgencia y solucion")

    def test_csv_contiene_los_20_casos(self) -> None:
        self.assertEqual(len(load_cases(DEFAULT_DATA_PATH)), 20)

    def test_clasifica_un_ticket_de_texto(self) -> None:
        result = classify_description("Clasificar el texto de un ticket de soporte")
        self.assertEqual(result.primary_category, "Procesamiento de lenguaje natural")

    def test_clasifica_evidencia_visual(self) -> None:
        result = classify_description(
            "Analizar una captura de pantalla y reconocer una anomalía visual"
        )
        self.assertEqual(result.primary_category, "Visión por computador")

    def test_caso_17_incluye_robotica_como_area_secundaria(self) -> None:
        result = classify_description(load_cases(DEFAULT_DATA_PATH)[16])
        self.assertEqual(result.primary_category, "Procesamiento de lenguaje natural")
        self.assertIn("Robótica", result.secondary_areas)

    def test_los_20_casos_coinciden_con_la_referencia_manual(self) -> None:
        results = analyze_cases(load_cases(DEFAULT_DATA_PATH))
        self.assertEqual(len(MANUAL_REFERENCE), 20)
        self.assertEqual(compare_with_manual(results), [])


if __name__ == "__main__":
    unittest.main()
