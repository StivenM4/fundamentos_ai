// Valores nominales de referencia y umbrales de alerta para el monitoreo de telemetría.
// La inferencia matemática real corre en FastAPI ("backend/routers/monitoreo.py") y en "src/semana07_representaciones.py".
// Este archivo queda como fallback local para no romper vistas si el backend se cae.

// Métricas normales de operación segura (línea base del hardware)
const BASELINE_REFERENCIA = {
  temperatura_cpu_c: 70.0,
  carga_servidor_pct: 0.80,
  tasa_errores_min: 2.0
};

// Límites donde ya salta alarma por calor, saturación o ráfaga de errores
const UMBRALES = {
  temperatura_alta: 71.0,
  carga_alta: 0.82,
  errores_presentes: 2.5,
  distancia_alerta: 1.5
};

// Nombres de máquinas de prueba para simular incidentes en los puestos de trabajo
const EQUIPOS_CATALOGO = [
  'PC-DIRECCION-01',
  'WS-DISENO-CAD-03',
  'SRV-BASE-DATOS-02'
];

module.exports = {
  BASELINE_REFERENCIA,
  UMBRALES,
  EQUIPOS_CATALOGO
};
