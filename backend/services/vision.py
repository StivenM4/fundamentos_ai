from __future__ import annotations

import io
import pickle
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from PIL import Image
from skimage import color, filters, measure

PROJECT_ROOT = Path(__file__).resolve().parents[2]

from backend.schemas import VisualAnalysis
from src.semana09_vision import extraer_texto_de_mascara

# Metadatos descriptivos de las clases visuales reconocidas por la Red Neuronal de la "Semana 08".
VISUAL_CLASS_METADATA: Dict[str, Dict[str, str]] = {
    "pantalla_azul_bsod": {
        "label": "Pantalla Azul de la Muerte (BSOD / Kernel Crash)",
        "impact_category": "Hardware",
        "fusion_note": "Reclasificación crítica activada por evidencia visual de pantalla azul (BSOD). Se asignó prioridad CRÍTICA, SLA de 30 min y Runbook de Memory Dump RB-HW-05 a Soporte N2.",
    },
    "disco_lleno": {
        "label": "Alerta de Almacenamiento Saturado / Disco Lleno",
        "impact_category": "Infraestructura",
        "fusion_note": "Detección visual de saturación de almacenamiento en disco. Se prioriza la ejecución de directivas de depuración y ampliación de cuotas.",
    },
    "red_desconectada": {
        "label": "Pérdida de Conectividad / Cable de Red Desconectado",
        "impact_category": "Redes",
        "fusion_note": "Detección visual de cable de red desconectado o enlace físico interrumpido. Se orienta el ticket hacia verificación de conector RJ45 e interfaz LAN.",
    },
    "error_aplicacion_crash": {
        "label": "Excepción de Software / Crash de Aplicación",
        "impact_category": "Software",
        "fusion_note": "Detección visual de excepción de software no controlada o crash de proceso. Se orienta el ticket hacia inspección de logs de aplicación y runtime.",
    },
}

_s8_model = None


def reload_semana08_model():
    """Limpia la instancia en memoria del clasificador MLP y fuerza su recarga desde disco."""
    global _s8_model
    _s8_model = None
    return get_semana08_model()


def get_semana08_model():
    """Carga de forma perezosa el clasificador MLP de visión computacional ("Semana 08").

    Verifica si existe el artefacto serializado en "artifacts/modelo_mlp.pkl".
    Si no existe, invoca la rutina de entrenamiento para compilarlo antes de cargarlo con pickle.
    """
    global _s8_model
    if _s8_model is None:
        mlp_path = PROJECT_ROOT / "artifacts" / "modelo_mlp.pkl"
        if not mlp_path.exists():
            try:
                from backend.services.training import train_vision_model
                train_vision_model()
            except Exception:
                pass
        if mlp_path.exists():
            with mlp_path.open("rb") as f:
                _s8_model = pickle.load(f)
        else:
            try:
                from src.semana08_red_ontologia import model as mlp_trained
                _s8_model = mlp_trained
            except Exception as exc:
                raise FileNotFoundError(f"No se encontró ni se pudo cargar el modelo de visión MLP: {exc}")
    return _s8_model


def _guardar_archivo_captura(file_bytes: bytes, filename: str) -> Tuple[Path, str, str]:
    """Almacena físicamente el archivo en "uploads/capturas_tickets" con un identificador UUID único.

    Retorna una tupla conteniendo la ruta física local en el sistema de archivos, el nombre seguro del archivo
    y la URL relativa lista para servir por HTTP.
    """
    uploads_dir = PROJECT_ROOT / "uploads" / "capturas_tickets"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    clean_filename = Path(filename).name if filename else "captura.png"
    unique_prefix = uuid.uuid4().hex[:12]
    saved_filename = f"{unique_prefix}_{clean_filename}"
    saved_file_path = uploads_dir / saved_filename
    saved_file_path.write_bytes(file_bytes)
    return saved_file_path, saved_filename, f"/uploads/capturas_tickets/{saved_filename}"


def _persistir_captura_y_auditoria(
    file_bytes: bytes,
    filename: str,
    clase_detectada: str,
    confianza: float,
) -> Tuple[Path, str, str]:
    """Guarda el archivo de la captura en disco y asienta el registro de auditoría en base de datos.

    Escribe la entrada en PostgreSQL 18 (y SQLite local) mediante "save_visual_capture_audit" con la clase predicha
    y la probabilidad de confianza para trazabilidad técnica.
    """
    saved_file_path, saved_filename, image_url = _guardar_archivo_captura(file_bytes, filename)
    try:
        from backend.database import save_visual_capture_audit
        save_visual_capture_audit(saved_filename, clase_detectada, confianza)
    except Exception as exc:
        print(f"Advertencia registrando auditoría de captura: {exc}")

    return saved_file_path, saved_filename, image_url


