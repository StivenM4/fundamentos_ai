// Catálogo de entregas semanales para enlazar la documentación técnica en "reports/" con la vista de Express
const SEMANAS_CATALOG = {
  semana02: { id: 'semana02', number: '02', title: 'Fundamentos y Clasificación', subtitle: 'Clasificación supervisada multietiqueta de tickets TI', file: 'semana02.md', prev: null, next: 'semana03' },
  semana03: { id: 'semana03', number: '03', title: 'Taxonomía y Activadores', subtitle: 'Taxonomía léxica, reglas difusas y explicabilidad XAI', file: 'semana03.md', prev: 'semana02', next: 'semana04' },
  semana04: { id: 'semana04', number: '04', title: 'Búsqueda Heurística A*', subtitle: 'Resolución y mitigación óptima de incidentes de TI con A*', file: 'semana04.md', prev: 'semana03', next: 'semana05' },
  semana05: { id: 'semana05', number: '05', title: 'Sistema Híbrido RAG', subtitle: 'Recuperación procedural de Runbooks con TF-IDF y Similitud Coseno', file: 'semana05.md', prev: 'semana04', next: 'semana07' },
  semana07: { id: 'semana07', number: '07', title: 'Representaciones de Conocimiento', subtitle: 'Frames, esquemas semánticos y reglas de inferencia', file: 'semana07.md', prev: 'semana05', next: 'semana08' },
  semana08: { id: 'semana08', number: '08', title: 'Redes y Ontologías', subtitle: 'Ontología RDF, SPARQL y grafos de dependencia de infraestructura', file: 'semana08.md', prev: 'semana07', next: 'semana09' },
  semana09: { id: 'semana09', number: '09', title: 'Visión Computacional & OCR', subtitle: 'Detección de contornos Canny, segmentación Otsu y extracción OCR de errores TI', file: 'semana09.md', prev: 'semana08', next: null }
};

module.exports = { SEMANAS_CATALOG };
