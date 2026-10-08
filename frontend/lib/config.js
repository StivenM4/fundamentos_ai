// URL base del backend FastAPI: toma la variable de entorno "BACKEND_URL" o cae por defecto al puerto 8000 en local
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
module.exports = { BACKEND_URL };
