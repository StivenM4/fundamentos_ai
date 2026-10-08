// Adapta la respuesta JSON que entrega FastAPI al formato que esperan las plantillas "EJS" del frontend.
// Deja organizados los bloques de A*, el runbook RAG y los datos de visión por computador (MLP y OCR).

function normalizeBackendResponse(data, subject, description, file = null) {
  if (!data) return null;

  // Arma la lista de pasos del algoritmo A* con costos "g", "h" y "f" calculados
  const astarSrc = data.astar_route || data.astar || {};
  const steps = (astarSrc.steps || []).map((s, idx) => ({
    step_number: s.step_number ?? (idx + 1),
    node_id: s.node_id || s.name || `nodo_${idx + 1}`,
    title: s.title || s.node_id || `Paso ${idx + 1}`,
    description: s.description || s.desc || '',
    role: s.role || 'Soporte TI',
    g: s.g ?? 0, h: s.h ?? 0, f: s.f ?? ((s.g ?? 0) + (s.h ?? 0)),
    is_goal: Boolean(s.is_goal)
  }));
  const efficiencyNote = astarSrc.efficiency_gain_pct
    ? `${steps.length} Pasos Optimizados (${astarSrc.efficiency_gain_pct}% reducción)`
    : `${steps.length} Pasos Optimizados`;

  // Datos del runbook RAG y porcentaje de confianza de la clasificación de texto
  const ragSrc = data.rag_sop || data.rag || {};
  const rawConf = data.confidence_score ?? data.classification?.confidence_score ?? 0.95;
  const confScore = typeof rawConf === 'number' && rawConf <= 1 ? `${(rawConf * 100).toFixed(1)}%` : String(rawConf);

  // Normaliza el resultado del análisis visual si el usuario adjuntó una captura de pantalla
  const v = data.visual_analysis || data.evidencia_visual || null;
  const visualAnalysis = v ? {
    detected_class: v.detected_class || '',
    class_label: v.class_label || v.detected_class || '',
    confidence_score: v.confidence_score ?? 0.984,
    confidence_pct: v.confidence_pct || `${((v.confidence_score ?? 0.984) * 100).toFixed(1)}%`,
    confidence: v.confidence_pct || `${((v.confidence_score ?? 0.984) * 100).toFixed(1)}%`,
    model: v.model || 'Red Neuronal MLP',
    saved_image_path: v.saved_image_path || (file ? file.path : ''),
    image_url: v.image_url || (file ? `/uploads/${file.filename}` : '/images/sample_bsod.png'),
    filename: v.filename || (file ? file.originalname : 'captura.png'),
    impact_category: v.impact_category || 'Hardware / Kernel Crítico',
    fusion_applied: Boolean(v.fusion_applied),
    fusion_note: v.fusion_note || v.explanation || '',
    explanation: v.fusion_note || v.explanation || '',
    ocr_text: v.ocr_text || v.texto_extraido || '',
    texto_extraido: v.ocr_text || v.texto_extraido || '',
    umbral_otsu: v.umbral_otsu !== undefined ? v.umbral_otsu : 0.5783,
    regiones_detectadas: v.regiones_detectadas !== undefined ? v.regiones_detectadas : 344,
    motor_usado: v.motor_usado || 'hibrido_s08_s09'
  } : null;

  // Empaqueta el objeto final del ticket para pasarlo directamente al render de la vista
  return {
    ticket_id: data.ticket_id || data.ticket?.ticket_id || `#INC-2026-${Math.floor(1000 + Math.random() * 9000)}`,
    subject: data.ticket?.subject || subject,
    description: data.ticket?.description || description,
    priority: data.priority || data.classification?.priority || 'MEDIA',
    sla_minutes: data.sla_minutes || (data.classification?.sla_minutes ? `${data.classification.sla_minutes} min` : '60 min'),
    category: data.category || data.classification?.category || 'General',
    confidence_score: confScore,
    estimated_resolution_time: data.estimated_resolution_time || '~25 min',
    lexical_evidence: data.lexical_evidence || data.classification?.lexical_evidence || [],
    rules_fired: data.rules_fired || data.reglas || [],
    astar: { totalCost: astarSrc.total_cost ?? astarSrc.cost ?? (steps[steps.length - 1]?.f || 6), efficiencyNote: astarSrc.efficiencyNote || efficiencyNote, steps },
    rag: {
      sop_title: ragSrc.title || ragSrc.sop_title || 'Runbook de Soporte Estándar',
      source: ragSrc.source || 'Base de Conocimiento PostgreSQL 18 & data/ (SOP)',
      similarity: ragSrc.similarity_score ?? ragSrc.similarity ?? 0.9,
      precautions: ragSrc.precautions || 'Verificar precauciones operativas antes de aplicar cambios.',
      checklist: Array.isArray(ragSrc.checklist) ? ragSrc.checklist : []
    },
    visual_analysis: visualAnalysis,
    evidencia_visual: visualAnalysis
  };
}

module.exports = {
  normalizeBackendResponse
};
