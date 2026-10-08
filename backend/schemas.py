from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class TicketRequest(BaseModel):
    """Datos de entrada para solicitar el análisis de un ticket a los motores de IA."""

    subject: str = Field(
        ...,
        min_length=1,
        description="Asunto o título resumido del ticket",
        examples=["Caída de Base de Datos Producción"],
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Descripción detallada de la anomalía o requerimiento",
        examples=[
            "El cluster de base de datos PostgreSQL de producción se detuvo repentinamente con alarma de timeout en el pool de conexiones."
        ],
    )
    blocked_steps: Optional[List[str]] = Field(
        default_factory=list,
        description="Lista opcional de nodos bloqueados para el cálculo de ruta A*",
    )


class ClassificationResult(BaseModel):
    """Resultado de clasificación, criticidad, evidencia léxica y SLA."""

    category: str = Field(..., description="Categoría asignada al ticket")
    priority: str = Field(..., description="Nivel de prioridad (CRÍTICA, ALTA, MEDIA, BAJA)")
    confidence_score: float = Field(..., description="Nivel de confianza o certidumbre (0.0 a 1.0)")
    lexical_evidence: List[str] = Field(
        default_factory=list,
        description="Palabras o tokens léxicos activadores encontrados",
    )
    sla_minutes: int = Field(..., description="Tiempo máximo comprometido de SLA en minutos")


class AStarStep(BaseModel):
    """Detalle de un paso individual en la ruta óptima calculada por A*."""

    step_number: int = Field(..., description="Número ordinal del paso en la ruta")
    node_id: str = Field(..., description="Identificador único del nodo en el grafo de soporte")
    title: str = Field(..., description="Título legible de la acción o fase")
    description: str = Field(..., description="Descripción detallada de la acción operativa")
    role: str = Field(..., description="Rol técnico responsable de ejecutar el paso")
    g: int = Field(..., description="Costo acumulado desde el nodo inicial g(n)")
    h: int = Field(..., description="Valor heurístico estimado hasta la meta h(n)")
    f: int = Field(..., description="Función de evaluación total f(n) = g(n) + h(n)")
    is_goal: bool = Field(default=False, description="Indica si corresponde al estado meta")


class AStarRoute(BaseModel):
    """Resultado del motor de búsqueda heurística A* (Semana 04)."""

    total_cost: int = Field(..., description="Costo total acumulado de la ruta óptima")
    heuristic_states: int = Field(..., description="Número de estados explorados por A*")
    blind_search_states: int = Field(..., description="Estados explorados por búsqueda sin información")
    efficiency_gain_pct: float = Field(..., description="Porcentaje de ganancia de eficiencia")
    steps: List[AStarStep] = Field(..., description="Secuencia ordenada de pasos a ejecutar")


class RagSop(BaseModel):
    """Procedimiento Operativo Estándar (SOP) recuperado por el motor híbrido RAG (Semana 05)."""

    runbook_id: str = Field(..., description="Identificador del Runbook o SOP")
    title: str = Field(..., description="Título del procedimiento recuperado")
    similarity_score: float = Field(..., description="Similitud semántica coseno (0.0 a 1.0)")
    precautions: str = Field(..., description="Precauciones operativas y advertencias críticas")
    checklist: List[str] = Field(..., description="Lista de verificación paso a paso")


