// Enrutador de telemetría y monitoreo de equipos en "/monitoreo".
// Esta vista actúa como capa delgada de presentación: recibe las lecturas de los puestos y le pasa los datos a FastAPI.
// Si el backend no contesta, usa los cálculos de respaldo en local para que la interfaz no se bloquee.

const express = require('express');
const router = express.Router();
const axios = require('axios');
const { BACKEND_URL } = require('../lib/config');

// Valores base de hardware y umbrales por si FastAPI no responde o el servicio está apagado
const FALLBACK_BASELINE = {
  temperatura_cpu_c: 70.0,
  carga_servidor_pct: 0.80,
  tasa_errores_min: 2.0
};

const FALLBACK_UMBRALES = {
  temperatura_alta: 71.0,
  carga_alta: 0.82,
  errores_presentes: 2.5,
  distancia_alerta: 1.5
};

const FALLBACK_EQUIPOS = [
  'PC-DIRECCION-01',
  'WS-DISENO-CAD-03',
  'SRV-BASE-DATOS-02'
];

// GET "/monitoreo": trae la línea base y la lista de equipos registrados desde el backend para pintar la consola
router.get('/', async (req, res) => {
  let baseline = { ...FALLBACK_BASELINE };
  let umbrales = { ...FALLBACK_UMBRALES };
  let equiposEjemplo = [...FALLBACK_EQUIPOS];

  try {
    const [baseRes, eqRes] = await Promise.allSettled([
      axios.get(`${BACKEND_URL}/api/monitoreo/baseline`, { timeout: 3000 }),
      axios.get(`${BACKEND_URL}/api/monitoreo/equipos-ejemplo`, { timeout: 3000 })
    ]);

    if (baseRes.status === 'fulfilled' && baseRes.value?.data) {
      const data = baseRes.value.data;
      if (data.baseline_referencia) baseline = data.baseline_referencia;
      if (data.umbrales_simbolicos) {
        umbrales = {
          ...data.umbrales_simbolicos,
          distancia_alerta: data.umbral_distancia_alerta || 1.5
        };
      }
    }

    if (eqRes.status === 'fulfilled' && Array.isArray(eqRes.value?.data)) {
      equiposEjemplo = eqRes.value.data.map(e => e.equipo_id || e);
    }
  } catch (err) {
    console.warn('[Monitoreo] Fallback local por error en FastAPI:', err.message);
  }

  res.render('monitoreo', {
    pageTitle: 'Monitoreo de Equipos - Telemetría y SLA',
    currentPath: '/monitoreo',
    backendUrl: BACKEND_URL,
    baseline,
    umbrales,
    equiposEjemplo
  });
});

