"""Módulo de Redes Semánticas e Ingeniería del Conocimiento para Soporte TI (Semana 14).

Implementa la representación formal del conocimiento sobre infraestructura tecnológica,
activos y Elementos de Configuración (CIs) bajo lineamientos de ITIL mediante redes
semánticas, grafos dirigidos etiquetados, normalización lingüística en español,
razonamiento deductivo explicable (XAI) con reconstrucción de rutas y herencia
estricta de requerimientos operacionales y salvaguardas.
"""

from __future__ import annotations

from collections import deque
import re
from typing import Any
import unicodedata


class RequerimientosHeredados(list[str]):
    """Estructura híbrida para requerimientos heredados.

    Se comporta como list[str] ante iteraciones, pruebas de pertenencia y aserciones
    de listas estándar, y a la vez provee acceso tipo diccionario por ancestro
    para auditoría y explicabilidad (XAI).
    """

    def __init__(
        self,
        items: list[str],
        por_ancestro: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(items)
        self.por_ancestro: dict[str, list[str]] = por_ancestro or {}

    def get(self, ancestro: str, default: Any = None) -> Any:
        """Obtiene la lista de requerimientos heredados de un ancestro específico."""
        return self.por_ancestro.get(ancestro, default)

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            return self.por_ancestro[item]
        return super().__getitem__(item)

    def __contains__(self, item: Any) -> bool:
        return super().__contains__(item) or item in self.por_ancestro

    def items(self) -> Any:
        """Retorna pares (ancestro, requerimientos_aportados)."""
        return self.por_ancestro.items()

    def keys(self) -> Any:
        """Retorna las claves de ancestros contribuyentes."""
        return self.por_ancestro.keys()

    def values(self) -> Any:
        """Retorna las listas de requerimientos agrupadas por ancestro."""
        return self.por_ancestro.values()


def normalizar(texto: str) -> str:
    """Normaliza cadenas eliminando acentos (NFD) y homogeneizando a minúsculas.

    Aplica descomposición canónica Unicode (NFD) para segregar caracteres base
    de marcas diacríticas (Mn), ejecutando casefold y remoción de espacios perimetrales.

    Args:
        texto: Cadena original con potencial presencia de mayúsculas o tildes.

    Returns:
        str: Cadena normalizada sin diacríticos y en minúsculas.
    """
    base = unicodedata.normalize("NFD", texto.casefold().strip())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def interpretar(oracion: str) -> tuple[str, str, str]:
    """Interpreta oraciones declarativas en español del dominio de infraestructura TI.

    Reconoce patrones gramaticales canónicos para relaciones taxonómicas ('es_un')
    y requerimientos operativos ('requiere', 'necesita'). Rechaza oraciones fuera
    de la gramática admitida para evitar alucinaciones ontológicas.

    Args:
        oracion: Enunciado en lenguaje natural (ej. 'Un servidor_postgres es un servidor_linux.').

    Returns:
        tuple[str, str, str]: Triple canónico normalizado (sujeto, relacion, objeto).

    Raises:
        ValueError: Si la oración no coincide con los patrones formales admitidos.
    """
    texto = normalizar(oracion).strip(" .!?")

    # Patrones formales admitidos para el dominio de infraestructura ITIL
    patrones = [
        (r"(?:(?:un|una|el|la)\s+)?(\w+)\s+es\s+(?:un|una)\s+(\w+)", "es_un"),
        (r"(?:(?:un|una|el|la)\s+)?(\w+)\s+requiere\s+(?:(?:un|una|el|la)\s+)?(\w+)", "requiere"),
        (r"(?:(?:un|una|el|la)\s+)?(\w+)\s+necesita\s+(?:(?:un|una|el|la)\s+)?(\w+)", "necesita"),
    ]

    for patron, relacion in patrones:
        coincidencia = re.fullmatch(patron, texto)
        if coincidencia:
            sujeto, objeto = coincidencia.groups()
            return sujeto, relacion, objeto

    raise ValueError(f"Oración fuera de los patrones admitidos: '{oracion}'")


class RedSemanticaTI:
    """Grafo de conocimiento semántico orientado a infraestructura TI y normas ITIL.

    Representa Conceptos/Elementos de Configuración (CIs) como nodos y dependencias
    operacionales como aristas dirigidas tipadas ('es_un', 'requiere', 'necesita').
    Garantiza inferencia libre de ciclos, explicabilidad paso a paso (XAI)
    y cálculo determinista de salvaguardas heredadas.
    """

    RELACIONES_VALIDAS: set[str] = {"es_un", "requiere", "necesita"}
    RELACIONES_REQUERIMIENTO: set[str] = {"requiere", "necesita"}

    def __init__(self) -> None:
        """Inicializa una red semántica vacía con almacenamiento de lista de adyacencia."""
        self.aristas: dict[str, list[tuple[str, str]]] = {}

    def agregar(self, sujeto: str, relacion: str, objeto: str) -> None:
        """Registra un hecho explícito (sujeto, relación, objeto) de forma idempotente.

        Args:
            sujeto: Concepto origen (ej. 'servidor_postgres').
            relacion: Tipo de relación ('es_un', 'requiere', 'necesita').
            objeto: Concepto destino (ej. 'servidor_linux', 'backup_inmutable').

        Raises:
            ValueError: Si la relación no pertenece al catálogo formal admitido.
        """
        suj_norm = normalizar(sujeto)
        rel_norm = normalizar(relacion)
        obj_norm = normalizar(objeto)

        if rel_norm not in self.RELACIONES_VALIDAS:
            raise ValueError(
                f"Relación '{relacion}' no admitida. Válidas: {sorted(self.RELACIONES_VALIDAS)}"
            )

        par = (rel_norm, obj_norm)
        vecinos = self.aristas.setdefault(suj_norm, [])
        if par not in vecinos:
            vecinos.append(par)

    def es_un(self, origen: str, categoria: str) -> tuple[bool, list[str]]:
        """Determina si un concepto pertenece a una categoría mediante transitividad taxonómica.

        Aplica búsqueda en anchura (BFS) para encontrar la ruta deductiva más corta,
        incorporando control estricto de nodos visitados para prevenir bucles infinitos.
        Provee explicabilidad completa (XAI).

        Args:
            origen: Concepto de inicio (ej. 'servidor_postgres').
            categoria: Categoría meta a demostrar (ej. 'activo_ti').

        Returns:
            tuple[bool, list[str]]: (demostrado, ruta_deductiva_paso_a_paso).
                Si es verdadero, la ruta contiene los nodos recorridos [origen, ..., categoria].
                Si es falso o inalcanzable, retorna (False, []).
        """
        orig_norm = normalizar(origen)
        cat_norm = normalizar(categoria)

        if orig_norm == cat_norm:
            return True, [orig_norm]

        cola: deque[tuple[str, list[str]]] = deque([(orig_norm, [orig_norm])])
        visitados: set[str] = set()

        while cola:
            actual, camino = cola.popleft()

            if actual in visitados:
                continue
            visitados.add(actual)

            for rel, destino in self.aristas.get(actual, []):
                if rel == "es_un":
                    nuevo_camino = camino + [destino]
                    if destino == cat_norm:
                        return True, nuevo_camino
                    if destino not in visitados:
                        cola.append((destino, nuevo_camino))

        return False, []

    def obtener_ancestros(self, concepto: str) -> list[str]:
        """Obtiene la jerarquía ascendente ordenada de categorías para un concepto.

        Args:
            concepto: Nodo inicial a inspeccionar.

        Returns:
            list[str]: Lista con el concepto inicial seguido de sus superclases transitivas.
        """
        concepto_norm = normalizar(concepto)
        jerarquia: list[str] = [concepto_norm]
        cola: deque[str] = deque([concepto_norm])
        visitados: set[str] = {concepto_norm}

        while cola:
            actual = cola.popleft()
            for rel, destino in self.aristas.get(actual, []):
                if rel == "es_un" and destino not in visitados:
                    visitados.add(destino)
                    jerarquia.append(destino)
                    cola.append(destino)

        return jerarquia

    def requerimientos(self, concepto: str) -> dict[str, Any]:
        """Calcula de forma rigurosa los requerimientos directos y los heredados por ITIL.

        Inspecciona el nodo especificado y asciende a través de su árbol taxonómico
        'es_un' agregando salvaguardas operacionales directas y heredadas sin duplicados.

        Args:
            concepto: Elemento de Configuración a auditar (ej. 'servidor_postgres').

        Returns:
            dict[str, Any]: Estructura que contiene:
                - concepto: Nombre normalizado del CI auditado.
                - jerarquia_ascendente: Secuencia de ancestros taxonómicos alcanzados.
                - requerimientos_directos: Lista ordenada de salvaguardas directas.
                - requerimientos_heredados: Objeto RequerimientosHeredados con trazabilidad.
                - requerimientos_totales: Unión ordenada y única de todas las exigencias.
                - trazabilidad_herencia: Diccionario {ancestro: [salvaguardas]}.
        """
        concepto_norm = normalizar(concepto)
        jerarquia = self.obtener_ancestros(concepto_norm)

        directos_set: set[str] = set()
        for rel, destino in self.aristas.get(concepto_norm, []):
            if rel in self.RELACIONES_REQUERIMIENTO:
                directos_set.add(destino)
        requerimientos_directos = sorted(directos_set)

        heredados_por_ancestro: dict[str, list[str]] = {}
        todos_heredados_set: set[str] = set()

        # Recorrer ancestros superiores (excluyendo el concepto evaluado)
        for ancestro in jerarquia[1:]:
            reqs_ancestro: set[str] = set()
            for rel, destino in self.aristas.get(ancestro, []):
                if rel in self.RELACIONES_REQUERIMIENTO:
                    reqs_ancestro.add(destino)
                    todos_heredados_set.add(destino)
            if reqs_ancestro:
                heredados_por_ancestro[ancestro] = sorted(reqs_ancestro)

        requerimientos_heredados_lista = sorted(todos_heredados_set)
        requerimientos_heredados = RequerimientosHeredados(
            items=requerimientos_heredados_lista,
            por_ancestro=heredados_por_ancestro,
        )

        requerimientos_totales = sorted(directos_set | todos_heredados_set)

        return {
            "concepto": concepto_norm,
            "jerarquia_ascendente": jerarquia,
            "requerimientos_directos": requerimientos_directos,
            "requerimientos_heredados": requerimientos_heredados,
            "requerimientos_totales": requerimientos_totales,
            "trazabilidad_herencia": heredados_por_ancestro,
        }

    def evaluar_caso_soporte(
        self,
        concepto: str,
        categoria_consulta: str | None = None,
    ) -> dict[str, Any]:
        """Ejecuta una evaluación integral de soporte y conformidad ITIL para un activo.

        Args:
            concepto: Elemento de Configuración evaluado.
            categoria_consulta: Categoría opcional a verificar (ej. 'activo_ti').

        Returns:
            dict[str, Any]: Dictamen técnico con validación taxonómica, requerimientos y XAI.
        """
        analisis_reqs = self.requerimientos(concepto)
        resultado: dict[str, Any] = {
            "ci_evaluado": concepto,
            "estado_evaluacion": "COMPLETADA",
            "jerarquia": analisis_reqs["jerarquia_ascendente"],
            "requerimientos_directos": analisis_reqs["requerimientos_directos"],
            "requerimientos_heredados": analisis_reqs["requerimientos_heredados"],
            "requerimientos_totales": analisis_reqs["requerimientos_totales"],
            "trazabilidad": analisis_reqs["trazabilidad_herencia"],
        }

        if categoria_consulta:
            pertenece, ruta = self.es_un(concepto, categoria_consulta)
            resultado["consulta_categoria"] = categoria_consulta
            resultado["es_miembro"] = pertenece
            resultado["ruta_deduccion_xai"] = ruta
            if pertenece:
                camino_str = " -> ".join(ruta)
                resultado["dictamen_taxonomico"] = (
                    f"El elemento '{concepto}' pertenece a la categoría '{categoria_consulta}' "
                    f"siguiendo la cadena de inferencia: {camino_str}."
                )
            else:
                resultado["dictamen_taxonomico"] = (
                    f"No existe evidencia ni transitividad en la red para afirmar que "
                    f"'{concepto}' es un '{categoria_consulta}'."
                )

        return resultado


def construir_red_soporte_ti() -> RedSemanticaTI:
    """Construye y puebla la red semántica estándar de infraestructura TI e ITIL.

    Returns:
        RedSemanticaTI: Red con los 10 hechos ontológicos fundamentales del centro de datos.
    """
    red = RedSemanticaTI()
    oraciones_itil = [
        "Un servidor_postgres es un servidor_linux.",
        "Un servidor_linux es un servidor_computo.",
        "Un servidor_computo es un activo_ti.",
        "Un activo_ti requiere energia_ups.",
        "Un activo_ti requiere monitoreo_snmp.",
        "Un servidor_computo requiere sistema_operativo.",
        "Un servidor_linux requiere acceso_ssh_bastion.",
        "Un servidor_postgres requiere backup_inmutable.",
        "Un firewall_perimetral es un dispositivo_seguridad.",
        "Un dispositivo_seguridad es un activo_ti.",
    ]
    for oracion in oraciones_itil:
        sujeto, relacion, objeto = interpretar(oracion)
        red.agregar(sujeto, relacion, objeto)

    return red


def main() -> None:
    """Demostración en consola de razonamiento con redes semánticas en infraestructura TI."""
    print("=" * 80)
    print("DEMOSTRACIÓN SEMANA 14: REDES SEMÁNTICAS E INGENIERÍA DEL CONOCIMIENTO (ITIL)")
    print("=" * 80)

    # 1. Construcción de la base de conocimiento declarativa
    red = construir_red_soporte_ti()
    print("\n[FASE 1] Hechos cargados en la base de conocimiento:")
    for sujeto, aristas in sorted(red.aristas.items()):
        for rel, destino in aristas:
            print(f"  Hecho explícito: ({sujeto}, {rel}, {destino})")

    # 2. Inferencia directa vs transitiva (XAI)
    ci_estudio = "servidor_postgres"
    print(f"\n[FASE 2] Consultas taxonómicas y deductivas para '{ci_estudio}' (Datacenter Bogotá):")

    es_linux, ruta_linux = red.es_un(ci_estudio, "servidor_linux")
    print(f"  ¿{ci_estudio} es_un servidor_linux? (Inferencia directa): {es_linux}")
    print(f"    Ruta XAI: {' -> '.join(ruta_linux)}")

    es_activo, ruta_activo = red.es_un(ci_estudio, "activo_ti")
    print(f"  ¿{ci_estudio} es_un activo_ti? (Inferencia transitiva profunda): {es_activo}")
    print(f"    Ruta XAI: {' -> '.join(ruta_activo)}")

    es_firewall, _ = red.es_un(ci_estudio, "firewall_perimetral")
    print(f"  ¿{ci_estudio} es_un firewall_perimetral? (Caso negativo / grafo cerrado): {es_firewall}")

    # 3. Herencia estricta de requerimientos y salvaguardas operacionales
    print(f"\n[FASE 3] Síntesis de requerimientos y salvaguardas para '{ci_estudio}':")
    reqs = red.requerimientos(ci_estudio)
    print(f"  Jerarquía taxonómica: {' -> '.join(reqs['jerarquia_ascendente'])}")
    print(f"  Requerimientos directos: {reqs['requerimientos_directos']}")
    print(f"  Requerimientos heredados: {reqs['requerimientos_heredados']}")
    print("  Trazabilidad de herencia por ancestro:")
    for ancestro, salvaguardas in reqs["trazabilidad_herencia"].items():
        print(f"    - Desde [{ancestro}]: {salvaguardas}")
    print(f"  Total salvaguardas consolidadas: {reqs['requerimientos_totales']}")

    # 4. Evaluación de caso de soporte ITIL
    print("\n[FASE 4] Evaluación formal de caso de soporte ITIL:")
    evaluacion = red.evaluar_caso_soporte(ci_estudio, categoria_consulta="activo_ti")
    print(f"  Dictamen: {evaluacion['dictamen_taxonomico']}")
    print(f"  Total salvaguardas requeridas: {len(evaluacion['requerimientos_totales'])}")
    print("=" * 80)


if __name__ == "__main__":
    main()