class VisualAnalysis(BaseModel):
    """Resultado del reconocimiento de capturas con la Red Neuronal MLP (Semana 08) y pipeline de visión (Semana 09)."""

    detected_class: str = Field(..., description="Clase predicha por el modelo de visión neuronal de Semana 08")
    class_label: str = Field(..., description="Etiqueta descriptiva y legible de la anomalía visual")
    confidence_score: float = Field(..., description="Puntuación de confianza (0.0 a 1.0)")
    confidence_pct: str = Field(..., description="Porcentaje legible de confianza (ej. '98.4%')")
    saved_image_path: str = Field(..., description="Ruta relativa o absoluta del archivo guardado en el servidor")
    image_url: Optional[str] = Field(None, description="URL pública o accesible para servir la imagen estática")
    impact_category: str = Field(..., description="Categoría de impacto inferida de la captura visual")
    fusion_applied: bool = Field(..., description="Indica si la clasificación o prioridad fue alterada por fusión multimodal")
    fusion_note: str = Field(..., description="Explicación detallada del efecto de la evidencia visual sobre el ticket")
    ocr_text: Optional[str] = Field(default=None, description="Texto extraído mediante el pipeline de visión y OCR de Semana 09")
    umbral_otsu: Optional[float] = Field(default=None, description="Umbral calculado por Otsu en Semana 09")
    regiones_detectadas: Optional[int] = Field(default=None, description="Número de regiones conectadas detectadas")
    motor_usado: Optional[str] = Field(default=None, description="Motor o pipeline usado (ej: 'semana08_mlp', 'semana09_vision_ocr', o 'hibrido_s08_s09')")


class VisionPipelineResponse(BaseModel):
    """Diagnóstico técnico generado por el pipeline de visión por computador y OCR (Semana 09)."""

    status: str = Field(default="success", description="Estado de la ejecución del pipeline")
    origen: str = Field(default="vision", description="Origen de los datos procesados")
    dimensiones: List[int] = Field(..., description="Dimensiones de la imagen en escala de grises [alto, ancho]")
    umbral_otsu: float = Field(..., description="Umbral de segmentación calculado por Otsu")
    pixeles_canny_por_sigma: Optional[Dict[str, int]] = Field(
        default=None, description="Píxeles de contorno detectados para cada sigma en Canny"
    )
    regiones_detectadas: int = Field(..., description="Número de regiones conexas detectadas")
    texto_extraido: str = Field(default="", description="Texto extraído mediante OCR sobre la máscara")
    categoria_sugerida: str = Field(..., description="Categoría de soporte TI inferida a partir de la imagen")
    artifact_url: str = Field(..., description="URL del artefacto visual cuádruple generado (Canny, Otsu, Regiones)")
    binarized_image_url: str = Field(..., description="URL de la imagen binarizada con Otsu")
    image_url: str = Field(..., description="URL de la captura original guardada")
    url_artefacto: Optional[str] = Field(None, description="Alias para URL del artefacto")
    url_binarizada: Optional[str] = Field(None, description="Alias para URL de la imagen binarizada")


class TicketResponse(BaseModel):
    """Respuesta unificada que integra los motores IA del sistema (S02 a S05, S08 y S09)."""

    ticket: Dict[str, Any] = Field(..., description="Datos originales de la solicitud")
    classification: ClassificationResult = Field(..., description="Resultado de clasificación y SLA")
    astar_route: AStarRoute = Field(..., description="Ruta de resolución calculada por A*")
    rag_sop: RagSop = Field(..., description="Procedimiento estándar y precauciones RAG")
    visual_analysis: Optional[VisualAnalysis] = Field(
        default=None,
        description="Resultado del análisis multimodal de capturas de pantalla (Semana 08)",
    )

    # Campos complementarios para máxima interoperabilidad con clientes web
    category: Optional[str] = None
    priority: Optional[str] = None
    confidence_score: Optional[float] = None
    sla_minutes: Optional[str] = None
    estimated_resolution_time: Optional[str] = None
    lexical_evidence: Optional[List[str]] = None
    clase: Optional[str] = None
    evidencia: Optional[str] = None
    similitud: Optional[float] = None
    reglas: Optional[List[str]] = None
    astar: Optional[Dict[str, Any]] = None
    rag: Optional[Dict[str, Any]] = None
    assigned_to: Optional[str] = Field(
        default=None,
        description="Especialista o equipo de soporte asignado para la resolución",
    )


class TemplateItem(BaseModel):
    """Plantilla de ticket predefinida para pruebas de incidentes comunes de TI."""

    id: str = Field(..., description="Identificador único de la plantilla")
    subject: str = Field(..., description="Asunto representativo del incidente")
    description: str = Field(..., description="Descripción detallada del incidente")
    category: str = Field(..., description="Categoría predeterminada")
    priority: str = Field(..., description="Prioridad predeterminada")


