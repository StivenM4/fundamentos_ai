from pathlib import Path
import pickle
import sqlite3

import matplotlib.pyplot as plt
import networkx as nx
from sklearn.datasets import load_digits
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
EVIDENCIAS = ARTIFACTS / "evidencias_soporte"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
EVIDENCIAS.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# 1. RED NEURONAL DE REFERENCIA DE LA SEMANA 8
# ---------------------------------------------------------------------
# Se conserva load_digits porque es el dataset suministrado en el material
# de clase. El repositorio no contiene actualmente un corpus etiquetado
# de imágenes de soporte TI suficiente para entrenar un clasificador visual
# del dominio sin fabricar datos.
X, y = load_digits(return_X_y=True)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y,
)

model = MLPClassifier(
    hidden_layer_sizes=(64,),
    max_iter=400,
    random_state=42,
)
model.fit(X_train, y_train)

pred = model.predict(X_test)
accuracy = accuracy_score(y_test, pred)
print("Accuracy MLP:", round(accuracy, 4))

with (ARTIFACTS / "modelo_mlp.pkl").open("wb") as file:
    pickle.dump(model, file)


# ---------------------------------------------------------------------
# 2. EVIDENCIAS VISUALES DERIVADAS DE LA SEMANA 7
# ---------------------------------------------------------------------
# Estos tres casos son exactamente los utilizados por
# src/semana07_representaciones.py.
CASOS_SEMANA07 = [
    {
        "equipo_id": "PC-DIRECCION-01",
        "temperatura_cpu_c": 70.0,
        "carga_servidor_pct": 0.80,
        "tasa_errores_min": 2.0,
        "secuencia_logs": "0000",
        "estado": "saludable",
    },
    {
        "equipo_id": "WS-DISENO-CAD-03",
        "temperatura_cpu_c": 72.0,
        "carga_servidor_pct": 0.85,
        "tasa_errores_min": 3.0,
        "secuencia_logs": "1101",
        "estado": "no_saludable",
    },
    {
        "equipo_id": "SRV-BASE-DATOS-02",
        "temperatura_cpu_c": 76.5,
        "carga_servidor_pct": 0.92,
        "tasa_errores_min": 5.0,
        "secuencia_logs": "0001",
        "estado": "no_saludable",
    },
]


def crear_evidencia_visual(caso: dict) -> str:
    """Genera una ficha PNG reproducible usando solo datos existentes de Semana 7."""
    ruta = EVIDENCIAS / f"{caso['equipo_id'].lower()}.png"

    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.axis("off")
    contenido = (
        f"Equipo: {caso['equipo_id']}\n"
        f"Temperatura CPU: {caso['temperatura_cpu_c']} C\n"
        f"Carga CPU/RAM: {caso['carga_servidor_pct'] * 100:.0f}%\n"
        f"Errores: {caso['tasa_errores_min']}/min\n"
        f"Secuencia de logs: {caso['secuencia_logs']}\n"
        f"Estado Semana 7: {caso['estado']}"
    )
    ax.text(0.02, 0.95, contenido, va="top", family="monospace", fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=120, bbox_inches="tight")
    plt.close(fig)

    return ruta.relative_to(ROOT).as_posix()


for caso in CASOS_SEMANA07:
    caso["ruta_imagen"] = crear_evidencia_visual(caso)