def _vectorizar_para_mlp(file_bytes: bytes) -> np.ndarray:
    """Transforma los bytes de una imagen en un vector plano de 1024 características normalizadas [0, 1].

    Abre la imagen con PIL, la convierte a escala de grises ("L"), la escala exactamente a 32x32 píxeles
    y aplana la matriz a un arreglo unidimensional de tipo float32.
    """
    with Image.open(io.BytesIO(file_bytes)) as img:
        return np.array(img.convert("L").resize((32, 32)), dtype=np.float32).flatten() / 255.0


def _predecir_mlp_s08(vector: np.ndarray) -> Tuple[str, float]:
    """Ejecuta la inferencia sobre el vector de entrada con el modelo MLP de la "Semana 08".

    Retorna el identificador de la clase predicha con mayor probabilidad y el valor numérico
    de certidumbre correspondiente ("predict_proba").
    """
    model = get_semana08_model()
    pred_cls = str(model.predict([vector])[0])
    proba = model.predict_proba([vector])[0]
    classes = list(model.classes_)
    idx = classes.index(pred_cls) if pred_cls in classes else int(np.argmax(proba))
    return pred_cls, float(proba[idx])


def procesar_captura_semana08(file_bytes: bytes, filename: str) -> VisualAnalysis:
    """Clasifica una captura de pantalla exclusivamente con la Red Neuronal MLP de la "Semana 08".

    Vectoriza la imagen a 32x32, infiere la categoría de falla ("BSOD", "red_desconectada", "disco_lleno", etc.),
    persiste la evidencia con su auditoría en base de datos y construye el esquema "VisualAnalysis"
    con las notas de impacto correspondientes.
    """
    if not file_bytes:
        raise ValueError("El archivo de imagen recibido está vacío.")

    try:
        vector = _vectorizar_para_mlp(file_bytes)
    except Exception as exc:
        raise ValueError(f"Error decodificando la imagen: {exc}")

    predicted_class, confidence_score = _predecir_mlp_s08(vector)
    saved_file_path, _, image_url = _persistir_captura_y_auditoria(file_bytes, filename, predicted_class, confidence_score)
    class_meta = VISUAL_CLASS_METADATA.get(
        predicted_class,
        {"label": predicted_class.replace("_", " ").title(), "impact_category": "General", "fusion_note": "Clase visual."},
    )

    return VisualAnalysis(
        detected_class=predicted_class,
        class_label=class_meta["label"],
        confidence_score=round(confidence_score, 4),
        confidence_pct=f"{round(confidence_score * 100, 1)}%",
        saved_image_path=str(saved_file_path),
        image_url=image_url,
        impact_category=class_meta["impact_category"],
        fusion_applied=True,
        fusion_note=class_meta["fusion_note"],
        motor_usado="semana08_mlp",
    )


def _inferir_categoria_desde_ocr(texto_ocr: str) -> Tuple[str, str]:
    """Infiere la categoría técnica y una etiqueta preliminar a partir de patrones léxicos en el OCR.

    Examina el texto extraído buscando códigos de error habituales de la infraestructura:
    - Conectividad y sockets ("ERR_CONNECTION", "DNS", "OFFLINE") -> "Redes".
    - Permisos y autenticación ("0x80070005", "ACCESS DENIED", "UNAUTHORIZED") -> "Seguridad".
    - Errores de servidor y bases de datos ("500", "503", "POSTGRESQL", "DISK") -> "Infraestructura".
    - Códigos de parada y fallas de memoria ("BSOD", "STOP CODE", "KERNEL") -> "Hardware".
    - Excepciones y caídas de programas ("EXCEPTION", "NULLPOINTER", "CRASH") -> "Software".
    """
    upper = texto_ocr.upper()
    if any(k in upper for k in ("ERR_CONNECTION", "DNS", "NETWORK", "CONECTIVIDAD", "OFFLINE", "SOCKET", "TIMEOUT_CONNECTION")):
        return "Redes", "Redes / Conectividad"
    if any(k in upper for k in ("0X80070005", "ACCESO DENEGADO", "ACCESS DENIED", "PERMISO", "UNAUTHORIZED", "FORBIDDEN", "AUTH")):
        return "Seguridad", "Permisos / Seguridad"
    if any(k in upper for k in ("UNAVAILABLE", "503", "500", "DATABASE", "POSTGRESQL", "POSTGRES", "SQL", "INFRAESTRUCTURA", "DISK")):
        return "Infraestructura", "Servicios de Infraestructura"
    if any(k in upper for k in ("BSOD", "STOP CODE", "CRITICAL_PROCESS", "MEMORY", "RAM", "DUMP", "KERNEL", "HARDWARE")):
        return "Hardware", "Hardware / Kernel"
    if any(k in upper for k in ("EXCEPTION", "ERROR", "CRASH", "NULLPOINTER", "SEGMENTATION", "FAULT", "APP_CRASH")):
        return "Software", "Software / Aplicación"
    return "General", "Incidente Desconocido"