// POST "/monitoreo/api/evaluar": reenvía métricas de temperatura, carga y logs a FastAPI para clasificar desvíos de SLA
router.post('/api/evaluar', async (req, res) => {
  const {
    equipo_id = 'PC-DIRECCION-01',
    temperatura_cpu_c,
    carga_servidor_pct,
    tasa_errores_min,
    secuencia_logs = '1100'
  } = req.body;

  const numTemp = parseFloat(temperatura_cpu_c);
  const numCarga = parseFloat(carga_servidor_pct);
  const numErrores = parseFloat(tasa_errores_min);
  const secLimpia = String(secuencia_logs || '').trim();
  const eqId = String(equipo_id || 'PC-DIRECCION-01').trim();

  const payload = {
    equipo_id: eqId,
    temperatura_cpu_c: numTemp,
    carga_servidor_pct: numCarga > 1.0 ? numCarga / 100.0 : numCarga,
    tasa_errores_min: numErrores,
    secuencia_eventos: secLimpia,
    secuencia_logs: secLimpia,
    crear_ticket_si_falla: true
  };

  try {
    const resp = await axios.post(`${BACKEND_URL}/api/monitoreo/evaluar`, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 5000
    });

    if (resp.data && typeof resp.data.esta_sano !== 'undefined') {
      const data = resp.data;
      data.ticket = data.ticket_generado || data.ticket || null;
      data.hechos_discretizados = data.hechos_simbolicos || data.hechos_discretizados || [];
      data.secuencia_analizada = data.secuencia_analizada || secLimpia;
      data.diagnostico_principal = (data.diagnosticos_simbolicos && data.diagnosticos_simbolicos.length > 0)
        ? data.diagnosticos_simbolicos.join(', ')
        : (data.esta_sano ? 'Operación Nominal (SLA Cumplido)' : 'Desvío de Telemetría SLA');
      data.prioridad = data.esta_sano ? 'SALUDABLE' : (data.distancia_sla > 3.0 ? 'CRÍTICA' : 'ALTA');

      return res.json({
        success: true,
        from_backend: true,
        resultado: data
      });
    }
  } catch (err) {
    console.warn('[Monitoreo] FastAPI no disponible para evaluar telemetría:', err.message);
  }

  // Cálculo local de respaldo: evalúa distancia euclidiana y secuencia de autómata binario si el backend está caído
  const dist = Math.sqrt(
    Math.pow(numTemp - 70.0, 2) +
    Math.pow((numCarga > 1.0 ? numCarga / 100.0 : numCarga) - 0.80, 2) +
    Math.pow(numErrores - 2.0, 2)
  );
  const alertaAutomata = secLimpia.endsWith('01');
  const estaSano = dist <= 1.5 && !alertaAutomata && numTemp < 71.0;
  const diagnosticos = [];
  if (numTemp >= 71.0 && numCarga >= 82.0) diagnosticos.push('riesgo_termico');
  if (numCarga >= 82.0 && numErrores >= 2.5) diagnosticos.push('posible_cuello_botella');
  if (numTemp >= 71.0 && numErrores >= 2.5) diagnosticos.push('falla_potencial_hardware');

  return res.json({
    success: true,
    from_backend: false,
    resultado: {
      equipo_id: eqId,
      telemetria: { temperatura_cpu_c: numTemp, carga_servidor_pct: numCarga, tasa_errores_min: numErrores },
      distancia_sla: parseFloat(dist.toFixed(3)),
      distancia_alerta: dist > 1.5,
      hechos_discretizados: [
        ...(numTemp >= 71.0 ? ['temperatura_alta'] : []),
        ...(numCarga >= 82.0 ? ['carga_alta'] : []),
        ...(numErrores >= 2.5 ? ['errores_presentes'] : [])
      ],
      diagnosticos_simbolicos: diagnosticos,
      diagnostico_principal: diagnosticos.length > 0 ? diagnosticos.join(', ') : (estaSano ? 'Operación Nominal (SLA Cumplido)' : 'Desvío de Telemetría SLA'),
      alerta_automata_01: alertaAutomata,
      secuencia_analizada: secLimpia,
      esta_sano: estaSano,
      prioridad: estaSano ? 'SALUDABLE' : 'ALTA',
      ticket: estaSano ? null : {
        id: `TCK-${Math.floor(10000 + Math.random() * 89999)}`,
        asunto: `Alerta Telemetría S07 [${eqId}]`,
        descripcion: `Telemetría fuera de SLA en ${eqId}. Temp: ${numTemp}°C, Carga: ${numCarga}%, Errores: ${numErrores} err/min.`
      }
    }
  });
});

