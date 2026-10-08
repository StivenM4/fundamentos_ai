import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from skimage import io, feature, filters, measure, color, morphology, data
import logging

try:
    import pytesseract
    import shutil
    HAS_TESSERACT = True
    if not shutil.which("tesseract"):
        posibles_rutas = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            str(Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe"),
        ]
        for r in posibles_rutas:
            if Path(r).exists():
                pytesseract.pytesseract.tesseract_cmd = r
                break
except ImportError:
    HAS_TESSERACT = False

def extraer_texto_de_mascara(mask: np.ndarray, image_gray: np.ndarray) -> str:
    """
    Intenta extraer texto de la imagen completa usando pytesseract sobre la máscara binarizada.
    
    Args:
        mask (np.ndarray): Máscara binaria.
        image_gray (np.ndarray): Imagen en escala de grises normalizada.
        
    Returns:
        str: Texto extraído o cadena vacía.
    """
    texto_extraido = ""
    
    if HAS_TESSERACT:
        try:
            # Convertimos la máscara a uint8 para tesseract (0 o 255)
            mask_uint8 = (mask * 255).astype(np.uint8)
            # Extraemos texto usando pytesseract
            texto_extraido = pytesseract.image_to_string(mask_uint8, lang='eng').strip()
        except Exception as e:
            logging.warning(f"Error al invocar pytesseract: {e}")
            texto_extraido = ""
            
    return texto_extraido

def ejecutar_pipeline_vision(ruta_imagen: str, out_dir=None) -> dict:
    """
    Ejecuta el pipeline de procesamiento de visión por computador.
    """
    path_img = Path(ruta_imagen)
    
    # 1. Cargar imagen (si no existe usar una de ejemplo temporalmente)
    if path_img.exists():
        image_rgb = io.imread(str(path_img))
        if image_rgb.ndim == 3:
            if image_rgb.shape[-1] == 4:
                image_rgb = image_rgb[..., :3]
            image_gray = color.rgb2gray(image_rgb)
        else:
            image_gray = image_rgb
    else:
        print(f"Advertencia: La imagen {ruta_imagen} no se encontró. Usando imagen de prueba (cámara).")
        image_rgb = data.camera()
        image_gray = image_rgb / 255.0
        
    # Asegurarnos de que image_gray está en [0.0, 1.0]
    if image_gray.max() > 1.5:
        image_gray = image_gray / 255.0
        
    print(f"Dimensiones de la imagen: {image_gray.shape}")
        
    # 2. Análisis comparativo de sigma en Canny
    sigmas = [1.0, 2.0, 3.0]
    print("\n--- Análisis de bordes según Sigma ---")
    mejor_sigma = 2.0
    edges_optimo = None
    pixeles_canny_por_sigma = {}
    
    for s in sigmas:
        edges = feature.canny(image_gray, sigma=s)
        pixeles_borde = np.sum(edges)
        pixeles_canny_por_sigma[f"sigma_{s}"] = int(pixeles_borde)
        print(f"Sigma = {s}: {pixeles_borde} píxeles de borde detectados.")
        if s == mejor_sigma:
            edges_optimo = edges
            
    # 3. Segmentación por umbral de Otsu
    threshold = filters.threshold_otsu(image_gray)
    print(f"\nUmbral Otsu calculado: {threshold:.4f}")
    
    # Generar máscara. Invertir si consideramos que el fondo es claro y el texto es oscuro
    if np.mean(image_gray) > 0.5:
        mask = image_gray < threshold
    else:
        mask = image_gray > threshold
        
    # 4. Etiquetado de regiones conectadas
    labels = measure.label(mask)
    num_regiones_total = labels.max()
    print(f"Número total de regiones conectadas: {num_regiones_total}")
    
    # Filtrado básico por área (para remover ruido y aislar texto)
    regiones_filtradas = []
    for region in measure.regionprops(labels):
        if 10 < region.area < 10000:
            regiones_filtradas.append(region)
            
    # 5. Extracción de Texto / OCR
    texto_extraido = extraer_texto_de_mascara(mask, image_gray)
    print("\n--- Texto o Códigos Extraídos ---")
    print(f"Resultado OCR/Heurística: {texto_extraido}")
    
    # Determinar categoría sugerida
    categoria = "Incidente Desconocido"
    if "ERR_CONNECTION" in texto_extraido:
        categoria = "Redes / Conectividad"
    elif "0x80070005" in texto_extraido or "ACCESO DENEGADO" in texto_extraido:
        categoria = "Permisos / Seguridad"
    elif "UNAVAILABLE" in texto_extraido:
        categoria = "Servicios de Infraestructura"
        
    print(f"Categoría Sugerida de TI: {categoria}")
    
    # Armar payload para sistema híbrido
    payload = {
        "origen": "vision",
        "dimensiones": image_gray.shape,
        "umbral_otsu": float(threshold),
        "pixeles_canny_por_sigma": pixeles_canny_por_sigma,
        "regiones_detectadas": int(num_regiones_total),
        "texto_extraido": texto_extraido,
        "categoria_sugerida": categoria
    }
    
    # 6. Generar Artefactos Visuales
    if out_dir is None:
        dir_artefactos = Path("artifacts")
    else:
        dir_artefactos = Path(out_dir)
    dir_artefactos.mkdir(parents=True, exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()
    
    # a) Original
    axes[0].imshow(image_rgb, cmap='gray' if image_rgb.ndim==2 else None)
    axes[0].set_title("a) Imagen Original de Error de TI")
    axes[0].axis("off")
    
    # b) Canny
    axes[1].imshow(edges_optimo, cmap="gray")
    axes[1].set_title(f"b) Contornos Canny (sigma={mejor_sigma})")
    axes[1].axis("off")
    
    # c) Otsu Mask
    axes[2].imshow(mask, cmap="gray")
    axes[2].set_title("c) Máscara Binaria (Otsu)")
    axes[2].axis("off")
    
    # d) Regions
    axes[3].imshow(image_gray, cmap="gray")
    axes[3].imshow(labels, cmap="nipy_spectral", alpha=0.3)
    
    # Dibujar bounding boxes de regiones relevantes
    for r in regiones_filtradas:
        minr, minc, maxr, maxc = r.bbox
        rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                  fill=False, edgecolor='red', linewidth=1.5)
        axes[3].add_patch(rect)
        
    axes[3].set_title("d) Regiones Conectadas (Cajas de texto/botones)")
    axes[3].axis("off")
    
    fig.tight_layout()
    output_path = dir_artefactos / "semana09_vision.png"
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    print(f"\nGuardado: {output_path}")
    
    return payload

if __name__ == "__main__":
    ruta_entrada = "data/imagen_proyecto.png"
    print("Iniciando pipeline de visión por computador para incidentes de TI...\n")
    payload_resultado = ejecutar_pipeline_vision(ruta_entrada)
