// Enrutador del portal de autoservicio para usuarios finales ("/portal-usuario").
// Permite radicar incidentes nuevos, editar reportes abiertos y revisar el historial de tickets guardados en PostgreSQL.
// Conecta con los endpoints de FastAPI ("/api/usuario/tickets" y "/api/tecnico/tickets").

const express = require('express');
const router = express.Router();
const axios = require('axios');
const multer = require('multer');
const { BACKEND_URL } = require('../lib/config');

const { memoryUpload } = require('../lib/upload-helper');

const uploadMiddleware = (req, res, next) => {
  memoryUpload.single('imagen')(req, res, (err) => {
    if (err) {
      req.fileValidationError = err.message;
    }
    next();
  });
};

// Trae los tickets desde FastAPI verificando que vengan con la URL de la imagen y los textos procesados por OCR
async function fetchTicketsFromBackend() {
  try {
    const response = await axios.get(`${BACKEND_URL}/api/tecnico/tickets`, { timeout: 4000 });
    if (Array.isArray(response.data)) {
      return response.data.map(t => {
        const desc = String(t.descripcion || '');
        const tieneOcr = Boolean(t.ocr_texto || desc.includes('[Evidencia OCR S09]') || desc.includes('[Evidencia Visual OCR S09]'));
        return {
          ...t,
          descripcion: t.descripcion,
          imagen_url: t.imagen_url,
          tiene_vision: Boolean(t.imagen_url || tieneOcr || t.tiene_vision)
        };
      });
    }
    return [];
  } catch (err) {
    console.warn(`[Portal Usuario] Backend FastAPI no disponible (${err.message}).`);
    return [];
  }
}

// GET "/portal-usuario": renderiza la bandeja de tickets del usuario o responde con JSON si la petición viene por "fetch" / AJAX
router.get('/', async (req, res) => {
  const isAjax = req.xhr || 
    (req.headers.accept && req.headers.accept.includes('application/json')) ||
    req.query.format === 'json';

  const tickets = await fetchTicketsFromBackend();

  if (isAjax) {
    return res.json({
      success: true,
      tickets: tickets
    });
  }

  let successMsg = null;
  if (req.query.msg === 'creado') {
    successMsg = 'Ticket registrado exitosamente en la base de datos.';
  } else if (req.query.msg === 'actualizado') {
    successMsg = 'Ticket actualizado exitosamente en la base de datos.';
  } else if (req.query.msg) {
    successMsg = req.query.msg;
  }

  res.render('portal_usuario', {
    pageTitle: 'Portal de Usuario - Mesa de Ayuda TI',
    currentPath: '/portal-usuario',
    tickets: tickets,
    error: req.query.error || null,
    success: successMsg
  });
});

// GET "/portal-usuario/tickets": entrega la lista de tickets en JSON para actualizar la tabla sin recargar toda la página
router.get('/tickets', async (req, res) => {
  try {
    const response = await axios.get(`${BACKEND_URL}/api/tecnico/tickets`, { timeout: 4000 });
    return res.json({
      success: true,
      tickets: response.data || []
    });
  } catch (err) {
    return res.status(502).json({
      success: false,
      error: `Error al consultar tickets en el servidor: ${err.message}`,
      tickets: []
    });
  }
});

// GET "/portal-usuario/ticket/:id": devuelve los datos de un ticket en JSON para cargar el formulario modal de edición
router.get('/ticket/:id', async (req, res) => {
  const { id } = req.params;
  try {
    const response = await axios.get(`${BACKEND_URL}/api/usuario/tickets/${id}`, { timeout: 4000 });
    return res.json({
      success: true,
      ticket: response.data
    });
  } catch (err) {
    const status = err.response?.status || 500;
    const detail = err.response?.data?.detail || err.message;
    return res.status(status).json({
      success: false,
      error: `Error al obtener el ticket ${id}: ${detail}`
    });
  }
});

// POST "/portal-usuario/enviar": recibe el formulario con título, detalle y pantallazo adjunto, y lo radica en FastAPI
router.post('/enviar', uploadMiddleware, async (req, res) => {
  const isAjax = req.xhr || 
    (req.headers.accept && req.headers.accept.includes('application/json')) ||
    req.is('json');

  if (req.fileValidationError) {
    if (isAjax) return res.status(400).json({ success: false, error: req.fileValidationError });
    return res.redirect(`/portal-usuario?error=${encodeURIComponent(req.fileValidationError)}`);
  }

  const titulo = (req.body.titulo || '').trim();
  const descripcion = (req.body.descripcion || '').trim();

  if (!titulo || !descripcion) {
    const msg = 'Los campos título y descripción son obligatorios.';
    if (isAjax) return res.status(400).json({ success: false, error: msg });
    return res.redirect(`/portal-usuario?error=${encodeURIComponent(msg)}`);
  }

  let imagenUrl = null;
  let backendRes = null;

  if (req.file) {
    try {
      const blob = new Blob([req.file.buffer], { type: req.file.mimetype || 'image/png' });
      const formData = new FormData();
      formData.append('titulo', titulo);
      formData.append('descripcion', descripcion);
      formData.append('imagen', blob, req.file.originalname || 'evidencia.png');

      backendRes = await axios.post(`${BACKEND_URL}/api/usuario/tickets`, formData, {
        timeout: 10000
      });
    } catch (multipartErr) {
      console.warn(`[Portal Usuario] Envío multipart a FastAPI falló (${multipartErr.message}), usando fallback JSON...`);
      imagenUrl = `/uploads/${req.file.originalname || 'evidencia.png'}`;
    }
  } else if (req.body.imagen_url) {
    const rawUrl = String(req.body.imagen_url).trim();
    // Asegura que la ruta de la imagen apunte a la carpeta local "/uploads/" o venga por una URL web válida
    if (rawUrl.startsWith('/uploads/') || rawUrl.startsWith('http://') || rawUrl.startsWith('https://')) {
      imagenUrl = rawUrl;
    }
  }

  if (!backendRes) {
    try {
      const payload = {
        titulo: titulo,
        descripcion: descripcion,
        imagen_url: imagenUrl
      };

      backendRes = await axios.post(`${BACKEND_URL}/api/usuario/tickets`, payload, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 5000
      });
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      const errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail);

      if (isAjax) {
        return res.status(err.response?.status || 500).json({
          success: false,
          error: `Error al guardar ticket: ${errorMsg}`
        });
      }

      return res.redirect(`/portal-usuario?error=${encodeURIComponent('Error al guardar ticket: ' + errorMsg)}`);
    }
  }

  if (isAjax) {
    return res.status(201).json({
      success: true,
      message: 'Ticket registrado exitosamente en la base de datos.',
      ticket: backendRes.data
    });
  }

  return res.redirect('/portal-usuario?msg=creado');
});

