from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from skimage import color, filters, io, measure
from skimage.feature import local_binary_pattern

# Rutas base del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DATA_DIR = PROJECT_ROOT / "data" / "paquete_impresiones_prueba"

def cargar_imagen_uint8(ruta: Path | str) -> np.ndarray:
    path_obj = Path(ruta)
    if not path_obj.exists():
        raise FileNotFoundError(f"No se encontró el archivo de imagen en: {path_obj}")

    img_raw = io.imread(str(path_obj))

    if img_raw.ndim == 3:
        if img_raw.shape[-1] == 4:
            img_raw = img_raw[..., :3]
        gray_float = color.rgb2gray(img_raw)
        gray_uint8 = np.clip(np.round(gray_float * 255.0), 0, 255).astype(np.uint8)
    elif img_raw.ndim == 2:
        if img_raw.dtype == np.uint8:
            gray_uint8 = img_raw
        elif np.issubdtype(img_raw.dtype, np.floating):
            factor = 255.0 if img_raw.max() <= 1.0 else 1.0
            gray_uint8 = np.clip(np.round(img_raw * factor), 0, 255).astype(np.uint8)
        else:
            gray_uint8 = np.clip(img_raw, 0, 255).astype(np.uint8)
    else:
        raise ValueError(f"Dimensión de imagen no soportada: {img_raw.shape}")

    return gray_uint8