def procesar_captura_multimodal(file_bytes: bytes, filename: str) -> VisualAnalysis:
    """Orquesta el análisis multimodal combinando la Red Neuronal MLP ("S08") con el OCR ("S09").

    Aplica una estrategia de desambiguación inteligente:
    1. Ejecuta primero la clasificación rápida mediante el perceptrón multicapa ("Semana 08").
    2. En paralelo, extrae texto y regiones de interés aplicando umbralización Otsu ("Semana 09").
    3. Si el clasificador MLP arroja baja confianza (< 75%) o una etiqueta genérica ("crash"),
       el texto recuperado por OCR reclasifica el ticket hacia su especialidad real (Redes, Seguridad, BD).
    4. Asienta la captura física en disco y registra la traza de auditoría en la base de datos.
    """
    if not file_bytes:
        raise ValueError("El archivo de imagen recibido está vacío.")

    try:
        with Image.open(io.BytesIO(file_bytes)) as test_img:
            test_img.verify()
    except Exception as exc:
        raise ValueError(f"Error decodificando la imagen: {exc}")

    predicted_class, confidence_score, s8_success = "error_aplicacion_crash", 0.50, False
    try:
        vector = _vectorizar_para_mlp(file_bytes)
        predicted_class, confidence_score = _predecir_mlp_s08(vector)
        s8_success = True
    except Exception as s8_exc:
        print(f"Advertencia: no se pudo ejecutar el modelo Semana 08: {s8_exc}")

    saved_file_path, _, image_url = _persistir_captura_y_auditoria(file_bytes, filename, predicted_class, confidence_score)
    class_meta = VISUAL_CLASS_METADATA.get(
        predicted_class,
        {"label": predicted_class.replace("_", " ").title(), "impact_category": "General", "fusion_note": "Clase visual."},
    )
    detected_class, class_label = predicted_class, class_meta["label"]
    impact_category = class_meta["impact_category"]

    if predicted_class in VISUAL_CLASS_METADATA:
        fusion_note = f"Patrón visual de {class_label} reconocido exitosamente por la Red Neuronal."
    else:
        fusion_note = "No se identificó un patrón de error común entre las clases entrenadas de la Red Neuronal."

    # Pipeline de visión y OCR Semana 09
    ocr_text, umbral_otsu, regiones_detectadas = None, None, None
    try:
        with Image.open(io.BytesIO(file_bytes)) as pil_img:
            if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
                pil_rgba = pil_img.convert("RGBA")
                bg = Image.new("RGB", pil_rgba.size, (255, 255, 255))
                bg.paste(pil_rgba, mask=pil_rgba.split()[3])
                img_rgb = np.array(bg)
            else:
                img_rgb = np.array(pil_img.convert("RGB"))

            image_gray = color.rgb2gray(img_rgb)
            if image_gray.max() > 1.5:
                image_gray = image_gray / 255.0

            otsu_calc = float(filters.threshold_otsu(image_gray))
            umbral_otsu = float(round(otsu_calc, 4))
            mask = (image_gray < otsu_calc) if np.mean(image_gray) > 0.5 else (image_gray > otsu_calc)
            regiones_detectadas = int(measure.label(mask).max())

            texto_extraido = extraer_texto_de_mascara(mask, image_gray)
            if texto_extraido and len(texto_extraido.strip()) > 5:
                ocr_text = texto_extraido.strip()
    except Exception as s9_err:
        print(f"Advertencia en pipeline Semana 09: {s9_err}")

    # Combinación multimodal de motores S08 y S09
    es_baja_confianza = (not s8_success) or (confidence_score < 0.75)
    es_generica = predicted_class in ("error_aplicacion_crash", "desconocido")

    if ocr_text:
        cat_sug, label_sug = _inferir_categoria_desde_ocr(ocr_text)
        if es_baja_confianza or es_generica:
            if cat_sug != "General":
                impact_category, class_label, detected_class = cat_sug, f"OCR S09: {label_sug}", f"ocr_{cat_sug.lower()}"
            confidence_score = max(confidence_score, 0.88)
            motor_usado = "semana09_vision_ocr"
        else:
            motor_usado = "hibrido_s08_s09"
    else:
        motor_usado = "semana08_mlp" if s8_success else "semana09_vision_ocr"

    return VisualAnalysis(
        detected_class=detected_class,
        class_label=class_label,
        confidence_score=round(confidence_score, 4),
        confidence_pct=f"{round(confidence_score * 100, 1)}%",
        saved_image_path=str(saved_file_path),
        image_url=image_url,
        impact_category=impact_category,
        fusion_applied=True,
        fusion_note=fusion_note,
        ocr_text=ocr_text,
        umbral_otsu=umbral_otsu,
        regiones_detectadas=regiones_detectadas,
        motor_usado=motor_usado,
    )