// GET "/monitoreo/api/random": genera lecturas aleatorias (normales o con falla) para hacer pruebas rápidas en la mesa de ayuda
router.get('/api/random', async (req, res) => {
  try {
    const resp = await axios.get(`${BACKEND_URL}/api/monitoreo/random`, {
      params: req.query,
      timeout: 3000
    });
    return res.json(resp.data);
  } catch (_) {
    const tipo = req.query.tipo || (Math.random() > 0.4 ? 'anomalo' : 'saludable');
    const equipo = FALLBACK_EQUIPOS[Math.floor(Math.random() * FALLBACK_EQUIPOS.length)];

    let temp, carga, errores, secuencia;
    if (tipo === 'saludable') {
      temp = parseFloat((69.5 + Math.random() * 1.3).toFixed(1));
      carga = parseFloat((77.0 + Math.random() * 4.0).toFixed(1));
      errores = parseFloat((1.6 + Math.random() * 0.7).toFixed(1));
      secuencia = ['1100', '1010', '0000', '1110', '1000'][Math.floor(Math.random() * 5)];
    } else {
      temp = parseFloat((71.5 + Math.random() * 20.0).toFixed(1));
      carga = parseFloat((82.5 + Math.random() * 16.0).toFixed(1));
      errores = parseFloat((2.6 + Math.random() * 5.0).toFixed(1));
      secuencia = ['1101', '0001', '01', '1001', '0101'][Math.floor(Math.random() * 5)];
    }

    return res.json({
      success: true,
      tipo,
      equipo_id: equipo,
      temperatura_cpu_c: temp,
      carga_servidor_pct: carga,
      tasa_errores_min: errores,
      secuencia_logs: secuencia
    });
  }
});

// POST "/monitoreo/api/evaluar-metrica": valida en tiempo real un solo campo (temperatura, carga, errores o cadena de logs)
router.post('/api/evaluar-metrica', (req, res) => {
  const { metrica, valor } = req.body;
  const numVal = parseFloat(valor);

  let alerta = false;
  let detalle = '';
  let hecho = null;
  let umbral = null;

  switch (metrica) {
    case 'temperatura':
      umbral = FALLBACK_UMBRALES.temperatura_alta;
      alerta = numVal >= umbral;
      hecho = alerta ? 'temperatura_alta' : null;
      detalle = alerta
        ? `ALERTA TÉRMICA: ${numVal}°C supera el umbral normativo (>= ${umbral}°C). Potencial riesgo térmico.`
        : `NORMAL: ${numVal}°C se encuentra dentro del rango operativo seguro (< ${umbral}°C).`;
      break;

    case 'carga':
      umbral = FALLBACK_UMBRALES.carga_alta * 100;
      const cargaPct = numVal > 1.0 ? numVal : numVal * 100;
      alerta = cargaPct >= umbral;
      hecho = alerta ? 'carga_alta' : null;
      detalle = alerta
        ? `SATURACIÓN DE RECURSOS: ${cargaPct.toFixed(1)}% supera el límite (>= ${umbral}%).`
        : `NORMAL: ${cargaPct.toFixed(1)}% está por debajo del umbral de sobrecarga (< ${umbral}%).`;
      break;

    case 'errores':
      umbral = FALLBACK_UMBRALES.errores_presentes;
      alerta = numVal >= umbral;
      hecho = alerta ? 'errores_presentes' : null;
      detalle = alerta
        ? `TASA ANÓMALA: ${numVal} err/min excede el límite permitido (>= ${umbral} err/min).`
        : `NORMAL: ${numVal} err/min dentro del margen de tolerancia (< ${umbral} err/min).`;
      break;

    case 'automata':
      const secStr = String(valor || '').trim();
      alerta = secStr.endsWith('01');
      detalle = alerta
        ? `PATRÓN CRÍTICO DETECTADO: La secuencia '${secStr}' culmina con el patrón de riesgo '01' (estado q2).`
        : `SECUENCIA SEGURA: La cadena '${secStr}' no activa el estado terminal de alerta q2.`;
      break;

    default:
      return res.status(400).json({ success: false, error: `Métrica '${metrica}' no válida.` });
  }

  res.json({
    success: true,
    metrica,
    valor,
    alerta,
    hecho_generado: hecho,
    umbral,
    detalle
  });
});

module.exports = router;
