const express = require('express');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const multer = require('multer');
const { marked } = require('marked');
const { SEMANAS_CATALOG } = require('./catalog');

const PORT = parseInt(process.env.PORT, 10) || 3000;
const { BACKEND_URL } = require('./lib/config');

const { createDiskStorage, imageFileFilter } = require('./lib/upload-helper');
const { normalizeBackendResponse } = require('./lib/ticket-formatter');

// Carpeta local "public/uploads" para guardar capturas de pantalla y evidencias adjuntas a los tickets
const uploadsDir = path.join(__dirname, 'public', 'uploads');
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir, { recursive: true });

const upload = multer({
  storage: createDiskStorage(uploadsDir),
  limits: { fileSize: 15 * 1024 * 1024 },
  fileFilter: imageFileFilter
});

// Middleware con Multer: recibe la imagen adjunta, tolera si no viene archivo y deja la referencia en "req.file"
const uploadMiddleware = (req, res, next) => {
  upload.any()(req, res, (err) => {
    if (err) console.warn('[Multer Warning]', err.message);
    if (req.files && req.files.length > 0) req.file = req.files[0];
    next();
  });
};

// Revisa si la base de datos "PostgreSQL" responde en FastAPI; si no hay conexión, hace fallback a los archivos locales en "data/"
async function getDataSource() {
  try {
    const { data } = await axios.get(`${BACKEND_URL}/api/models/status`, { timeout: 2000 });
    if (data?.database?.connected) return { type: 'database', name: 'PostgreSQL 18 (SoporteAIBD)', connected: true };
  } catch (_) {}
  const hasLocal = fs.existsSync(path.join(__dirname, '..', 'data', 'tickets_soporte.csv'));
  return {
    type: 'files',
    name: hasLocal ? 'data/ (tickets_soporte.csv, base_conocimiento.txt)' : 'Archivos data/ no disponibles',
    connected: false
  };
}