# ---------------------------------------------------------------------
# 3. SQLITE: EVIDENCIA DEL EJERCICIO Y EVIDENCIA DEL PROYECTO
# ---------------------------------------------------------------------
with sqlite3.connect(ARTIFACTS / "imagenes.db") as con:
    # Tabla mínima solicitada en el material de Semana 8.
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS images(
            id INTEGER PRIMARY KEY,
            label INTEGER,
            split TEXT
        )
        """
    )
    con.execute("DELETE FROM images")
    con.executemany(
        "INSERT INTO images(id, label, split) VALUES (?, ?, ?)",
        [(i, int(y[i]), "dataset") for i in range(20)],
    )

    # Tabla propia del proyecto. No sustituye la tabla de clase:
    # la complementa con evidencia derivada de Semana 7.
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS evidencias_soporte(
            id INTEGER PRIMARY KEY,
            equipo_id TEXT NOT NULL,
            ruta_imagen TEXT NOT NULL,
            estado TEXT NOT NULL,
            temperatura_cpu_c REAL NOT NULL,
            carga_servidor_pct REAL NOT NULL,
            tasa_errores_min REAL NOT NULL,
            secuencia_logs TEXT NOT NULL
        )
        """
    )
    con.execute("DELETE FROM evidencias_soporte")
    con.executemany(
        """
        INSERT INTO evidencias_soporte(
            id,
            equipo_id,
            ruta_imagen,
            estado,
            temperatura_cpu_c,
            carga_servidor_pct,
            tasa_errores_min,
            secuencia_logs
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                indice,
                caso["equipo_id"],
                caso["ruta_imagen"],
                caso["estado"],
                caso["temperatura_cpu_c"],
                caso["carga_servidor_pct"],
                caso["tasa_errores_min"],
                caso["secuencia_logs"],
            )
            for indice, caso in enumerate(CASOS_SEMANA07, start=1)
        ],
    )
    con.commit()

    total_digits = con.execute("SELECT COUNT(*) FROM images").fetchone()[0]
    total_soporte = con.execute(
        "SELECT COUNT(*) FROM evidencias_soporte"
    ).fetchone()[0]

print("Registros load_digits en SQLite:", total_digits)
print("Evidencias soporte en SQLite:", total_soporte)


# ---------------------------------------------------------------------
# 4. ONTOLOGIA BASE DE LA CLASE
# ---------------------------------------------------------------------
G = nx.DiGraph()

G.add_edges_from(
    [
        ("digito", "cero", {"rel": "tiene_clase"}),
        ("digito", "uno", {"rel": "tiene_clase"}),
        ("digito", "dos", {"rel": "tiene_clase"}),
        ("modelo_mlp", "digito", {"rel": "reconoce"}),
        ("imagen", "digito", {"rel": "representa"}),
        ("prediccion", "digito", {"rel": "asigna_clase"}),
        ("modelo_mlp", "prediccion", {"rel": "produce"}),
    ]
)

print("Relaciones de ontologia base:", G.number_of_edges())


# ---------------------------------------------------------------------
# 5. ENLACE ENTRE UNA PREDICCION Y LA ONTOLOGIA
# ---------------------------------------------------------------------
ejemplo_id = 15
clase_predicha = int(model.predict([X[ejemplo_id]])[0])
concepto = f"digito_{clase_predicha}"

G.add_edge("prediccion_15", concepto, rel="asigna_clase")
G.add_edge("imagen_15", "prediccion_15", rel="genera")

print("Ejemplo MLP:", ejemplo_id, clase_predicha, concepto)


# ---------------------------------------------------------------------
# 6. ADAPTACION ONTOLOGICA AL ASISTENTE DE SOPORTE TI
# ---------------------------------------------------------------------
RELACIONES_PROYECTO = [
    ("ticket_soporte", "evidencia_visual_ti", {"rel": "puede_incluir"}),
    ("evidencia_visual_ti", "telemetria_equipo", {"rel": "documenta"}),
    ("telemetria_equipo", "diagnostico_simbolico", {"rel": "alimenta"}),
    ("diagnostico_simbolico", "ticket_soporte", {"rel": "puede_generar"}),
    ("ticket_soporte", "categoria_soporte", {"rel": "pertenece_a"}),
    ("categoria_soporte", "hardware", {"rel": "tiene_clase"}),
    ("categoria_soporte", "software", {"rel": "tiene_clase"}),
    ("categoria_soporte", "red", {"rel": "tiene_clase"}),
    ("categoria_soporte", "accesos", {"rel": "tiene_clase"}),
]

G.add_edges_from(RELACIONES_PROYECTO)

# La exportacion se hace al final para incluir tanto la ontologia base,
# como la prediccion concreta y las relaciones propias del proyecto.
nx.write_graphml(G, ARTIFACTS / "ontologia.graphml")

print("Relaciones propias del proyecto:", len(RELACIONES_PROYECTO))
print("Relaciones de ontologia finales:", G.number_of_edges())
print("Modelo:", (ARTIFACTS / "modelo_mlp.pkl").relative_to(ROOT))
print("SQLite:", (ARTIFACTS / "imagenes.db").relative_to(ROOT))
print("GraphML:", (ARTIFACTS / "ontologia.graphml").relative_to(ROOT))
print("Evidencias PNG:", len(list(EVIDENCIAS.glob("*.png"))))