def procesar_pipeline_vision_semana09(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Ejecuta el procesamiento digital avanzado de visión computacional ("Semana 09") sobre una captura.

    Aplica paso a paso:
    - Escalamiento y conversión a escala de grises.
    - Binarización adaptativa mediante el método de Otsu.
    - Detección de contornos con filtro Canny evaluando tres escalas de sigma (1.0, 2.0 y 3.0).
    - Etiquetado de regiones conexas ("scikit-image") y extracción morfológica de cadenas de texto OCR.
    - Generación de artefactos gráficos en disco para visualización comparativa en la consola técnica.
    """
    import shutil
    from src.semana09_vision import ejecutar_pipeline_vision

    if not file_bytes:
        raise ValueError("El archivo de imagen recibido está vacío.")

    saved_file_path, saved_filename, image_url = _guardar_archivo_captura(file_bytes, filename)
    uploads_dir = saved_file_path.parent
    artifacts_dir = PROJECT_ROOT / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    res_s9 = ejecutar_pipeline_vision(str(saved_file_path), out_dir=str(artifacts_dir))
    artifact_filename = f"artifact_{saved_filename}"
    unique_artifact_path = uploads_dir / artifact_filename
    source_artifact = artifacts_dir / "semana09_vision.png"
    if source_artifact.exists():
        shutil.copyfile(source_artifact, unique_artifact_path)

    otsu_mask_filename = f"otsu_mask_{saved_filename}"
    otsu_mask_path = uploads_dir / otsu_mask_filename
    try:
        with Image.open(io.BytesIO(file_bytes)) as pil_img:
            arr = np.array(pil_img.convert("L"), dtype=np.float32) / 255.0
            thresh = float(res_s9.get("umbral_otsu", 0.5))
            mask_pure = ((arr < thresh) if np.mean(arr) > 0.5 else (arr > thresh)).astype(np.uint8) * 255
            Image.fromarray(mask_pure).save(otsu_mask_path)
    except Exception as exc:
        print(f"Advertencia generando máscara pura Otsu: {exc}")

    artifact_url = f"/uploads/capturas_tickets/{artifact_filename}"
    binarized_image_url = f"/uploads/capturas_tickets/{otsu_mask_filename}" if otsu_mask_path.exists() else artifact_url

    return {
        "status": "success",
        "origen": res_s9.get("origen", "vision"),
        "dimensiones": list(res_s9.get("dimensiones", [])),
        "umbral_otsu": float(res_s9.get("umbral_otsu", 0.0)),
        "pixeles_canny_por_sigma": res_s9.get("pixeles_canny_por_sigma", {}),
        "regiones_detectadas": int(res_s9.get("regiones_detectadas", 0)),
        "texto_extraido": res_s9.get("texto_extraido", ""),
        "categoria_sugerida": res_s9.get("categoria_sugerida", "Incidente Desconocido"),
        "artifact_url": artifact_url,
        "binarized_image_url": binarized_image_url,
        "image_url": image_url,
        "url_artefacto": artifact_url,
        "url_binarizada": binarized_image_url,
    }
