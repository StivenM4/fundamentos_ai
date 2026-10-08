const path = require('path');
const multer = require('multer');

// Extensiones válidas para adjuntar pantallazos de fallas o errores del sistema
const ALLOWED_IMAGE_EXTENSIONS = new Set(['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']);

// Filtra los archivos subidos para rechazar ejecutables, scripts o documentos que no sean imágenes
function imageFileFilter(req, file, cb) {
  const ext = (path.extname(file.originalname) || '').toLowerCase();
  if (ALLOWED_IMAGE_EXTENSIONS.has(ext)) {
    cb(null, true);
  } else {
    cb(new Error('Tipo de archivo no permitido. Solo se aceptan imágenes (PNG, JPG, WEBP, BMP, GIF).'));
  }
}

// Guarda la captura en disco limpiando el nombre original y agregando una marca de tiempo ("timestamp") para evitar sobreescrituras
function createDiskStorage(destDir) {
  return multer.diskStorage({
    destination: (req, file, cb) => cb(null, destDir),
    filename: (req, file, cb) => {
      let ext = (path.extname(file.originalname) || '.png').toLowerCase();
      if (!ALLOWED_IMAGE_EXTENSIONS.has(ext)) ext = '.png';
      const base = path.basename(file.originalname, path.extname(file.originalname)).replace(/[^a-zA-Z0-9_-]/g, '_');
      cb(null, `${base || 'evidencia'}-${Date.now()}${ext}`);
    }
  });
}

// Instancia de Multer en memoria ("memoryStorage") para reenviar el archivo directamente a FastAPI como buffer en peticiones multipart
const memoryUpload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: imageFileFilter
});

module.exports = {
  ALLOWED_IMAGE_EXTENSIONS,
  imageFileFilter,
  createDiskStorage,
  memoryUpload
};
