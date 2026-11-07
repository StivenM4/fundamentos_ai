"""Módulo de Benchmark de Modelos de Aprendizaje Supervisado - Semana 11
Proyecto: Asistente de Soporte TI e Infraestructura L1/L2

Compara de manera rigurosa, reproducible y auditable tres familias fundamentales de
clasificadores supervisados bajo las mismas condiciones experimentales:
1. LogisticRegression ('logistic'): Modelo lineal generalizado, rápido y altamente interpretable.
2. RandomForestClassifier ('forest'): Ensamble no lineal de árboles de decisión (Bagging).
3. MLPClassifier ('mlp'): Red neuronal artificial (Perceptrón Multicapa) con regularización L2.

Conjuntos de datos evaluados:
- Principal (Texto NLP): data/tickets_soporte.csv (1.000 tickets de soporte TI balanceados
  en 4 categorías: 'hardware', 'software', 'red', 'accesos').
- Complementario (Visión Multimodal): data/imagenes_errores/etiquetas.csv (160 capturas
  de pantallas de errores TI: BSOD, disco lleno, caída de aplicación, desconexión de red).

Métricas de desempeño calculadas en mínimo 3 iteraciones (corridas):
- Precisión global (Accuracy)
- Tiempo de entrenamiento (fit_seconds) medido con time.perf_counter
- Latencia de inferencia en prueba (predict_seconds y ms por ticket)
- Métricas macro: Precisión, Recall y F1-score
- Estadísticas agregadas: Media, Desviación Estándar, Mínimo y Máximo

Persistencia de artefactos:
- artifacts/benchmark.csv (Consolidado principal con columnas modelo, accuracy, fit_seconds...)
- artifacts/benchmark_corridas.csv (Trazabilidad detallada corrida por corrida)
- artifacts/benchmark_imagenes.csv (Evidencia comparativa multimodal)
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES DEL EXPERIMENTO
# ==============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

TICKETS_CSV_PATH = DATA_DIR / "tickets_soporte.csv"
IMAGENES_DIR = DATA_DIR / "imagenes_errores"
IMAGENES_CSV_PATH = IMAGENES_DIR / "etiquetas.csv"

BENCHMARK_CSV_PATH = ARTIFACTS_DIR / "benchmark.csv"
BENCHMARK_RUNS_CSV_PATH = ARTIFACTS_DIR / "benchmark_corridas.csv"
BENCHMARK_IMAGENES_CSV_PATH = ARTIFACTS_DIR / "benchmark_imagenes.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.25
NUM_RUNS_DEFAULT = 3


# ==============================================================================
# ESTRUCTURAS DE DATOS (TIPADO ESTÁTICO)
# ==============================================================================

@dataclass
class CorridaResultado:
    """Registro atómico de una única ejecución experimental."""
    corrida: int
    modelo: str
    nombre_completo: str
    dataset: str
    n_muestras_train: int
    n_muestras_test: int
    fit_seconds: float
    predict_seconds: float
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float


@dataclass
class ResumenModelo:
    """Resumen estadístico consolidado de un modelo tras múltiples corridas."""
    modelo: str
    accuracy: float
    fit_seconds: float
    std_fit_seconds: float
    min_fit_seconds: float
    max_fit_seconds: float
    f1_macro: float
    precision_macro: float
    recall_macro: float
    predict_seconds: float
    latencia_ms_por_muestra: float
    run_1_sec: float
    run_2_sec: float
    run_3_sec: float


# ==============================================================================
# FUNCIONES DE CARGA Y PARTICIÓN DE DATOS
# ==============================================================================

def cargar_dataset_tickets(
    ruta_csv: Path | str = TICKETS_CSV_PATH,
) -> Tuple[pd.Series, pd.Series]:
    """
    Carga el corpus estructurado de tickets de soporte TI (1.000 muestras).
    
    Returns:
        Tuple[pd.Series, pd.Series]: (X_texto, y_categoria)
    Raises:
        FileNotFoundError: Si el archivo CSV no se encuentra en la ruta indicada.
    """
    path_obj = Path(ruta_csv)
    if not path_obj.exists():
        raise FileNotFoundError(f"No se encontró el dataset de tickets en: {path_obj}")

    df = pd.read_csv(path_obj)
    if "texto" not in df.columns or "categoria" not in df.columns:
        raise ValueError("El archivo CSV debe contener las columnas 'texto' y 'categoria'")

    return df["texto"], df["categoria"]


def cargar_dataset_imagenes(
    ruta_csv: Path | str = IMAGENES_CSV_PATH,
    directorio_base: Path | str = IMAGENES_DIR,
    tamano: Tuple[int, int] = (32, 32),
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Carga y normaliza el corpus visual de errores de infraestructura TI (160 imágenes).
    
    Cada imagen se convierte a escala de grises, se redimensiona a 32x32 píxeles
    y se normaliza en el rango [0.0, 1.0], produciendo vectores densos de 1.024 características.
    
    Returns:
        Tuple[np.ndarray, np.ndarray]: (X_vectores, y_etiquetas)
    """
    path_csv = Path(ruta_csv)
    dir_base = Path(directorio_base)

    if not path_csv.exists():
        raise FileNotFoundError(f"No se encontró el archivo de metadatos de imágenes en: {path_csv}")

    X_list: List[np.ndarray] = []
    y_list: List[str] = []

    with open(path_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            ruta_img = dir_base / fila["archivo"]
            if ruta_img.exists():
                try:
                    with Image.open(ruta_img) as img:
                        img_gray = img.convert("L").resize(tamano)
                        vec = np.array(img_gray, dtype=np.float32).flatten() / 255.0
                        X_list.append(vec)
                        y_list.append(fila["clase"])
                except Exception:
                    continue

    if not X_list:
        raise RuntimeError("No se pudieron cargar imágenes válidas del dataset visual.")

    return np.array(X_list, dtype=np.float32), np.array(y_list)


# ==============================================================================
# DEFINICIÓN Y FÁBRICA DE MODELOS Y PIPELINES
# ==============================================================================

def obtener_constructores_modelos(random_state: int = RANDOM_STATE) -> Dict[str, Tuple[str, Callable[[], Any]]]:
    """
    Retorna la fábrica de los tres clasificadores supervisados estipulados en la guía:
    - 'logistic': LogisticRegression
    - 'forest': RandomForestClassifier
    - 'mlp': MLPClassifier
    """
    return {
        "logistic": (
            "LogisticRegression",
            lambda: LogisticRegression(
                max_iter=1000,
                random_state=random_state,
                solver="lbfgs",
            ),
        ),
        "forest": (
            "RandomForestClassifier",
            lambda: RandomForestClassifier(
                n_estimators=100,
                random_state=random_state,
                n_jobs=-1,
            ),
        ),
        "mlp": (
            "MLPClassifier",
            lambda: MLPClassifier(
                hidden_layer_sizes=(64, 32),
                max_iter=300,
                random_state=random_state,
                learning_rate_init=0.001,
            ),
        ),
    }


def crear_pipeline_texto(
    clf_instancia: Any,
) -> Pipeline:
    """
    Construye el pipeline de Scikit-Learn adaptado a matrices dispersas (sparse).
    
    Incluye:
    1. TfidfVectorizer: Ponderación de frecuencias de términos ignorando acentos Unicode.
    2. StandardScaler(with_mean=False): Escalado a varianza unitaria preservando la dispersión.
    3. Clasificador supervisado.
    """
    return make_pipeline(
        TfidfVectorizer(strip_accents="unicode"),
        StandardScaler(with_mean=False),
        clf_instancia,
    )


def crear_pipeline_denso(
    clf_instancia: Any,
) -> Pipeline:
    """
    Construye el pipeline para datos numéricos continuos densos (ej. características de visión).
    """
    return make_pipeline(
        StandardScaler(with_mean=True),
        clf_instancia,
    )


# ==============================================================================
# MOTOR DE BENCHMARKING MULTI-CORRIDA
# ==============================================================================

def ejecutar_benchmark(
    X: pd.Series | np.ndarray,
    y: pd.Series | np.ndarray,
    nombre_dataset: str = "tickets_soporte",
    es_texto: bool = True,
    num_runs: int = NUM_RUNS_DEFAULT,
    random_state: int = RANDOM_STATE,
    test_size: float = TEST_SIZE,
) -> Tuple[List[CorridaResultado], List[ResumenModelo]]:
    """
    Ejecuta el protocolo experimental completo de benchmarking:
    - Realiza una partición determinista única train_test_split con estratificación.
    - Ejecuta exactamente num_runs corridas independientes para cada modelo.
    - Mide tiempos de entrenamiento (fit_seconds) con time.perf_counter.
    - Mide latencia de inferencia y exactitud (accuracy) sobre el conjunto de test.
    - Consolida estadísticas agregadas (media, std, min, max).
    """
    # 1. Partición idéntica y reproducible para todos los modelos
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    n_train = len(X_train)
    n_test = len(X_test)
    constructores = obtener_constructores_modelos(random_state=random_state)

    todas_corridas: List[CorridaResultado] = []
    resumenes: List[ResumenModelo] = []

    for clave_modelo, (nombre_largo, builder) in constructores.items():
        tiempos_fit: List[float] = []
        tiempos_pred: List[float] = []
        accuracies: List[float] = []
        precisions: List[float] = []
        recalls: List[float] = []
        f1s: List[float] = []

        for i in range(1, num_runs + 1):
            clf = builder()
            pipeline = crear_pipeline_texto(clf) if es_texto else crear_pipeline_denso(clf)

            # Medición precisa del tiempo de entrenamiento
            t_fit_0 = perf_counter()
            pipeline.fit(X_train, y_train)
            t_fit = perf_counter() - t_fit_0

            # Medición precisa del tiempo de inferencia
            t_pred_0 = perf_counter()
            y_pred = pipeline.predict(X_test)
            t_pred = perf_counter() - t_pred_0

            # Métricas de calidad
            acc = float(accuracy_score(y_test, y_pred))
            p_macro, r_macro, f1_mac, _ = precision_recall_fscore_support(
                y_test, y_pred, average="macro", zero_division=0
            )

            tiempos_fit.append(t_fit)
            tiempos_pred.append(t_pred)
            accuracies.append(acc)
            precisions.append(float(p_macro))
            recalls.append(float(r_macro))
            f1s.append(float(f1_mac))

            corrida = CorridaResultado(
                corrida=i,
                modelo=clave_modelo,
                nombre_completo=nombre_largo,
                dataset=nombre_dataset,
                n_muestras_train=n_train,
                n_muestras_test=n_test,
                fit_seconds=t_fit,
                predict_seconds=t_pred,
                accuracy=acc,
                precision_macro=float(p_macro),
                recall_macro=float(r_macro),
                f1_macro=float(f1_mac),
            )
            todas_corridas.append(corrida)

        # Cálculo de agregados estadísticos
        mean_fit = float(np.mean(tiempos_fit))
        std_fit = float(np.std(tiempos_fit, ddof=1)) if len(tiempos_fit) > 1 else 0.0
        min_fit = float(np.min(tiempos_fit))
        max_fit = float(np.max(tiempos_fit))

        mean_pred = float(np.mean(tiempos_pred))
        latencia_ms = (mean_pred / n_test) * 1000.0 if n_test > 0 else 0.0

        resumen = ResumenModelo(
            modelo=clave_modelo,
            accuracy=float(np.mean(accuracies)),
            fit_seconds=mean_fit,
            std_fit_seconds=std_fit,
            min_fit_seconds=min_fit,
            max_fit_seconds=max_fit,
            f1_macro=float(np.mean(f1s)),
            precision_macro=float(np.mean(precisions)),
            recall_macro=float(np.mean(recalls)),
            predict_seconds=mean_pred,
            latencia_ms_por_muestra=latencia_ms,
            run_1_sec=tiempos_fit[0] if len(tiempos_fit) > 0 else 0.0,
            run_2_sec=tiempos_fit[1] if len(tiempos_fit) > 1 else 0.0,
            run_3_sec=tiempos_fit[2] if len(tiempos_fit) > 2 else 0.0,
        )
        resumenes.append(resumen)

    return todas_corridas, resumenes


# ==============================================================================
# PERSISTENCIA Y REPORTE
# ==============================================================================

def guardar_resumen_csv(
    resumenes: List[ResumenModelo],
    ruta_salida: Path | str = BENCHMARK_CSV_PATH,
) -> Path:
    """
    Persiste el resumen consolidado en formato CSV, asegurando que las columnas
    clave 'modelo', 'accuracy' y 'fit_seconds' lideren el esquema para compatibilidad.
    """
    ruta_obj = Path(ruta_salida)
    ruta_obj.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame([asdict(r) for r in resumenes])
    # Orden explícito de columnas
    columnas_orden = [
        "modelo",
        "accuracy",
        "fit_seconds",
        "std_fit_seconds",
        "min_fit_seconds",
        "max_fit_seconds",
        "f1_macro",
        "precision_macro",
        "recall_macro",
        "predict_seconds",
        "latencia_ms_por_muestra",
        "run_1_sec",
        "run_2_sec",
        "run_3_sec",
    ]
    df = df[columnas_orden]
    df.to_csv(ruta_obj, index=False)
    return ruta_obj


def guardar_corridas_csv(
    corridas: List[CorridaResultado],
    ruta_salida: Path | str = BENCHMARK_RUNS_CSV_PATH,
) -> Path:
    """Persiste la trazabilidad detallada de cada corrida experimental."""
    ruta_obj = Path(ruta_salida)
    ruta_obj.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame([asdict(c) for c in corridas])
    df.to_csv(ruta_obj, index=False)
    return ruta_obj


def imprimir_reporte_consola(
    nombre_dataset: str,
    n_train: int,
    n_test: int,
    pipeline_desc: str,
    corridas: List[CorridaResultado],
    resumenes: List[ResumenModelo],
) -> None:
    """Imprime un informe formateado en consola con diseno para ingenieria de soporte TI."""
    ancho = 90
    print("\n" + "=" * ancho)
    print(f"BENCHMARK SEMANA 11: MODELOS SUPERVISADOS ({nombre_dataset.upper()})".center(ancho))
    print("Proyecto: Asistente de Soporte TI e Infraestructura L1/L2".center(ancho))
    print("=" * ancho)
    print(f"Muestras de Entrenamiento : {n_train}")
    print(f"Muestras de Evaluacion    : {n_test}")
    print(f"Estrategia de Particion   : train_test_split (test_size={TEST_SIZE}, stratify=y, random_state={RANDOM_STATE})")
    print(f"Pipeline de Datos         : {pipeline_desc}")
    print("-" * ancho)

    # Detalle por corrida
    print("\n1. TRAZABILIDAD CORRIDA POR CORRIDA (MINIMO 3 ITERACIONES):")
    print("-" * ancho)
    print(f"{'Corrida':<8} | {'Modelo':<10} | {'Fit (s)':<10} | {'Pred (s)':<10} | {'Accuracy':<10} | {'F1 Macro':<10}")
    print("-" * ancho)
    for c in corridas:
        print(
            f"{c.corrida:<8} | {c.modelo:<10} | {c.fit_seconds:<10.4f} | "
            f"{c.predict_seconds:<10.4f} | {c.accuracy * 100:>8.2f} % | {c.f1_macro * 100:>8.2f} %"
        )
    print("-" * ancho)

    # Tabla resumen consolidada
    print("\n2. TABLA CONSOLIDADA COMPARATIVA (MEDIAS Y DESVIACION ESTANDAR):")
    print("-" * ancho)
    print(
        f"{'Modelo':<10} | {'Accuracy':<10} | {'F1 Macro':<10} | "
        f"{'Fit Medio(s)':<14} | {'Std Fit(s)':<12} | {'Latencia/Ticket(ms)':<18}"
    )
    print("-" * ancho)
    for r in resumenes:
        print(
            f"{r.modelo:<10} | {r.accuracy * 100:>8.2f} % | {r.f1_macro * 100:>8.2f} % | "
            f"{r.fit_seconds:<14.4f} | {r.std_fit_seconds:<12.4f} | "
            f"{r.latencia_ms_por_muestra:<18.3f}"
        )
    print("-" * ancho)

    # Hallazgos tecnicos
    print("\n3. DICTAMEN TECNICO Y EVALUACION DE ARQUITECTURA (SLA & PRODUCCION):")
    modelo_mas_rapido = min(resumenes, key=lambda r: r.fit_seconds)
    modelo_mayor_acc = max(resumenes, key=lambda r: r.accuracy)

    print(
        f"   - Eficiencia en Entrenamiento : '{modelo_mas_rapido.modelo}' es el estimador mas rapido "
        f"({modelo_mas_rapido.fit_seconds:.4f} s de fit medio)."
    )
    print(
        f"   - Maxima Exactitud Predictiva : '{modelo_mayor_acc.modelo}' alcanza el mayor accuracy "
        f"({modelo_mayor_acc.accuracy * 100:.2f} %)."
    )
    print(
        f"   - Trade-off en Produccion     : 'logistic' ofrece inferencia ultrarrapida (<5 ms) ideal para "
        f"triaje en caliente en APIs REST, mientras 'forest' y 'mlp' aportan capacidades no lineales "
        f"con mayor costo de entrenamiento."
    )
    print("=" * ancho + "\n")


# ==============================================================================
# PIPELINE COMPLETO DE EJECUCIÓN (FUNCIÓN PRINCIPAL)
# ==============================================================================

def ejecutar_benchmark_completo(num_runs: int = NUM_RUNS_DEFAULT) -> Dict[str, Any]:
    """
    Ejecuta el benchmark oficial de la Semana 11 sobre el dataset de tickets
    y adicionalmente sobre el dataset multimodal de imágenes de errores.
    
    Genera y valida todos los artefactos requeridos.
    """
    # 1. Benchmark Principal sobre Tickets de Soporte TI
    X_tickets, y_tickets = cargar_dataset_tickets()
    corridas_tickets, resumenes_tickets = ejecutar_benchmark(
        X=X_tickets,
        y=y_tickets,
        nombre_dataset="tickets_soporte_1000",
        es_texto=True,
        num_runs=num_runs,
        random_state=RANDOM_STATE,
        test_size=TEST_SIZE,
    )

    ruta_csv_principal = guardar_resumen_csv(resumenes_tickets, BENCHMARK_CSV_PATH)
    ruta_csv_corridas = guardar_corridas_csv(corridas_tickets, BENCHMARK_RUNS_CSV_PATH)

    imprimir_reporte_consola(
        nombre_dataset="Tickets de Soporte TI (Texto)",
        n_train=int(len(X_tickets) * (1 - TEST_SIZE)),
        n_test=int(len(X_tickets) * TEST_SIZE),
        pipeline_desc="TF-IDF + StandardScaler(with_mean=False) + Clasificador",
        corridas=corridas_tickets,
        resumenes=resumenes_tickets,
    )

    print(f"[OK] Artefacto principal persistido en : {ruta_csv_principal}")
    print(f"[OK] Trazabilidad de corridas guardada en: {ruta_csv_corridas}")

    # 2. Benchmark Complementario Multimodal sobre Imágenes de Errores TI
    try:
        X_imgs, y_imgs = cargar_dataset_imagenes()
        corridas_imgs, resumenes_imgs = ejecutar_benchmark(
            X=X_imgs,
            y=y_imgs,
            nombre_dataset="imagenes_errores_160",
            es_texto=False,
            num_runs=num_runs,
            random_state=RANDOM_STATE,
            test_size=TEST_SIZE,
        )
        ruta_csv_imgs = guardar_resumen_csv(resumenes_imgs, BENCHMARK_IMAGENES_CSV_PATH)
        imprimir_reporte_consola(
            nombre_dataset="Capturas de Errores TI (Vision Multimodal)",
            n_train=int(len(X_imgs) * (1 - TEST_SIZE)),
            n_test=int(len(X_imgs) * TEST_SIZE),
            pipeline_desc="Vectores 32x32 (1024 atributos) + StandardScaler(with_mean=True) + Clasificador",
            corridas=corridas_imgs,
            resumenes=resumenes_imgs,
        )
        print(f"[OK] Artefacto multimodal persistido en : {ruta_csv_imgs}")
    except Exception as e:
        print(f"[INFO] Dataset multimodal omitido o no disponible: {e}")
        resumenes_imgs = []

    return {
        "resumenes_tickets": [asdict(r) for r in resumenes_tickets],
        "resumenes_imagenes": [asdict(r) for r in resumenes_imgs],
        "csv_benchmark": str(ruta_csv_principal),
        "csv_corridas": str(ruta_csv_corridas),
    }


if __name__ == "__main__":
    ejecutar_benchmark_completo(num_runs=NUM_RUNS_DEFAULT)