def extraer_caracteristicas_imagen(
    image: np.ndarray,
    min_area: int = 50,
    lbp_points: int = 16,
    lbp_radius: int = 2,
    bins_intensidad: int = 32,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    
    # a) Histograma de intensidad
    intensity_hist, intensity_edges = np.histogram(
        image.ravel(),
        bins=bins_intensidad,
        range=(0, 256),
        density=True,
    )

    # b) Umbral de Otsu
    threshold = float(filters.threshold_otsu(image))

    # c) Máscara binaria con inversión de polaridad inteligente
    mean_val = float(np.mean(image))
    if mean_val > 127.0:
        mask = image < threshold
        polaridad = "fondo_claro (image < threshold)"
    else:
        mask = image > threshold
        polaridad = "fondo_oscuro (image > threshold)"

    # d) Etiquetado y medición de regiones
    labeled_mask = measure.label(mask)
    all_regions = measure.regionprops(labeled_mask)
    filtered_regions = [r for r in all_regions if r.area > min_area]

    # e) Estadísticas de regiones
    areas = [r.area for r in filtered_regions]
    if len(areas) > 0:
        area_mean = float(np.mean(areas))
        area_std = float(np.std(areas))
    else:
        area_mean = 0.0
        area_std = 0.0
    num_regions = len(filtered_regions)

    # f) Textura LBP
    lbp = local_binary_pattern(
        image,
        lbp_points,
        lbp_radius,
        method="uniform",
    )
    lbp_bins = np.arange(0, lbp_points + 3)
    lbp_hist, lbp_edges = np.histogram(
        lbp.ravel(),
        bins=lbp_bins,
        density=True,
    )

    # g) Vector de características concatenado (Dimensión: 3 + 32 + 18 = 53)
    features = np.concatenate(
        [
            np.array([area_mean, area_std, float(num_regions)], dtype=np.float64),
            intensity_hist.astype(np.float64),
            lbp_hist.astype(np.float64),
        ]
    )

    metadata: Dict[str, Any] = {
        "image_shape": image.shape,
        "mean_intensity": mean_val,
        "otsu_threshold": threshold,
        "polaridad": polaridad,
        "total_regions": len(all_regions),
        "num_regions_filtradas": num_regions,
        "area_mean": area_mean,
        "area_std": area_std,
        "intensity_hist": intensity_hist,
        "intensity_edges": intensity_edges,
        "lbp_hist": lbp_hist,
        "lbp_edges": lbp_edges,
        "mask": mask,
        "labeled_mask": labeled_mask,
        "regions": filtered_regions,
        "lbp_map": lbp,
    }

    return features, metadata

def generar_figura_comparativa(
    normal_meta: Dict[str, Any],
    normal_img: np.ndarray,
    fallos_data: List[Dict[str, Any]],
    salida_path: Path,
    dpi: int = 160,
) -> Path:
    
    salida_path.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(16, 12), tight_layout=True)
    
    ax_hist = plt.subplot2grid((4, 3), (0, 0), colspan=2)
    ax_lbp = plt.subplot2grid((4, 3), (0, 2))
    
    # Plot Histograma de intensidad
    centers = (normal_meta["intensity_edges"][:-1] + normal_meta["intensity_edges"][1:]) / 2
    ax_hist.plot(centers, normal_meta["intensity_hist"], label="Normal", color="green", linewidth=2)
    for fallo in fallos_data:
        ax_hist.plot(centers, fallo["meta"]["intensity_hist"], alpha=0.3)
    ax_hist.set_title("Histograma de Intensidad - Semana 10", fontweight='bold')
    ax_hist.set_xlabel("Intensidad")
    ax_hist.set_ylabel("Densidad")
    ax_hist.legend()

    # Plot Histograma LBP
    lbp_centers = (normal_meta["lbp_edges"][:-1] + normal_meta["lbp_edges"][1:]) / 2
    ax_lbp.plot(lbp_centers, normal_meta["lbp_hist"], label="Normal", color="blue", linewidth=2)
    for fallo in fallos_data:
        ax_lbp.plot(lbp_centers, fallo["meta"]["lbp_hist"], alpha=0.3)
    ax_lbp.set_title("Histograma LBP (18 bins)", fontweight='bold')
    ax_lbp.set_xlabel("Bins LBP")
    ax_lbp.set_ylabel("Densidad")
    ax_lbp.legend()

    # Grilla de miniaturas
    axes_mosaic = [plt.subplot2grid((4, 3), (row, col)) for row in range(1, 4) for col in range(3)]
    
    ax = axes_mosaic[0]
    ax.imshow(normal_img, cmap='gray')
    ax.set_title("00_impresion_normal", fontsize=10, fontweight='bold', color='green')
    ax.axis("off")
    
    for i, fallo in enumerate(fallos_data):
        if (i + 1) < len(axes_mosaic):
            ax = axes_mosaic[i + 1]
            ax.imshow(fallo['img'], cmap='gray')
            titulo = fallo['nombre'].replace(".png", "")
            ax.set_title(f"{titulo}\nDist: {fallo['dist_total']:.2f}", fontsize=9, color='red')
            ax.axis("off")
            
    for j in range(len(fallos_data) + 1, len(axes_mosaic)):
        axes_mosaic[j].axis("off")
        
    fig.suptitle("Comparativa de Fallos de Impresion con Histogramas", fontsize=14, fontweight='bold')
    fig.savefig(salida_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return salida_path

def ejecutar_pipeline_texturas(
    data_dir: Optional[Path | str] = None,
    out_dir: Optional[Path | str] = None,
) -> Dict[str, Any]:
    
    artifacts_path = Path(out_dir) if out_dir else ARTIFACTS_DIR
    artifacts_path.mkdir(parents=True, exist_ok=True)
    base_dir = Path(data_dir) if data_dir else DATA_DIR

    normal_path = base_dir / "00_impresion_normal.png"
    if not normal_path.exists():
        raise FileNotFoundError(f"Imagen normal no encontrada: {normal_path}")

    # Cargar y extraer características de la normal
    normal_img = cargar_imagen_uint8(normal_path)
    normal_features, normal_meta = extraer_caracteristicas_imagen(normal_img)
    
    fallos_paths = sorted(base_dir.glob("*.png"))
    fallos_paths = [p for p in fallos_paths if "00_impresion_normal" not in p.name]
    
    fallos_data = []
    
    for p in fallos_paths:
        img = cargar_imagen_uint8(p)
        features, meta = extraer_caracteristicas_imagen(img)
        
        dist_total = float(np.linalg.norm(normal_features - features))
        dist_morf = float(np.linalg.norm(normal_features[:3] - features[:3]))
        dist_int = float(np.linalg.norm(normal_features[3:35] - features[3:35]))
        dist_lbp = float(np.linalg.norm(normal_features[35:53] - features[35:53]))
        
        d_reg = meta["num_regions_filtradas"] - normal_meta["num_regions_filtradas"]
        d_area_mean = meta["area_mean"] - normal_meta["area_mean"]
        d_area_std = meta["area_std"] - normal_meta["area_std"]
        
        fallos_data.append({
            "path": p,
            "nombre": p.name,
            "img": img,
            "features": features,
            "meta": meta,
            "dist_total": dist_total,
            "dist_morf": dist_morf,
            "dist_lbp": dist_lbp,
            "dist_int": dist_int,
            "d_reg": d_reg,
            "d_area_mean": d_area_mean,
            "d_area_std": d_area_std
        })

    # Guardar features
    np.save(artifacts_path / "semana10_features.npy", normal_features)
    todas_features = {"00_impresion_normal": normal_features}
    for fd in fallos_data:
        todas_features[fd['nombre']] = fd['features']
    np.save(artifacts_path / "semana10_features_todas.npy", todas_features)
    
    fig_file = artifacts_path / "semana10_histograma.png"
    generar_figura_comparativa(
        normal_meta=normal_meta,
        normal_img=normal_img,
        fallos_data=fallos_data,
        salida_path=fig_file,
    )
    
    imprimir_reporte_consola(normal_path, normal_meta, normal_features, fallos_data, fig_file, artifacts_path / "semana10_features.npy")
    
    return {
        "status": "success",
        "normal_features": normal_features
    }

def _formatear_ruta_relativa(ruta: Path) -> str:
    try:
        return str(ruta.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except Exception:
        return f"artifacts/{ruta.name}"

def imprimir_reporte_consola(
    normal_path: Path,
    normal_meta: Dict[str, Any],
    normal_features: np.ndarray,
    fallos_data: List[Dict[str, Any]],
    fig_file: Path,
    feature_file: Path,
) -> None:
    separador = "=" * 101
    subsep = "-" * 101

    print("\n" + separador)
    print("SOPORTE TI L1/L2 - ANALISIS DE TEXTURAS Y CALIDAD DE IMPRESION")
    print(separador)

    print(f"\n1. ESTADO Y FIRMA BASE DE LA IMAGEN DE REFERENCIA (\"{normal_path.name}\")")
    print(subsep)
    print(f"   - Archivo de referencia: \"{normal_path.name}\"")
    print(f"   - Dimensiones: {normal_meta['image_shape']} px")
    print(f"   - Intensidad media: {normal_meta['mean_intensity']:.2f} (escala [0, 255])")
    print(f"   - Umbral de Otsu: {normal_meta['otsu_threshold']:.2f}")
    print(f"   - Modo de polaridad: \"{normal_meta['polaridad']}\"")
    print(f"   - Regiones conexas (>50 px): {normal_meta['num_regions_filtradas']} (total componentes: {normal_meta['total_regions']})")
    print(f"   - Morfometria de regiones: area media {normal_meta['area_mean']:.2f} px, desviacion estandar {normal_meta['area_std']:.2f} px")
    print(f"   - Bins de extraccion: 32 bins (\"intensity_hist\"), 18 bins (\"lbp_hist\", uniform P=16, R=2)")
    print(f"   - Dimension total vector de caracteristicas: {len(normal_features)} dimensiones float64")

    print("\n2. TABLA COMPARATIVA DE DEFECTOS DE IMPRESION (DISTANCIAS EUCLIDIANAS)")
    print(subsep)

    col_arch = 32
    col_morf = 11
    col_int = 10
    col_lbp = 10
    col_tot = 12
    col_sev = 11

    encabezado_tabla = (
        f"{'Nombre de archivo':<{col_arch}} | "
        f"{'Dist Morf':>{col_morf}} | "
        f"{'Dist Int':>{col_int}} | "
        f"{'Dist LBP':>{col_lbp}} | "
        f"{'Dist Total':>{col_tot}} | "
        f"{'Severidad':<{col_sev}}"
    )
    separador_tabla = "-" * len(encabezado_tabla)

    print(encabezado_tabla)
    print(separador_tabla)

    fallos_data_sorted = sorted(fallos_data, key=lambda x: x["dist_total"], reverse=True)

    for fd in fallos_data_sorted:
        nombre = fd["nombre"]
        dist_morf = fd["dist_morf"]
        dist_int = fd["dist_int"]
        dist_lbp = fd["dist_lbp"]
        d_tot = fd["dist_total"]
        diag = "Alta" if d_tot >= 1000.0 else "Media" if d_tot >= 500.0 else "Baja"
        print(
            f"{nombre:<{col_arch}} | "
            f"{dist_morf:>{col_morf}.2f} | "
            f"{dist_int:>{col_int}.4f} | "
            f"{dist_lbp:>{col_lbp}.4f} | "
            f"{d_tot:>{col_tot}.2f} | "
            f"{diag:<{col_sev}}"
        )

    print("\n3. TOP 3 DE DEFECTOS CON MAYOR SEVERIDAD (PRIORIZACION DE MANTENIMIENTO DE HARDWARE)")
    print(subsep)
    acciones_hardware = {
        "09_desregistro_color.png": "Desalineacion critica en tambores de transferencia o carro de impresion. Accion: calibracion de registro y ajuste mecanico de arrastre.",
        "02_bandas_horizontales.png": "Ciclo repetitivo por defecto en rodillo de carga (PCR) o rodillo de calor. Accion: inspeccion visual de rodillos y limpieza de fusor.",
        "05_impresion_desvanecida.png": "Agotamiento de toner o falla de contacto de polarizacion en rodillo revelador. Accion: reemplazo de consumible y revision de contactos electricos.",
        "01_lineas_verticales_negras.png": "Dano fisico o raya en tambor fotosensible (OPC) o cuchilla de limpieza saturada. Accion: reemplazo de tambor (drum unit).",
        "03_manchas_de_toner.png": "Fuga de toner residual o rodillo de transferencia contaminado. Accion: limpieza de cavidad y aspirado tecnico de toner.",
        "10_toner_corrido_y_arrugas.png": "Presion inadecuada en rodillos fusores o papel humedo. Accion: verificacion de temperatura de fusor y calidad del sustrato.",
        "08_impresion_torcida.png": "Desviacion en bandeja de alimentacion o rodillo de recogida (pickup roller) desgastado. Accion: ajuste de guias de papel y limpieza de gomas.",
        "06_fondo_gris_sucio.png": "Perdida de carga electrostatica en tambor o cuchilla de recuperacion vencida. Accion: revision de fuente de alto voltaje y tambor OPC.",
        "04_imagen_fantasma.png": "Fallo termico en rodillo de teflon de la unidad fusora. Accion: reemplazo de unidad fusora o termistor.",
        "07_marcas_repetitivas.png": "Muesca o perforacion en rodillo fotosensible o de transferencia. Accion: medir circunferencia de defecto e identificar rodillo comprometido.",
    }

    for i, fd in enumerate(fallos_data_sorted[:3], 1):
        nombre = fd["nombre"]
        d_tot = fd["dist_total"]
        diag = "Alta" if d_tot >= 1000.0 else "Media" if d_tot >= 500.0 else "Baja"
        accion = acciones_hardware.get(
            nombre,
            "Inspeccion tecnica y revision funcional de componentes de impresion."
        )
        print(f"   {i}. \"{nombre}\"")
        print(f"      - Distancia total: {d_tot:.2f} | Severidad: \"{diag}\"")
        print(f"      - Diagnostico de hardware: {accion}")

    print("\n4. REGISTRO DE ARTEFACTOS PERSISTIDOS EN DISCO")
    print(subsep)
    features_todas_path = feature_file.parent / "semana10_features_todas.npy"
    print(f"   - Vector base de referencia: \"{_formatear_ruta_relativa(feature_file)}\"")
    print(f"   - Consolidado de caracteristicas: \"{_formatear_ruta_relativa(features_todas_path)}\"")
    print(f"   - Grafico comparativo de histogramas y mosaico: \"{_formatear_ruta_relativa(fig_file)}\"")
    print(separador + "\n")

def main() -> None:
    ejecutar_pipeline_texturas()

if __name__ == "__main__":
    main()