// Configuración base de Express: parsers de JSON, formularios, estáticos y plantillas "EJS"
const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(path.join(__dirname, '..', 'uploads')), express.static(path.join(__dirname, 'public', 'uploads')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use((req, res, next) => { res.locals.currentPath = req.path; next(); });

// Enrutadores modulares por rol: portal de usuario, consola técnica de TI y módulo de telemetría
app.use('/portal-usuario', require('./routes/portal_usuario'));
app.use('/soporte-ti', require('./routes/soporte_ti'));
app.use('/monitoreo', require('./routes/monitoreo'));

// Vista de inicio: renderiza la interfaz principal del clasificador y asistente de soporte
app.get('/', (req, res) => res.render('index', { ticket: null, result: null, error: null, backendUrl: BACKEND_URL }));

// Carga y renderiza en HTML los informes Markdown de cada entrega semanal guardados en "reports/"
app.get('/semanas/:semanaId', async (req, res) => {
  const { semanaId } = req.params;
  const semana = SEMANAS_CATALOG[semanaId];
  if (!semana) return res.status(404).render('stub', { moduleTitle: 'Módulo No Encontrado', moduleBadge: 'Error 404', moduleDesc: `Identificador '${semanaId}' no válido.` });
  const reportPath = path.join(__dirname, '..', 'reports', `${semanaId}.md`);
  if (!fs.existsSync(reportPath)) return res.status(404).render('stub', { moduleTitle: `Semana ${semana.number}: ${semana.title}`, moduleBadge: 'Error 404', moduleDesc: `El archivo ${semanaId}.md no se encontró.` });
  try {
    const content = await fs.promises.readFile(reportPath, 'utf8');
    const htmlContent = marked && typeof marked.parse === 'function' ? marked.parse(content) : `<pre>${content}</pre>`;
    res.render('semana', { metadata: semana, htmlContent, prevSemana: semana.prev ? SEMANAS_CATALOG[semana.prev] : null, nextSemana: semana.next ? SEMANAS_CATALOG[semana.next] : null });
  } catch (err) {
    res.status(500).render('stub', { moduleTitle: 'Error en Documentación', moduleBadge: 'Error 500', moduleDesc: err.message });
  }
});

// Endpoint "/health" para verificar el estado del servidor web y saber de dónde se leen los datos ("PostgreSQL" o "data/")
app.get('/health', async (req, res) => {
  const ds = await getDataSource();
  res.json({
    status: 'ok',
    engine: 'express',
    uptime: process.uptime(),
    port: PORT,
    backendUrl: BACKEND_URL,
    dataSource: ds.name,
    database_connected: ds.connected,
    engines: ['NLP / XAI (S03)', 'Heurística A* (S04)', 'RAG (S05)', 'Visión MLP (S08)', 'Visión OCR (S09)'],
    timestamp: new Date().toISOString()
  });
});

// Consulta a FastAPI las plantillas de casos comunes para llenar el selector rápido de la interfaz
app.get('/api/tickets/templates', async (req, res) => {
  try {
    const { data } = await axios.get(`${BACKEND_URL}/api/tickets/templates`, { timeout: 4000 });
    return res.json(data);
  } catch (err) {
    return res.status(502).json({ error: `Error conectando con FastAPI en ${BACKEND_URL}: ${err.message}` });
  }
});

// Dispara el reentrenamiento del clasificador de imágenes "MLP" directamente en el backend
app.post('/api/models/train-vision', async (req, res) => {
  try {
    const { data } = await axios.post(`${BACKEND_URL}/api/models/train-vision`, {}, { timeout: 20000 });
    return res.json(data);
  } catch (err) {
    return res.status(502).json({ error: `Error conectando con FastAPI en ${BACKEND_URL}: ${err.message}` });
  }
});

// Procesa el ticket enviado: si viene imagen la manda como "multipart/form-data", si no como "JSON", y normaliza la respuesta
app.post('/analyze', uploadMiddleware, async (req, res) => {
  const subject = (req.body.subject || '').trim();
  const description = (req.body.description || '').trim();
  const file = req.file;
  const isAjax = req.xhr || (req.headers.accept && req.headers.accept.includes('application/json')) || req.is('json');

  if (!subject || !description) {
    const errorMsg = 'El asunto y la descripción detallada del ticket son obligatorios.';
    if (isAjax) return res.status(400).json({ error: errorMsg });
    return res.render('index', { ticket: { subject, description }, result: null, error: errorMsg, backendUrl: BACKEND_URL });
  }

  try {
    let backendRes;
    if (file) {
      const formData = new FormData();
      formData.append('subject', subject);
      formData.append('description', description);
      const fileBuffer = await fs.promises.readFile(file.path);
      formData.append('image', new Blob([fileBuffer], { type: file.mimetype || 'image/png' }), file.originalname);
      try {
        backendRes = await axios.post(`${BACKEND_URL}/api/tickets/analyze-multipart`, formData, { timeout: 10000 });
      } catch (_) {
        backendRes = await axios.post(`${BACKEND_URL}/api/tickets/analyze`, formData, { timeout: 10000 });
      }
    } else {
      backendRes = await axios.post(`${BACKEND_URL}/api/tickets/analyze`, { subject, description }, { timeout: 10000, headers: { 'Content-Type': 'application/json' } });
    }

    const finalResult = normalizeBackendResponse(backendRes.data, subject, description, file);
    if (isAjax) return res.json({ success: true, ticket: { subject, description }, result: finalResult });
    return res.render('index', { ticket: { subject, description }, result: finalResult, error: null, backendUrl: BACKEND_URL });
  } catch (err) {
    const detail = err.response?.data?.detail;
    const msg = typeof detail === 'string' ? detail : (err.response?.data?.error || err.message);
    const errorMsg = `No se pudo conectar con la API backend en ${BACKEND_URL}: ${msg}`;
    if (isAjax) return res.status(502).json({ error: errorMsg });
    return res.render('index', { ticket: { subject, description }, result: null, error: errorMsg, backendUrl: BACKEND_URL });
  }
});

// Levanta el servidor HTTP en el puerto configurado (por defecto 3000)
app.listen(PORT, () => {
  console.log(`[ServiceDesk AI] Servidor Express corriendo en http://localhost:${PORT}`);
  console.log(`[ServiceDesk AI] Backend FastAPI configurado en ${BACKEND_URL}`);
});
