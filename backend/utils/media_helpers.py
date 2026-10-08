from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from backend.schemas import VisualAnalysis
from backend.services.vision import procesar_captura_multimodal

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def buscar_archivo_imagen(imagen_url: Optional[str]) -> Optional[Path]:
    """Localiza la ruta física real de una imagen en el servidor a partir de su URL o ruta relativa.

    Evalúa en orden de precedencia:
    1. Ruta directa (absoluta o relativa al directorio de trabajo).
    2. Ruta relativa a la raíz del repositorio ("PROJECT_ROOT").
    3. Carpeta de capturas dedicadas ("uploads/capturas_tickets/<filename>").
    4. Carpeta general de subidas ("uploads/<filename>").
    Retorna el objeto "Path" si el archivo existe en disco o None si no se encuentra.
    """
    if not imagen_url or not str(imagen_url).strip():
        return None
    url_clean = str(imagen_url).strip()

    # 1. Ruta directa absoluta o relativa al directorio de ejecución
    p = Path(url_clean)
    if p.is_file() and p.exists():
        return p

    # 2. Relativa a la raíz del proyecto
    rel_clean = url_clean.lstrip("/\\")
    p_proj = PROJECT_ROOT / rel_clean
    if p_proj.is_file() and p_proj.exists():
        return p_proj

    # 3. Relativa a uploads/ o subdirectorios de capturas
    filename = Path(url_clean).name
    p_uploads = PROJECT_ROOT / "uploads" / "capturas_tickets" / filename
    if p_uploads.is_file() and p_uploads.exists():
        return p_uploads

    p_uploads_root = PROJECT_ROOT / "uploads" / filename
    if p_uploads_root.is_file() and p_uploads_root.exists():
        return p_uploads_root

    return None


def resolver_visual_analysis_ticket(ticket: Dict[str, Any]) -> Optional[VisualAnalysis]:
    """Recupera el esquema de análisis visual de un ticket o lo procesa en demanda si existe su captura.

    Inspecciona si el ticket ya posee un objeto o diccionario "visual_analysis" (en la raíz
    o dentro de "sugerencia_ia"). Si no está presente pero cuenta con un "imagen_url" válido,
    lee los bytes físicos del archivo en disco y ejecuta "procesar_captura_multimodal" en caliente.
    """
    va_raw = ticket.get("visual_analysis")
    if va_raw is None and isinstance(ticket.get("sugerencia_ia"), dict):
        va_raw = ticket["sugerencia_ia"].get("visual_analysis")

    if va_raw is not None:
        if isinstance(va_raw, VisualAnalysis):
            return va_raw
        if isinstance(va_raw, dict):
            try:
                return VisualAnalysis(**va_raw)
            except Exception:
                pass

    imagen_url = ticket.get("imagen_url")
    if imagen_url:
        img_path = buscar_archivo_imagen(imagen_url)
        if img_path and img_path.exists():
            try:
                file_bytes = img_path.read_bytes()
                if file_bytes:
                    return procesar_captura_multimodal(file_bytes, img_path.name)
            except Exception as exc:
                print(f"Advertencia procesando imagen del ticket {ticket.get('id')}: {exc}")

    return None


# Alias con guion bajo mantenidos para garantizar retrocompatibilidad con llamadas legadas.
_buscar_archivo_imagen = buscar_archivo_imagen
_resolver_visual_analysis_ticket = resolver_visual_analysis_ticket