class HealthResponse(BaseModel):
    """Respuesta del chequeo de salud y estado de los motores IA."""

    status: str = Field(..., description="Estado general de la API")
    version: str = Field(..., description="Versión de la API")
    engines: Dict[str, str] = Field(..., description="Módulos y motores IA activos")
    timestamp: str = Field(..., description="Marca de tiempo en formato ISO")


class KnowledgeManualItem(BaseModel):
    """Representación de un manual o procedimiento operativo de la base de conocimiento (SOP)."""

    id: Union[int, str] = Field(..., description="Identificador único del manual")
    code: str = Field(..., description="Código del runbook o manual (ej. SOP-KB-001)")
    title: str = Field(..., description="Título o descripción resumida del manual")
    content: str = Field(..., description="Contenido procedimental completo del manual")
    precautions: Optional[str] = Field(None, description="Precauciones operativas críticas")
    category: Optional[str] = Field(None, description="Categoría asociada al manual")
    source: str = Field(..., description="Origen de los datos ('PostgreSQL 18' o 'data/base_conocimiento.txt')")


class KnowledgeManualsResponse(BaseModel):
    """Respuesta del catálogo de manuales de la base de conocimiento."""

    total: int = Field(..., description="Total de manuales que coinciden con los criterios de búsqueda")
    count: int = Field(..., description="Número de manuales devueltos en la página actual")
    query: Optional[str] = Field(None, description="Término de búsqueda aplicado si hubo filtro")
    source: str = Field(..., description="Origen principal de la base de conocimiento")
    manuals: List[KnowledgeManualItem] = Field(..., description="Lista de manuales recuperados")


# Aliases para mantener compatibilidad con clientes y pruebas
HealthCheckResponse = HealthResponse
TicketTemplate = TemplateItem
ManualItem = KnowledgeManualItem
ManualsResponse = KnowledgeManualsResponse


class TicketUsuarioCreate(BaseModel):
    """Datos requeridos para que un usuario registre un ticket de soporte."""

    titulo: str = Field(..., min_length=1, description="Título o resumen del incidente reportado")
    descripcion: str = Field(..., min_length=1, description="Descripción detallada del incidente reportado")
    imagen_url: Optional[str] = Field(None, description="URL o ruta de imagen o captura de pantalla adjunta")


class TicketUsuarioUpdate(BaseModel):
    """Campos permitidos para que el usuario actualice la información de su ticket."""

    titulo: Optional[str] = Field(None, min_length=1, description="Título actualizado")
    descripcion: Optional[str] = Field(None, min_length=1, description="Descripción actualizada")
    imagen_url: Optional[str] = Field(None, description="URL de imagen actualizada")


class TicketTecnicoUpdate(BaseModel):
    """Campos que el analista técnico modifica al gestionar o cerrar el ticket."""

    solucion_pasos: Optional[str] = Field(None, description="Pasos o solución documentada por el técnico")
    criticidad: Optional[str] = Field(None, description="Nivel de criticidad validado (CRÍTICA, ALTA, MEDIA, BAJA)")
    area_asignada: Optional[str] = Field(None, description="Área técnica asignada")
    es_incidente: Optional[bool] = Field(None, description="Determina si clasifica formalmente como incidente")
    estado: Optional[str] = Field(None, description="Estado operativo del ticket (Abierto, En Progreso, Resuelto, Cerrado)")


