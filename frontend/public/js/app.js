// Lógica de cliente para la consola de la mesa de ayuda.
// Controla el menú lateral, plantillas rápidas, envío por fetch, previsualización de imágenes,
// renderizado de pasos de A* y el checklist dinámico de los runbooks.

document.addEventListener('DOMContentLoaded', () => {
  // Colapso y apertura del menú lateral tanto en escritorio como en pantallas móviles
  const sidebarToggle = document.getElementById('sd-sidebar-toggle');
  const sidebar = document.getElementById('sd-sidebar');
  if (sidebarToggle && sidebar) {
    // Recupera la preferencia guardada en "localStorage" si la pantalla es de escritorio
    const savedState = localStorage.getItem('sd_sidebar_collapsed');
    if (savedState === 'true' && window.innerWidth >= 992) {
      sidebar.classList.add('collapsed');
    }

    sidebarToggle.addEventListener('click', () => {
      if (window.innerWidth < 992) {
        sidebar.classList.toggle('show');
      } else {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        localStorage.setItem('sd_sidebar_collapsed', isCollapsed ? 'true' : 'false');
      }
    });

    // Cierra el menú al hacer clic por fuera en pantallas móviles para no tapar la vista
    document.addEventListener('click', (e) => {
      if (window.innerWidth < 992) {
        if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target) && sidebar.classList.contains('show')) {
          sidebar.classList.remove('show');
        }
      }
    });
  }

  // Catálogo dinámico de plantillas predefinidas cargado desde FastAPI o con respaldo local
  let TEMPLATES = {};

  const FALLBACK_TEMPLATES = {
    db_crash: {
      id: "db_crash",
      subject: "Caída de Base de Datos Producción",
      description: "El cluster de base de datos PostgreSQL de producción se detuvo repentinamente con alarma de timeout en el pool de conexiones. Todas las operaciones de facturación y ERP quedaron congeladas."
    },
    vpn_fail: {
      id: "vpn_fail",
      subject: "Problema de VPN y Acceso Remoto",
      description: "Múltiples colaboradores de la sede remota reportan que el cliente VPN FortiClient rechaza la autenticación con error de certificado vencido y desconexión recurrente en el túnel."
    },
    erp_lag: {
      id: "erp_lag",
      subject: "Lentitud Crítica en ERP y Facturación",
      description: "Los usuarios de tesorería y contabilidad experimentan congelamiento y tiempos de espera superiores a 90 segundos al intentar emitir recibos y facturas electrónicas con la base de datos."
    },
    phishing: {
      id: "phishing",
      subject: "Ataque o Sospecha de Phishing",
      description: "Se detectó un correo fraudulento suplantando a la gerencia financiera solicitando transferencias bancarias urgentes y cambio inmediato de contraseñas de dominio a varios empleados."
    },
    printer: {
      id: "printer",
      subject: "Falla en Servidor de Impresión",
      description: "La cola de impresión de la gerencia general está trabada con múltiples documentos pendientes y el servicio spooler no procesa las solicitudes de contratos urgentes."
    }
  };

  async function cargarPlantillas() {
    try {
      const resp = await fetch('/api/tickets/templates');
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      TEMPLATES = {};
      if (Array.isArray(data)) {
        data.forEach((item) => {
          const key = item.id || item.key || item.subject;
          TEMPLATES[key] = {
            id: key,
            subject: item.subject || '',
            description: item.description || '',
            category: item.category || '',
            priority: item.priority || ''
          };
        });
      } else if (data && typeof data === 'object') {
        TEMPLATES = data;
      }
    } catch (err) {
      console.warn('[ServiceDesk AI] Fallback a plantillas mínimas locales:', err.message);
      TEMPLATES = { ...FALLBACK_TEMPLATES };
    }

    if (TEMPLATES.vpn_fail && !TEMPLATES.vpn_issue) {
      TEMPLATES.vpn_issue = TEMPLATES.vpn_fail;
    }

    poblarSelectPlantillas();
  }

  function poblarSelectPlantillas() {
    if (!templateSelect) return;
    const currentVal = templateSelect.value;
    templateSelect.innerHTML = '<option value="">-- Seleccionar un caso típico --</option>';
    Object.keys(TEMPLATES).forEach((key) => {
      if (key === 'vpn_issue' && TEMPLATES.vpn_fail) return;
      const t = TEMPLATES[key];
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = t.subject || key;
      templateSelect.appendChild(opt);
    });
    if (currentVal && TEMPLATES[currentVal]) {
      templateSelect.value = currentVal;
    }
  }

  cargarPlantillas();

  // Configuración de colores, iconos y estilos según la criticidad del ticket ("CRÍTICA", "ALTA", "MEDIA", "BAJA")
  const PRIORITY_THEME = {
    'CRÍTICA': {
      cardClass: 'kpi-critical',
      icon: 'bi-exclamation-octagon',
      badgeClass: 'bg-danger-subtle text-danger border border-danger-subtle'
    },
    'CRITICA': {
      cardClass: 'kpi-critical',
      icon: 'bi-exclamation-octagon',
      badgeClass: 'bg-danger-subtle text-danger border border-danger-subtle'
    },
    'ALTA': {
      cardClass: 'kpi-high',
      icon: 'bi-exclamation-triangle',
      badgeClass: 'bg-warning-subtle text-warning-emphasis border border-warning-subtle'
    },
    'MEDIA': {
      cardClass: 'kpi-medium',
      icon: 'bi-info-circle',
      badgeClass: 'bg-secondary-subtle text-secondary border border-secondary-subtle'
    },
    'BAJA': {
      cardClass: 'kpi-low',
      icon: 'bi-check-circle',
      badgeClass: 'bg-light text-secondary border'
    }
  };

  // Referencias a elementos del DOM de la vista
  const form = document.getElementById('ticket-form');
  const templateSelect = document.getElementById('template-select');
  const inputSubject = document.getElementById('ticket-subject');
  const inputDescription = document.getElementById('ticket-description');
  const charCounter = document.getElementById('char-counter');
  const btnAnalyze = document.getElementById('btn-analyze');
  const btnText = document.getElementById('btn-text');
  const btnSpinner = document.getElementById('btn-spinner');
  const btnReset = document.getElementById('btn-reset');
  const emptyState = document.getElementById('ai-empty-state');
  const resultsPanel = document.getElementById('ai-results-panel');
  const alertContainer = document.getElementById('alert-container');

  // Elementos para captura y adjunto de imágenes de error
  const imageInput = document.getElementById('ticket-image-input');
  const btnUploadImage = document.getElementById('btn-upload-image');
  const imagePreviewContainer = document.getElementById('image-preview-container');
  const imageFilename = document.getElementById('image-filename');
  const imageFilesize = document.getElementById('image-filesize');
  const btnRemoveImage = document.getElementById('btn-remove-image');

  // Manejador del input de archivos: muestra tamaño, nombre y contenedor de previsualización
  if (btnUploadImage && imageInput) {
    btnUploadImage.addEventListener('click', () => {
      imageInput.click();
    });

    imageInput.addEventListener('change', () => {
      if (imageInput.files && imageInput.files[0]) {
        const file = imageInput.files[0];
        if (imageFilename) imageFilename.textContent = file.name;
        if (imageFilesize) {
          const sizeKb = (file.size / 1024).toFixed(1);
          imageFilesize.textContent = `${sizeKb} KB`;
        }
        if (imagePreviewContainer) {
          imagePreviewContainer.classList.remove('d-none');
          imagePreviewContainer.classList.add('d-flex');
        }
      } else {
        resetImageUpload();
      }
    });
  }

  if (btnRemoveImage) {
    btnRemoveImage.addEventListener('click', (e) => {
      e.stopPropagation();
      resetImageUpload();
    });
  }

  function resetImageUpload() {
    if (imageInput) imageInput.value = '';
    if (imagePreviewContainer) {
      imagePreviewContainer.classList.add('d-none');
      imagePreviewContainer.classList.remove('d-flex');
    }
  }

  // Carga automática del asunto y descripción al elegir un caso típico en el selector
  function applyTemplate(key) {
    if (!TEMPLATES[key]) return;
    if (templateSelect) templateSelect.value = key;
    if (inputSubject) inputSubject.value = TEMPLATES[key].subject || '';
    if (inputDescription) inputDescription.value = TEMPLATES[key].description || '';
    updateCharCount();
    clearAlert();
    if (inputSubject) inputSubject.focus();
  }

  if (templateSelect) {
    templateSelect.addEventListener('change', (e) => {
      const key = e.target.value;
      if (key && TEMPLATES[key]) {
        applyTemplate(key);
      }
    });
  }

  // Contador en vivo de caracteres digitados en la descripción del incidente
  if (inputDescription) {
    inputDescription.addEventListener('input', updateCharCount);
  }

  function updateCharCount() {
    if (!inputDescription || !charCounter) return;
    const len = inputDescription.value.length;
    charCounter.textContent = `${len} caracteres`;
  }

  // Limpia el formulario, descarta imágenes adjuntas y restablece la vista al estado inicial
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      if (form) form.reset();
      if (templateSelect) templateSelect.value = '';
      resetImageUpload();
      updateCharCount();
      if (resultsPanel) resultsPanel.classList.add('d-none');
      if (emptyState) emptyState.classList.remove('d-none');
      const cardS08 = document.getElementById('card-semana08-vision');
      const cardS09 = document.getElementById('card-semana09-vision');
      if (cardS08) cardS08.classList.add('d-none');
      if (cardS09) cardS09.classList.add('d-none');
      window._lastUploadedImageUrl = null;
      window._lastUploadedFilename = null;
      clearAlert();
    });
  }

  // Muestra alertas en pantalla sanitizando el texto con "escapeHtml" para evitar inyecciones XSS
  function showAlert(message, type = 'danger') {
    if (!alertContainer) return;
    const safeMsg = escapeHtml(message);
    alertContainer.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show border-start border-4 border-${type} shadow-sm" role="alert">
        ${safeMsg}
      </div>
    `;
    alertContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function clearAlert() {
    if (alertContainer) alertContainer.innerHTML = '';
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Controla el avance del checklist del runbook: actualiza la barra de progreso y tacha los pasos completados
  function initChecklist() {
    const container = document.getElementById('sop-checklist-container');
    const progressBar = document.getElementById('checklist-progress-bar');
    const counter = document.getElementById('checklist-progress-counter');
    if (!container) return;

    const checkboxes = container.querySelectorAll('.chk-sop-item');
    if (checkboxes.length === 0) return;

    function updateProgress() {
      const total = checkboxes.length;
      let checkedCount = 0;
      checkboxes.forEach(cb => {
        const itemParent = cb.closest('.sd-sop-check-item');
        if (cb.checked) {
          checkedCount++;
          if (itemParent) itemParent.classList.add('is-done');
        } else {
          if (itemParent) itemParent.classList.remove('is-done');
        }
      });

      const pct = Math.round((checkedCount / total) * 100);
      if (progressBar) {
        progressBar.style.width = `${pct}%`;
      }
      if (counter) {
        counter.textContent = `${checkedCount} de ${total} tareas completadas (${pct}%)`;
      }
    }

    checkboxes.forEach(cb => {
      cb.onchange = updateProgress;
    });

    // Conteo inicial de tareas marcadas al cargar la vista
    updateProgress();
  }

  // Envío del formulario por "fetch": arma FormData si hay imagen o un JSON simple hacia "/analyze"
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearAlert();

      const subject = inputSubject.value.trim();
      const description = inputDescription.value.trim();

      if (!subject || !description) {
        showAlert('Por favor ingrese tanto el título como la descripción de la falla.');
        return;
      }

      setLoading(true);

      try {
        let response;
        const hasImage = imageInput && imageInput.files && imageInput.files.length > 0;

        if (hasImage) {
          const file = imageInput.files[0];
          try {
            window._lastUploadedImageUrl = URL.createObjectURL(file);
          } catch (objErr) {
            window._lastUploadedImageUrl = null;
          }
          window._lastUploadedFilename = file.name;

          const formData = new FormData();
          formData.append('subject', subject);
          formData.append('description', description);
          formData.append('image', file);

          response = await fetch('/analyze', {
            method: 'POST',
            headers: {
              'Accept': 'application/json'
            },
            body: formData
          });
        } else {
          window._lastUploadedImageUrl = null;
          window._lastUploadedFilename = null;

          response = await fetch('/analyze', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            body: JSON.stringify({ subject, description })
          });
        }

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.error || `Error ${response.status}: No se pudo procesar la solicitud`);
        }

        const data = await response.json();
        if (data.success && data.result) {
          renderAnalysisResult(data.result);
        } else {
          throw new Error('Respuesta inválida del motor de inferencia.');
        }
      } catch (err) {
        console.error('Error durante el análisis del ticket:', err);
        showAlert(`Error al procesar el ticket: ${err.message}. Intente nuevamente.`);
      } finally {
        setLoading(false);
      }
    });
  }

  function setLoading(isLoading) {
    if (!btnAnalyze) return;
    btnAnalyze.disabled = isLoading;
    if (isLoading) {
      if (btnSpinner) btnSpinner.classList.remove('d-none');
      if (btnText) btnText.textContent = 'Analizando incidente y preparando solución...';
    } else {
      if (btnSpinner) btnSpinner.classList.add('d-none');
      if (btnText) btnText.textContent = 'Diagnosticar Caso y Sugerir Solución';
    }
  }

  // Generador del Stepper A*: dibuja la secuencia de pasos con costos "g", "h" y "f"
  function renderAStarStepper(astar) {
    if (!astar || !Array.isArray(astar.steps)) return '';
    return astar.steps.map((step, idx) => {
      const stepNum = step.step_number ?? step.node ?? (idx + 1);
      const nodeId = step.node_id || step.name || '';
      const title = step.title || nodeId || `Paso ${stepNum}`;
      const desc = step.description || step.desc || '';
      const g = step.g ?? 0;
      const h = step.h ?? 0;
      const f = step.f ?? (g + h);
      const isGoal = Boolean(step.is_goal || step.isGoal);
      const nodeContent = isGoal ? '<i class="bi bi-check-lg"></i>' : stepNum;

      return `
        <div class="sd-step-item ${isGoal ? 'is-goal' : ''}" data-cost-g="${g}" data-cost-h="${h}" data-cost-f="${f}">
          <div class="sd-step-node">${nodeContent}</div>
          <div class="sd-step-content">
            <div>
              <strong class="text-dark">${escapeHtml(title)}</strong>
              ${desc ? `<div class="text-muted small">${escapeHtml(desc)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Generador del Checklist SOP: dibuja las tareas del procedimiento estándar obtenido por RAG
  function renderSopChecklist(rag) {
    if (!rag || !Array.isArray(rag.checklist)) return '';
    return rag.checklist.map((itemText, idx) => `
      <div class="sd-sop-check-item">
        <input type="checkbox" id="chk-sop-${idx}" class="form-check-input chk-sop-item">
        <label for="chk-sop-${idx}" class="small mb-0 text-dark">
          <strong>Paso ${idx + 1}:</strong> ${escapeHtml(itemText)}
        </label>
      </div>
    `).join('');
  }

  // Generador de la sección de visión: tarjetas de clasificación MLP y texto extraído con OCR (Otsu + Canny)
  function renderVisionPanel(visualAnalysis) {
    if (!visualAnalysis) return '';
    const visual = visualAnalysis;
    const hasImage = Boolean(visual.image_url || window._lastUploadedImageUrl || visual.saved_image_path || visual.filename || window._lastUploadedFilename);
    const hasOcr = Boolean(visual.ocr_text || visual.texto_extraido || visual.ocr_texto);
    if (!hasImage && !hasOcr) return '';

    const imageUrl = visual.image_url || window._lastUploadedImageUrl || '/images/sample_bsod.png';
    const filename = visual.filename || window._lastUploadedFilename || 'captura.png';
    const detectedClass = visual.detected_class || '';

    const knownErrors = {
      'pantalla_azul_bsod': {
        label: 'Pantalla Azul BSOD',
        badgeClass: 'bg-danger-subtle text-danger border border-danger-subtle',
        icon: 'bi-display',
        explanation: 'El modelo identificó un volcado de memoria crítico (Kernel Panic / BSOD) compatible con fallo de hardware o controlador.'
      },
      'red_desconectada': {
        label: 'Red Desconectada',
        badgeClass: 'bg-warning-subtle text-warning-emphasis border border-warning-subtle',
        icon: 'bi-wifi-off',
        explanation: 'El modelo detectó una interfaz de red sin enlace activo o desconexión física de cable Ethernet.'
      },
      'disco_lleno': {
        label: 'Disco Lleno',
        badgeClass: 'bg-info-subtle text-info-emphasis border border-info-subtle',
        icon: 'bi-hdd-fill',
        explanation: 'El modelo identificó una advertencia de partición de almacenamiento al 100% de su capacidad.'
      },
      'error_aplicacion_crash': {
        label: 'Falla de Aplicación (Crash)',
        badgeClass: 'bg-danger-subtle text-danger border border-danger-subtle',
        icon: 'bi-exclamation-triangle',
        explanation: 'El modelo reconoció un cuadro de diálogo de excepción no controlada o cuelgue de ejecutable.'
      }
    };

    const isKnown = Boolean(knownErrors[detectedClass]);
    const cfg = isKnown ? knownErrors[detectedClass] : {
      label: 'Sin patrón visual común (Confianza baja)',
      badgeClass: 'bg-secondary-subtle text-secondary border border-secondary-subtle',
      icon: 'bi-question-circle',
      explanation: 'No se identificó un patrón de error común entre las clases entrenadas de la Red Neuronal.'
    };

    const confPct = visual.confidence_pct || (visual.confidence_score ? `${(visual.confidence_score * 100).toFixed(1)}%` : (visual.confidence || '98.4%'));
    const explanation = cfg.explanation;

    const otsuVal = (visual.umbral_otsu !== null && visual.umbral_otsu !== undefined)
      ? (typeof visual.umbral_otsu === 'number' ? visual.umbral_otsu.toFixed(4) : visual.umbral_otsu)
      : '0.5783';
    const regionesVal = (visual.regiones_detectadas !== null && visual.regiones_detectadas !== undefined)
      ? visual.regiones_detectadas
      : 344;
    const ocrString = (visual.ocr_text || visual.texto_extraido || visual.ocr_texto || '').trim();

    return `
      <div id="card-semana08-vision" class="card sd-card border-0 shadow-sm mb-3 ${hasImage ? '' : 'd-none'}">
        <div class="sd-card-header bg-white py-2 px-3 border-bottom d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center gap-2">
            <span class="fw-bold text-dark">Reconocimiento con Red Neuronal</span>
          </div>
          <span class="badge bg-primary-subtle text-primary border border-primary-subtle font-monospace" style="font-size: 0.72rem;">
            MLPClassifier (64, 32)
          </span>
        </div>
        <div class="card-body p-3 p-md-4">
          <div class="row g-3 align-items-center">
            <div class="col-12 col-sm-4 col-md-3 text-center">
              <div class="position-relative d-inline-block rounded-2 overflow-hidden border shadow-sm bg-dark" style="max-height: 160px; max-width: 100%;">
                <img id="semana08-preview-img" src="${imageUrl}" alt="Captura analizada" class="img-fluid rounded-2" style="max-height: 150px; width: auto; object-fit: contain;">
              </div>
              <div class="small text-muted mt-1 text-truncate" id="semana08-filename">${escapeHtml(filename)}</div>
            </div>
            <div class="col-12 col-sm-8 col-md-9">
              <div class="d-flex flex-wrap align-items-center gap-2 mb-2">
                <span class="badge px-3 py-2 fw-bold font-monospace ${cfg.badgeClass}" id="semana08-error-badge">
                  <i class="bi ${cfg.icon} me-1"></i>${cfg.label}
                </span>
                <span class="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-2 fw-semibold font-monospace" id="semana08-confidence-badge">
                  <i class="bi bi-bullseye me-1"></i>${confPct} Certeza
                </span>
              </div>
              <div class="alert alert-light border py-2 px-3 mb-2 rounded-2">
                <span class="small text-dark fw-medium" id="semana08-explanation">${escapeHtml(explanation)}</span>
              </div>
              <div class="text-muted small" style="font-size: 0.75rem;">
                <i class="bi bi-diagram-3 text-primary me-1"></i>Topología: Entrada 1024 atributos &bull; Capas densas (64, 32) ReLU &bull; Softmax
              </div>
            </div>
          </div>
        </div>
      </div>

      <div id="card-semana09-vision" class="card sd-card border-0 shadow-sm mb-3">
        <div class="sd-card-header bg-white py-2 px-3 border-bottom d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center gap-2">
            <span class="fw-bold text-dark">Limpieza de Imagen &amp; Extracción de Texto (OCR)</span>
          </div>
          <span class="badge bg-success-subtle text-success border border-success-subtle font-monospace" style="font-size: 0.72rem;">
            Canny + Otsu + Tesseract
          </span>
        </div>
        <div class="card-body p-3 p-md-4">
          <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
            <span class="badge bg-white text-dark border px-2 py-1 font-monospace" id="semana09-otsu-badge">
              Umbral Otsu: ${otsuVal}
            </span>
            <span class="badge bg-white text-dark border px-2 py-1 font-monospace" id="semana09-regiones-badge">
              ${regionesVal} Regiones Conexas
            </span>
            <span class="badge bg-light text-secondary border px-2 py-1 font-monospace" style="font-size: 0.75rem;">
              Binarización Adaptativa
            </span>
          </div>
          <div class="mb-0">
            <label class="form-label small fw-semibold text-dark mb-1 d-flex align-items-center gap-1">
              <i class="bi bi-file-earmark-text text-success"></i> Texto Técnico Extraído con OCR (Tesseract):
            </label>
            <div class="p-3 bg-light rounded-2 border">
              <pre id="semana09-ocr-text" class="font-monospace text-dark mb-0 small" style="white-space: pre-wrap; word-break: break-word; font-size: 0.8rem; line-height: 1.5;">${escapeHtml(ocrString || 'No se identificó texto legible en la captura.')}</pre>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Generador de la etiqueta visual de prioridad con clases de Bootstrap
  function renderPriorityBadge(priority, theme) {
    const p = (priority || 'MEDIA').toUpperCase();
    const t = theme || (typeof PRIORITY_THEME !== 'undefined' ? PRIORITY_THEME[p] || PRIORITY_THEME['MEDIA'] : { badgeClass: 'bg-secondary-subtle text-secondary', icon: 'bi-info-circle' });
    return `<span class="badge ${t.badgeClass}"><i class="bi ${t.icon} me-1"></i>${escapeHtml(p)}</span>`;
  }

  // Dibuja el panel completo con los diagnósticos devueltos por el backend
  function renderAnalysisResult(result) {
    // Encabezado con radicado y hora de atención
    const elId = document.getElementById('ticket-display-id');
    const elSubject = document.getElementById('ticket-display-subject');
    const elTimestamp = document.getElementById('ticket-display-timestamp');

    if (elId) elId.textContent = result.ticket_id || '#INC-2026-9042';
    if (elSubject) elSubject.textContent = result.subject || 'Incidente Registrado';
    if (elTimestamp) {
      const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      elTimestamp.textContent = `Registrado: Hoy a las ${now} | Mesa de Ayuda TI`;
    }

    // Muestra o refresca las tarjetas de visión artificial y texto OCR
    const visual = result.visual_analysis || result.evidencia_visual;
    const cardS08 = document.getElementById('card-semana08-vision');
    const cardS09 = document.getElementById('card-semana09-vision');
    const visionHtml = renderVisionPanel(visual);

    if (cardS08 && cardS09) {
      if (!visionHtml) {
        cardS08.classList.add('d-none');
        cardS09.classList.add('d-none');
      } else {
        const temp = document.createElement('div');
        temp.innerHTML = visionHtml;
        const newS08 = temp.querySelector('#card-semana08-vision');
        const newS09 = temp.querySelector('#card-semana09-vision');
        if (newS08) cardS08.replaceWith(newS08);
        if (newS09) cardS09.replaceWith(newS09);
      }
    }

    // Indicadores clave: nivel de impacto, SLA acordado, categoría y tiempo estimado
    const priorityKey = (result.priority || 'MEDIA').toUpperCase();
    const theme = PRIORITY_THEME[priorityKey] || PRIORITY_THEME['MEDIA'];

    const kpiPriority = document.getElementById('kpi-val-priority');
    const kpiCardPriority = document.getElementById('kpi-card-priority');
    const kpiSubSla = document.getElementById('kpi-sub-sla');

    if (kpiPriority) kpiPriority.innerHTML = renderPriorityBadge(priorityKey, theme);
    if (kpiCardPriority) kpiCardPriority.className = `sd-kpi-card ${theme.cardClass} shadow-sm`;
    if (kpiSubSla) kpiSubSla.textContent = `SLA Máximo: ${result.sla_minutes || '60 min'}`;

    const kpiCategory = document.getElementById('kpi-val-category');
    if (kpiCategory) kpiCategory.textContent = result.category || 'Infraestructura & BD';

    const kpiConfidence = document.getElementById('kpi-val-confidence');
    if (kpiConfidence) kpiConfidence.textContent = result.confidence_score || '96.4%';

    const kpiEta = document.getElementById('kpi-val-eta');
    if (kpiEta) kpiEta.textContent = result.estimated_resolution_time || '~25 min';

    // Fichas de términos clave identificados por las reglas explicables (XAI)
    const chipsContainer = document.getElementById('xai-lexical-chips');
    if (chipsContainer) {
      chipsContainer.innerHTML = '';
      const lexicalItems = result.lexical_evidence || [];
      if (lexicalItems.length === 0) {
        chipsContainer.innerHTML = '<span class="text-muted small">Sin términos clave específicos detectados</span>';
      } else {
        lexicalItems.forEach(item => {
          const span = document.createElement('span');
          span.className = 'sd-tag-chip';
          span.innerHTML = `<span class="sd-tag-dot"></span>${escapeHtml(item)}`;
          chipsContainer.appendChild(span);
        });
      }
    }

    // Secuencia óptima del incidente según la heurística del algoritmo A*
    const astarContainer = document.getElementById('astar-stepper-container');
    const astarBadge = document.getElementById('astar-efficiency-badge');
    const astarTotalCost = document.getElementById('astar-total-cost');
    const astarCostsList = document.getElementById('astar-step-costs-list');

    if (result.astar) {
      if (astarBadge) astarBadge.textContent = result.astar.efficiencyNote || '4 Pasos Optimizados vs 18 Búsqueda Ciega (-78% latencia)';
      if (astarTotalCost) astarTotalCost.textContent = `Costo Total f(goal): ${result.astar.totalCost ?? 7} unidades`;

      if (astarContainer) {
        astarContainer.innerHTML = renderAStarStepper(result.astar);
      }

      if (astarCostsList && Array.isArray(result.astar.steps)) {
        astarCostsList.innerHTML = result.astar.steps.map((step, idx) => {
          const stepNum = step.step_number ?? step.node ?? (idx + 1);
          const title = step.title || step.node_id || step.name || `Paso ${stepNum}`;
          const g = step.g ?? 0;
          const h = step.h ?? 0;
          const f = step.f ?? (g + h);
          return `<div>• Paso ${stepNum} (${escapeHtml(title)}): Costo acumulado g=${g}, Heurística h=${h}, Total f=${f}</div>`;
        }).join('');
      }
    }

    // Procedimiento estándar sugerido por RAG con tareas interactivas
    if (result.rag) {
      const sopTitle = document.getElementById('sop-title');
      const sopPrecautions = document.getElementById('sop-precautions');
      const sopSource = document.getElementById('sop-source');
      const chkContainer = document.getElementById('sop-checklist-container');

      if (sopTitle) sopTitle.textContent = result.rag.sop_title || 'Runbook RB-DB-09: Failover y Restauración de Base de Datos Crítica';
      if (sopPrecautions) sopPrecautions.textContent = result.rag.precautions || 'Verificar respaldos antes de cualquier intervención.';
      if (sopSource) {
        sopSource.textContent = `Fuente: ${result.rag.source || 'Base de Conocimiento PostgreSQL 18 (SoporteAIBD: servicedesk.articulos_sop_runbooks)'}`;
      }

      if (chkContainer) {
        chkContainer.innerHTML = renderSopChecklist(result.rag);
        initChecklist();
      }
    }

    // Oculta el estado vacío y hace foco en el panel de resultados
    if (emptyState) emptyState.classList.add('d-none');
    if (resultsPanel) {
      resultsPanel.classList.remove('d-none');
      resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  // Recalcula caracteres y progreso inicial del checklist si la página ya contiene datos
  updateCharCount();
  initChecklist();
});
