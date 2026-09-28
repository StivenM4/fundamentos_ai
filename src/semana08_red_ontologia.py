from pathlib import Path
import csv
import pickle
import sqlite3

import networkx as nx
import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
DATA_ERRORES = ROOT / "data" / "imagenes_errores"
CSV_ERRORES = DATA_ERRORES / "etiquetas.csv"

ARTIFACTS.mkdir(parents=True, exist_ok=True)


def cargar_dataset_errores(tamano=(32, 32)):
    """
    Lee las capturas de errores de TI referenciadas en etiquetas.csv,
    las estandariza a escala de grises y las escala a 32x32 píxeles (1024 atributos).
    """
    X, y, rutas = [], [], []

    if not CSV_ERRORES.exists():
        raise FileNotFoundError(f"No se encontró el archivo de metadatos: {CSV_ERRORES}")

    with CSV_ERRORES.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            ruta_img = DATA_ERRORES / fila["archivo"]
            if ruta_img.exists():
                try:
                    with Image.open(ruta_img) as img:
                        # Convertir a escala de grises ('L') y redimensionar
                        img_gray = img.convert("L").resize(tamano)
                        # Normalizar valores a [0.0, 1.0] y aplanar a vector 1D
                        vector = np.array(img_gray, dtype=np.float32).flatten() / 255.0
                        X.append(vector)
                        y.append(fila["clase"])
                        rutas.append(fila["archivo"])
                except Exception as e:
                    print(f"Error procesando imagen {ruta_img.name}: {e}")
            else:
                print(f"Advertencia: Archivo no encontrado {ruta_img}")

    return np.array(X), np.array(y), rutas


# 1. Carga y partición de datos
X, y, rutas = cargar_dataset_errores(tamano=(32, 32))
print(f"Total de imágenes cargadas: {len(X)} de 4 categorías de errores TI")

X_train, X_test, y_train, y_test, rutas_train, rutas_test = train_test_split(
    X,
    y,
    rutas,
    test_size=0.25,
    random_state=42,
    stratify=y,
)

# 2. Reconocimiento mediante Red Neuronal (MLP)
model = MLPClassifier(
    hidden_layer_sizes=(64, 32),
    max_iter=500,
    random_state=42,
)
model.fit(X_train, y_train)

pred = model.predict(X_test)
accuracy = accuracy_score(y_test, pred)

print("\n" + "=" * 65)
print("REPORTE DE CLASIFICACIÓN DETALLADO (Conjunto de Prueba)")
print("=" * 65)
print(classification_report(y_test, pred))
print("=" * 65)
print(f"Accuracy Global: {round(accuracy * 100, 2)}% ({accuracy_score(y_test, pred, normalize=False)} de {len(y_test)} aciertos)\n")

# Persistencia del modelo entrenado
with (ARTIFACTS / "modelo_mlp.pkl").open("wb") as file:
    pickle.dump(model, file)


# 3. Base de datos SQLite para registrar evidencia y metadatos de imágenes
with sqlite3.connect(ARTIFACTS / "imagenes.db") as con:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS imagenes_errores(
            id INTEGER PRIMARY KEY,
            archivo TEXT NOT NULL,
            clase_real TEXT NOT NULL,
            split TEXT NOT NULL
        )
        """
    )
    con.execute("DELETE FROM imagenes_errores")

    registros_errores = [
        (i, rutas_train[i], y_train[i], "train")
        for i in range(len(rutas_train))
    ] + [
        (len(rutas_train) + j, rutas_test[j], y_test[j], "test")
        for j in range(len(rutas_test))
    ]

    con.executemany(
        "INSERT INTO imagenes_errores(id, archivo, clase_real, split) VALUES (?, ?, ?, ?)",
        registros_errores,
    )
    con.commit()

    total_errores_db = con.execute("SELECT COUNT(*) FROM imagenes_errores").fetchone()[0]

print("Registros de imágenes de errores en SQLite:", total_errores_db)


# 4. Ontología para representar significado y relaciones del dominio TI
G = nx.DiGraph()

CLASES_ERRORES = [
    "pantalla_azul_bsod",
    "red_desconectada",
    "disco_lleno",
    "error_aplicacion_crash",
]

# Definición de clases de errores visuales reconocibles
for clase in CLASES_ERRORES:
    G.add_edge("error_visual", clase, rel="tiene_clase")

# Relaciones del modelo sobre los errores
G.add_edges_from(
    [
        ("modelo_mlp", "error_visual", {"rel": "reconoce"}),
        ("imagen_error", "error_visual", {"rel": "representa"}),
        ("prediccion_error", "error_visual", {"rel": "asigna_clase"}),
        ("modelo_mlp", "prediccion_error", {"rel": "produce"}),
    ]
)

print("Relaciones de ontología base de errores:", G.number_of_edges())

# Integración de un ejemplo concreto de prueba en la ontología
ejemplo_idx = 0
ejemplo_archivo = rutas_test[ejemplo_idx]
clase_real_ejemplo = y_test[ejemplo_idx]
clase_predicha_ejemplo = str(model.predict([X_test[ejemplo_idx]])[0])

G.add_edge(f"prediccion_{ejemplo_idx}", clase_predicha_ejemplo, rel="asigna_clase")
G.add_edge(f"imagen_{ejemplo_idx}", f"prediccion_{ejemplo_idx}", rel="genera")

print(
    f"Ejemplo de prueba #{ejemplo_idx}: archivo='{ejemplo_archivo}', real='{clase_real_ejemplo}', predicha='{clase_predicha_ejemplo}'"
)

# Relaciones del dominio TI (clasificación de tickets y categorías de soporte)
RELACIONES_PROYECTO = [
    # Mapeo semántico de los errores visuales a las categorías de soporte
    ("pantalla_azul_bsod", "hardware", {"rel": "pertenece_a_categoria"}),
    ("red_desconectada", "red", {"rel": "pertenece_a_categoria"}),
    ("disco_lleno", "software", {"rel": "pertenece_a_categoria"}),
    ("error_aplicacion_crash", "software", {"rel": "pertenece_a_categoria"}),

    # Relaciones del ticket de soporte y categorías
    ("ticket_soporte", "error_visual", {"rel": "puede_adjuntar"}),
    ("ticket_soporte", "categoria_soporte", {"rel": "pertenece_a"}),
    ("categoria_soporte", "hardware", {"rel": "tiene_clase"}),
    ("categoria_soporte", "software", {"rel": "tiene_clase"}),
    ("categoria_soporte", "red", {"rel": "tiene_clase"}),
    ("categoria_soporte", "accesos", {"rel": "tiene_clase"}),
]

G.add_edges_from(RELACIONES_PROYECTO)

# Exportación del grafo completo a GraphML
nx.write_graphml(G, ARTIFACTS / "ontologia.graphml")

print("Relaciones de integración con soporte TI agregadas:", len(RELACIONES_PROYECTO))
print("Relaciones de ontología totales en GraphML:", G.number_of_edges())
print("Modelo guardado:", (ARTIFACTS / "modelo_mlp.pkl").relative_to(ROOT))
print("Base SQLite guardada:", (ARTIFACTS / "imagenes.db").relative_to(ROOT))
print("Ontología GraphML guardada:", (ARTIFACTS / "ontologia.graphml").relative_to(ROOT))