class BaseIaSuggestionFields(BaseModel):
    """Campos base de recomendación y diagnóstico generados por los motores de IA."""

    criticidad_sugerida: Optional[str] = Field(None, description="Criticidad recomendada por IA")
    area_sugerida: Optional[str] = Field(None, description="Área recomendada por IA")
    es_incidente_sugerido: Optional[bool] = Field(None, description="Predicción de IA sobre si es incidente")
    confianza: Optional[float] = Field(None, description="Nivel de certidumbre de la IA")
    pasos_solucion: Optional[List[str]] = Field(default_factory=list, description="Lista de pasos sugeridos por IA")
    analisis_causa: Optional[str] = Field(None, description="Diagnóstico de causa raíz inferido por IA")
    tiene_manual: Optional[bool] = Field(False, description="Indica si existe un manual SOP en base de conocimiento")
    manual_titulo: Optional[str] = Field(None, description="Título del manual SOP recuperado")
    manual_precauciones: Optional[str] = Field(None, description="Precauciones operativas críticas")
    manual_checklist: Optional[List[str]] = Field(default_factory=list, description="Checklist procedimental del SOP")
    manual_id: Optional[str] = Field(None, description="Identificador del manual SOP")
    visual_analysis: Optional[Union[VisualAnalysis, Dict[str, Any]]] = Field(
        default=None,
        description="Resultado del análisis multimodal de capturas de pantalla (Semana 08 y 09)",
    )


class TicketDetalleResponse(BaseIaSuggestionFields):
    """Modelo completo del ticket persistido en base de datos para la consola técnica y de usuario."""

    id: int = Field(..., description="Identificador único del ticket")
    numero_ticket: Optional[str] = Field(None, description="Código de ticket (ej. TCK-2026-00001)")
    titulo: str = Field(..., description="Título del ticket")
    descripcion: str = Field(..., description="Descripción detallada")
    imagen_url: Optional[str] = Field(None, description="Ruta o URL de la imagen de evidencia")
    solucion_pasos: Optional[str] = Field(None, description="Solución registrada por el técnico")
    criticidad: Optional[str] = Field(None, description="Criticidad asignada")
    area_asignada: Optional[str] = Field(None, description="Área o equipo técnico asignado")
    es_incidente: Optional[bool] = Field(None, description="Indica si es un incidente")
    estado: str = Field(default="Abierto", description="Estado actual del ticket")
    sugerencia_ia: Optional[Union[Dict[str, Any], Any]] = Field(None, description="Payload JSON con recomendaciones de IA")
    created_at: Optional[str] = Field(None, description="Fecha y hora de creación")
    updated_at: Optional[str] = Field(None, description="Fecha y hora de última actualización")


class TicketGuiaIaResponse(BaseIaSuggestionFields):
    """Guía técnica diagnóstica generada por los motores de IA para orientar al analista de soporte."""

    criticidad_sugerida: str = Field(..., description="Criticidad sugerida por IA (CRÍTICA, ALTA, MEDIA, BAJA)")
    area_sugerida: str = Field(..., description="Área o categoría técnica sugerida por IA")
    es_incidente_sugerido: bool = Field(..., description="Determina si la IA clasifica el reporte como incidente")
    confianza: float = Field(..., description="Puntaje de confianza de la inferencia (0.0 a 1.0)")
    analisis_causa: str = Field(..., description="Explicación del análisis causal o evidencia léxica")
    tiene_manual: bool = Field(..., description="Indica si se recuperó un manual SOP en la base procedimental")


# Esquemas para el módulo de monitoreo y telemetría de equipos TI (Semana 07)

class MonitoreoRequest(BaseModel):
    """Muestra de telemetría enviada por un equipo para evaluar su salud operativa (Semana 07)."""

    equipo_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único del equipo monitoreado",
        examples=["PC-DIRECCION-01", "WS-DISENO-CAD-03", "SRV-BASE-DATOS-02"],
    )
    temperatura_cpu_c: float = Field(
        ...,
        description="Temperatura térmica del procesador en grados Celsius (°C)",
        examples=[72.0],
    )
    carga_servidor_pct: float = Field(
        ...,
        description="Uso de recursos (fracción 0.0 a 1.0 o porcentaje 0 a 100)",
        examples=[0.85],
    )
    tasa_errores_min: float = Field(
        ...,
        description="Tasa de errores registrados por minuto",
        examples=[3.0],
    )
    secuencia_eventos: str = Field(
        default="0000",
        description="Cadena de eventos temporales binarios ('0' y '1')",
        examples=["1101"],
    )
    crear_ticket_si_falla: bool = Field(
        default=True,
        description="Indica si debe generarse y persistirse un ticket de soporte cuando el equipo no está sano",
    )

    @field_validator("carga_servidor_pct", mode="before")
    @classmethod
    def normalize_carga(cls, v: Any) -> float:
        val = float(v)
        if val > 1.0:
            return round(val / 100.0, 4)
        return val