// POST "/portal-usuario/editar/:id": procesa la actualización de texto o reemplazo de captura de pantalla para un ticket abierto
router.post('/editar/:id', uploadMiddleware, async (req, res) => {
  const { id } = req.params;
  const isAjax = req.xhr || 
    (req.headers.accept && req.headers.accept.includes('application/json')) ||
    req.is('json');

  if (req.fileValidationError) {
    if (isAjax) return res.status(400).json({ success: false, error: req.fileValidationError });
    return res.redirect(`/portal-usuario?error=${encodeURIComponent(req.fileValidationError)}`);
  }

  const titulo = (req.body.titulo || '').trim();
  const descripcion = (req.body.descripcion || '').trim();

  if (!titulo || !descripcion) {
    const msg = 'Los campos título y descripción son obligatorios para actualizar el ticket.';
    if (isAjax) return res.status(400).json({ success: false, error: msg });
    return res.redirect(`/portal-usuario?error=${encodeURIComponent(msg)}`);
  }

  let imagenUrl = undefined;
  let backendRes = null;

  if (req.file) {
    try {
      const blob = new Blob([req.file.buffer], { type: req.file.mimetype || 'image/png' });
      const formData = new FormData();
      formData.append('titulo', titulo);
      formData.append('descripcion', descripcion);
      formData.append('imagen', blob, req.file.originalname || 'evidencia.png');

      backendRes = await axios.put(`${BACKEND_URL}/api/usuario/tickets/${id}`, formData, {
        timeout: 10000
      });
    } catch (multipartErr) {
      console.warn(`[Portal Usuario] Envío multipart en edición falló (${multipartErr.message}), usando fallback JSON...`);
      imagenUrl = `/uploads/${req.file.originalname || 'evidencia.png'}`;
    }
  } else if (req.body.imagen_url) {
    const rawUrl = String(req.body.imagen_url).trim();
    // Asegura que la ruta de la imagen apunte a la carpeta local "/uploads/" o venga por una URL web válida
    if (rawUrl.startsWith('/uploads/') || rawUrl.startsWith('http://') || rawUrl.startsWith('https://')) {
      imagenUrl = rawUrl;
    }
  }

  if (!backendRes) {
    try {
      const payload = {
        titulo: titulo,
        descripcion: descripcion
      };
      if (imagenUrl !== undefined) {
        payload.imagen_url = imagenUrl;
      }

      backendRes = await axios.put(`${BACKEND_URL}/api/usuario/tickets/${id}`, payload, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 5000
      });
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      const errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail);

      if (isAjax) {
        return res.status(err.response?.status || 500).json({
          success: false,
          error: `Error al actualizar ticket: ${errorMsg}`
        });
      }

      return res.redirect(`/portal-usuario?error=${encodeURIComponent('Error al actualizar ticket: ' + errorMsg)}`);
    }
  }

  if (isAjax) {
    return res.json({
      success: true,
      message: 'Ticket actualizado exitosamente.',
      ticket: backendRes.data
    });
  }

  return res.redirect('/portal-usuario?msg=actualizado');
});

// PUT "/portal-usuario/:id": endpoint REST directo para actualizar tickets desde clientes externos o scripts automatizados
router.put('/:id', uploadMiddleware, async (req, res) => {
  const { id } = req.params;
  const titulo = (req.body.titulo || '').trim();
  const descripcion = (req.body.descripcion || '').trim();

  let imagenUrl = undefined;
  if (req.file) {
    imagenUrl = `/uploads/${req.file.originalname || 'evidencia.png'}`;
  } else if (req.body.imagen_url) {
    const rawUrl = String(req.body.imagen_url).trim();
    // Asegura que la ruta de la imagen apunte a la carpeta local "/uploads/" o venga por una URL web válida
    if (rawUrl.startsWith('/uploads/') || rawUrl.startsWith('http://') || rawUrl.startsWith('https://')) {
      imagenUrl = rawUrl;
    }
  }

  try {
    const payload = {};
    if (titulo) payload.titulo = titulo;
    if (descripcion) payload.descripcion = descripcion;
    if (imagenUrl !== undefined) payload.imagen_url = imagenUrl;

    const backendRes = await axios.put(`${BACKEND_URL}/api/usuario/tickets/${id}`, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 5000
    });

    return res.json({
      success: true,
      message: 'Ticket actualizado exitosamente.',
      ticket: backendRes.data
    });
  } catch (err) {
    const status = err.response?.status || 500;
    const detail = err.response?.data?.detail || err.message;
    return res.status(status).json({
      success: false,
      error: `Error al actualizar ticket: ${detail}`
    });
  }
});

module.exports = router;