class MonitoreoResponse(BaseModel):
    """Evaluación integral de salud del equipo combinando distancia euclidiana, reglas lógicas y autómata DFA."""

    equipo_id: str = Field(..., description="Identificador del equipo monitoreado")
    telemetria: Dict[str, float] = Field(
        ...,
        description="Telemetría observada con temperatura_cpu_c, carga_servidor_pct y tasa_errores_min",
    )
    distancia_sla: float = Field(
        ...,
        description="Distancia euclidiana respecto al baseline normal de SLA (redondeada a 3 decimales)",
    )
    umbral_distancia_alerta: float = Field(
        default=1.5,
        description="Umbral numérico de distancia a partir del cual se dispara alerta de SLA",
    )
    distancia_alerta: bool = Field(
        ...,
        description="Indica si la distancia euclidiana supera el umbral de alerta (distancia > 1.5)",
    )
    hechos_simbolicos: List[str] = Field(
        default_factory=list,
        description="Hechos lógicos discretizados a partir de los umbrales de métricas",
    )
    diagnosticos_simbolicos: List[str] = Field(
        default_factory=list,
        description="Diagnósticos derivados por el motor de reglas de inferencia simbólica",
    )
    alerta_automata_01: bool = Field(
        ...,
        description="Indica si el autómata finito determinista (DFA) detectó la secuencia de falla que termina en '01'",
    )
    secuencia_analizada: str = Field(
        ...,
        description="Secuencia de logs temporales analizada por el autómata",
    )
    esta_sano: bool = Field(
        ...,
        description="Estado integral de salud del equipo (True si está dentro de SLA, sin diagnósticos ni alerta DFA)",
    )
    ticket_generado: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Ticket de soporte generado y persistido si el equipo no está sano",
    )


class MonitoreoBaselineResponse(BaseModel):
    """Configuración del baseline de SLA, umbrales de discretización y catálogo de reglas simbólicas."""

    baseline_referencia: Dict[str, float] = Field(
        ...,
        description="Métricas normales de referencia del SLA",
    )
    umbral_distancia_alerta: float = Field(
        ...,
        description="Umbral de distancia euclidiana para alerta de SLA (1.5)",
    )
    umbrales_simbolicos: Dict[str, float] = Field(
        ...,
        description="Umbrales de discretización para temperatura, carga y tasa de errores",
    )
    reglas_simbolicas: List[Dict[str, Any]] = Field(
        ...,
        description="Catálogo de reglas de inferencia simbólica (premisas -> conclusión)",
    )
    automata_alerta_patron: str = Field(
        ...,
        description="Patrón de alerta reconocido por el autómata DFA (ej. secuencias terminadas en '01')",
    )
    metricas_descripcion: Dict[str, str] = Field(
        ...,
        description="Descripción legible de cada métrica evaluada",
    )


class EquipoEjemploItem(BaseModel):
    """Caso de prueba o equipo de referencia para demostración rápida del monitoreo."""

    equipo_id: str = Field(..., description="Identificador del equipo")
    temperatura_cpu_c: float = Field(..., description="Temperatura de CPU en °C")
    carga_servidor_pct: float = Field(..., description="Carga del servidor (fracción 0.0 - 1.0)")
    tasa_errores_min: float = Field(..., description="Tasa de errores por minuto")
    secuencia_eventos: str = Field(..., description="Secuencia de eventos para el DFA")
    descripcion_esperada: Optional[str] = Field(None, description="Comportamiento o estado esperado")
    estado_esperado: Optional[str] = Field(None, description="Estado de salud previsto (SALUDABLE / NO SALUDABLE)")



