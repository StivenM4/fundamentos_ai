# Semana 08: Representaciones del reconocimiento aplicadas al Gestor de Tickets de Soporte TI

## 1. Alcance técnico y criterio de integración

La Semana 08 estudia tres piezas que deben trabajar de forma complementaria:

1. **Reconocimiento mediante redes neuronales artificiales.**
2. **Persistencia de imágenes y metadatos en SQLite.**
3. **Ontologías para representar conceptos y relaciones con significado.**

La idea central es que una predicción aislada no es suficiente. El sistema debe poder conservar evidencia y asociar esa evidencia con conceptos comprensibles dentro del dominio.

El flujo conceptual de la semana es:

```text
ENTRADA
  ↓
MODELO
  ↓
PREDICCIÓN
  ↓
EVIDENCIA PERSISTENTE
  ↓
SIGNIFICADO / ONTOLOGÍA
```

### Decisión metodológica para este proyecto

El repositorio actual está orientado a un **Asistente de Soporte TI**, funcionalmente utilizado como gestor inteligente de tickets. Sin embargo, en el estado actual del proyecto **no existe un corpus etiquetado de capturas de pantalla, fotografías de hardware o imágenes de incidentes TI suficiente para entrenar de manera válida una red neuronal visual propia del dominio**.

Por esta razón, no se fabricará un dataset de imágenes de soporte ni se afirmará que el modelo reconoce fallas visuales reales.

Se adopta la siguiente estrategia:

- La **MLP** se entrena con `load_digits`, exactamente como plantea el material de Semana 08, para demostrar de manera reproducible el funcionamiento de una red neuronal aplicada al reconocimiento de imágenes.
- La **persistencia de evidencia** se adapta al proyecto utilizando exclusivamente los tres casos de telemetría ya definidos en Semana 07.
- A partir de esos casos se generan fichas PNG reproducibles, que funcionan como evidencia visual del estado de cada equipo.
- SQLite conserva tanto el ejercicio base de imágenes como los metadatos propios de soporte TI.
- La ontología conserva las relaciones base de la clase y añade relaciones específicas del gestor de tickets.
- No se conecta falsamente la MLP de dígitos con una predicción de hardware, software, red o accesos. Esa adaptación requerirá posteriormente un conjunto de imágenes TI etiquetado.

---

## 2. Contexto acumulativo revisado del repositorio

### Semana 01

En la rama `main` revisada no se encontró `reports/semana01.md`. Por lo tanto, este documento no atribuye contenidos a una Semana 01 que no está disponible en el repositorio.

### Semana 02: clasificación supervisada de tickets

El proyecto implementa un pipeline sobre `data/tickets_soporte.csv` para predecir:

- categoría: `hardware`, `software`, `red`, `accesos`;
- prioridad: `alta`, `media`, `baja`;
- condición de incidente.

Esta fase establece el triaje inicial del ticket mediante aprendizaje supervisado.

### Semana 03: motor simbólico explicable

El proyecto incorpora reglas y activadores que permiten determinar áreas de IA, conservar los términos que dispararon la decisión y proponer una técnica inicial.

Esta semana aporta explicabilidad y representación simbólica.

### Semana 04: búsqueda heurística y toma de decisiones

A* representa la atención del ticket como un grafo de estados y busca una secuencia de remediación de costo mínimo.

Minimax se conserva como práctica académica independiente, ya que las fallas de infraestructura no representan un adversario racional.

### Semana 05: sistema híbrido de soporte

El proyecto integra reglas expertas, recuperación documental TF-IDF, similitud coseno, una base de conocimiento y clasificación supervisada.

La salida mantiene trazabilidad mediante:

```text
regla + evidencia + similitud + clase
```

### Semana 07: representaciones y reconocimiento de estado

Semana 07 introduce:

- representación numérica de telemetría;
- representación simbólica mediante hechos y reglas;
- autómata DFA para secuencias de eventos;
- generación automática de tickets cuando se detecta un estado no saludable.

Los tres casos definidos en esa semana se reutilizan aquí sin modificar sus valores:

| Equipo | Temperatura CPU | Carga CPU/RAM | Errores/min | Logs | Estado Semana 07 |
|---|---:|---:|---:|---|---|
| `PC-DIRECCION-01` | 70.0 °C | 80 % | 2.0 | `0000` | `saludable` |
| `WS-DISENO-CAD-03` | 72.0 °C | 85 % | 3.0 | `1101` | `no_saludable` |
| `SRV-BASE-DATOS-02` | 76.5 °C | 92 % | 5.0 | `0001` | `no_saludable` |

Semana 08 agrega ahora una nueva capa:

```text
RECONOCER
+
REGISTRAR
+
INTERPRETAR
```

---

## 3. Objetivos de Semana 08 dentro del proyecto

Al finalizar esta práctica el repositorio debe poder demostrar:

1. Entrenamiento y validación reproducible de una red neuronal MLP.
2. Persistencia del modelo entrenado.
3. Creación de una base SQLite de imágenes y metadatos.
4. Persistencia de evidencia visual derivada de la telemetría de Semana 07.
5. Construcción de una ontología en un grafo dirigido.
6. Asociación entre una imagen de prueba, una predicción y un concepto.
7. Inclusión de conceptos y relaciones propias del dominio de soporte TI.
8. Exportación completa de la ontología a GraphML.
9. Generación reproducible de todos los artefactos desde un único script.

---

## 4. Dependencias

El script utiliza:

```python
pickle
sqlite3
matplotlib
networkx
scikit-learn
```

`pickle` y `sqlite3` pertenecen a la biblioteca estándar de Python.

El `requirements.txt` actual del repositorio ya contiene `matplotlib` y `scikit-learn`, pero debe verificarse e incorporar `networkx` antes del commit de Semana 08.

Desde el entorno virtual del proyecto:

```bash
python3 -m pip install networkx
```

Después debe agregarse a `requirements.txt` la versión **realmente instalada** en el entorno. No se fija una versión arbitraria en este reporte.

---

## 5. Arquitectura implementada

La práctica mantiene dos flujos diferenciados para no confundir una demostración académica con una capacidad que el proyecto todavía no posee.

### 5.1. Flujo neuronal reproducible

```text
load_digits
   ↓
imágenes 8 x 8
   ↓
64 valores numéricos
   ↓
MLPClassifier
   ↓
predicción 0..9
   ↓
accuracy
   ↓
modelo_mlp.pkl
```

### 5.2. Flujo de evidencia propio del proyecto

```text
CASOS SEMANA 07
   ↓
telemetría + logs + estado
   ↓
ficha visual PNG
   ↓
SQLite
   ↓
ontología de soporte TI
   ↓
evidencia trazable
```

La segunda ruta no utiliza la MLP para diagnosticar la telemetría. Las fichas PNG son evidencia visual generada a partir de datos existentes, no entradas de entrenamiento del clasificador neuronal.

---

## 6. Diseño de la base SQLite

El archivo generado es:

```text
artifacts/imagenes.db
```

Se crean dos tablas.

### 6.1. Tabla `images`

Conserva la estructura mínima del ejercicio base:

| Campo | Tipo | Uso |
|---|---|---|
| `id` | INTEGER | Identificador del ejemplo |
| `label` | INTEGER | Etiqueta real del dígito |
| `split` | TEXT | Valor `dataset`, siguiendo el ejercicio de clase |

Se registran los primeros 20 ejemplos de `load_digits`.

### 6.2. Tabla `evidencias_soporte`

Es la adaptación propia del proyecto:

| Campo | Tipo | Significado |
|---|---|---|
| `id` | INTEGER | Identificador interno |
| `equipo_id` | TEXT | Equipo analizado |
| `ruta_imagen` | TEXT | Ruta de la ficha visual generada |
| `estado` | TEXT | `saludable` o `no_saludable` |
| `temperatura_cpu_c` | REAL | Temperatura usada en Semana 07 |
| `carga_servidor_pct` | REAL | Carga usada en Semana 07 |
| `tasa_errores_min` | REAL | Errores por minuto |
| `secuencia_logs` | TEXT | Secuencia utilizada por el DFA |

Esta tabla mantiene la evidencia dentro del contexto del sistema de soporte sin inventar nuevas observaciones.

---

## 7. Ontología

### 7.1. Ontología base

Se conservan las siete relaciones del ejercicio de clase:

```text
digito → tiene_clase → cero
digito → tiene_clase → uno
digito → tiene_clase → dos
modelo_mlp → reconoce → digito
imagen → representa → digito
prediccion → asigna_clase → digito
modelo_mlp → produce → prediccion
```

### 7.2. Integración de una predicción concreta

Para el ejemplo `15`:

```text
imagen_15
   ↓ genera
prediccion_15
   ↓ asigna_clase
digito_5
```

Con la semilla y configuración suministradas por la práctica, el ejemplo 15 es reconocido como clase `5`.

### 7.3. Relaciones propias del Gestor de Tickets

La ontología añade nueve relaciones específicas del dominio:

| Origen | Relación | Destino | Lectura natural |
|---|---|---|---|
| `ticket_soporte` | `puede_incluir` | `evidencia_visual_ti` | Un ticket de soporte puede incluir evidencia visual. |
| `evidencia_visual_ti` | `documenta` | `telemetria_equipo` | La evidencia visual documenta la telemetría del equipo. |
| `telemetria_equipo` | `alimenta` | `diagnostico_simbolico` | La telemetría alimenta el diagnóstico simbólico. |
| `diagnostico_simbolico` | `puede_generar` | `ticket_soporte` | Un diagnóstico puede generar un ticket de soporte. |
| `ticket_soporte` | `pertenece_a` | `categoria_soporte` | El ticket pertenece a una categoría de soporte. |
| `categoria_soporte` | `tiene_clase` | `hardware` | Hardware es una categoría del proyecto. |
| `categoria_soporte` | `tiene_clase` | `software` | Software es una categoría del proyecto. |
| `categoria_soporte` | `tiene_clase` | `red` | Red es una categoría del proyecto. |
| `categoria_soporte` | `tiene_clase` | `accesos` | Accesos es una categoría del proyecto. |

Estas clases ya existen en la formulación acumulativa del proyecto desde Semana 02.

---

## 8. Código ejecutable

Crear:

```text
src/semana08_red_ontologia.py
```

con el siguiente contenido:

```python
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

```

---

## 9. Ejecución

Desde la raíz del repositorio:

```bash
source .venv/bin/activate
python3 src/semana08_red_ontologia.py
```

La ejecución validada del código anterior produce:

```text
Accuracy MLP: 0.9622
Registros load_digits en SQLite: 20
Evidencias soporte en SQLite: 3
Relaciones de ontologia base: 7
Ejemplo MLP: 15 5 digito_5
Relaciones propias del proyecto: 9
Relaciones de ontologia finales: 18
Modelo: artifacts/modelo_mlp.pkl
SQLite: artifacts/imagenes.db
GraphML: artifacts/ontologia.graphml
Evidencias PNG: 3
```

El valor:

```text
Accuracy MLP: 0.9622
```

equivale a aproximadamente:

```text
96.22 %
```

de predicciones correctas sobre el conjunto de prueba de `load_digits`.

Este resultado corresponde al experimento de reconocimiento de dígitos y **no debe interpretarse como precisión de diagnóstico del gestor de tickets**.

---

## 10. Artefactos generados

Después de ejecutar el script deben existir:

```text
artifacts/
├── modelo_mlp.pkl
├── imagenes.db
├── ontologia.graphml
└── evidencias_soporte/
    ├── pc-direccion-01.png
    ├── ws-diseno-cad-03.png
    └── srv-base-datos-02.png
```

### `modelo_mlp.pkl`

Contiene la MLP entrenada con `load_digits`.

### `imagenes.db`

Contiene:

- 20 registros del ejercicio base en `images`;
- 3 registros propios del proyecto en `evidencias_soporte`.

### `ontologia.graphml`

Contiene:

- las siete relaciones base;
- las dos relaciones del ejemplo de predicción;
- las nueve relaciones propias del proyecto.

Total esperado:

```text
18 relaciones
```

### `evidencias_soporte/*.png`

Contiene tres fichas generadas directamente desde los casos de Semana 07.

---

## 11. Corrección aplicada frente al orden del ejemplo de clase

En el ejemplo explicado en Semana 08, el archivo GraphML puede exportarse antes de agregar las relaciones:

```text
imagen_15 → genera → prediccion_15
prediccion_15 → asigna_clase → digito_5
```

Si se guarda el grafo antes, las relaciones agregadas posteriormente existen en memoria pero no aparecen en el archivo ya escrito.

En esta implementación:

```python
nx.write_graphml(G, ARTIFACTS / "ontologia.graphml")
```

se ejecuta **al final**, después de agregar tanto la predicción concreta como las relaciones del proyecto.

Así, `ontologia.graphml` representa realmente el estado final del grafo.

---

## 12. Validación de funcionamiento

El código fue verificado con las siguientes condiciones:

| Validación | Resultado |
|---|---|
| El script termina sin excepción | Correcto |
| La MLP entrena correctamente | Correcto |
| Accuracy visible | `0.9622` |
| `modelo_mlp.pkl` se genera | Correcto |
| `imagenes.db` se genera | Correcto |
| Registros tabla `images` | `20` |
| Registros `evidencias_soporte` | `3` |
| `ontologia.graphml` se genera | Correcto |
| Relaciones base | `7` |
| Relaciones propias del proyecto | `9` |
| Relaciones finales GraphML | `18` |
| Evidencias PNG generadas | `3` |

---

## 13. Relación con las semanas anteriores

La Semana 08 no reemplaza las capacidades desarrolladas anteriormente.

```text
SEMANA 02
Texto del ticket
→ categoría / prioridad / incidente

SEMANA 03
Caso de soporte
→ taxonomía explicable / técnica sugerida

SEMANA 04
Ticket previamente clasificado
→ secuencia de atención A*

SEMANA 05
Consulta
→ regla + evidencia documental + similitud + clase

SEMANA 07
Telemetría + logs
→ representación + diagnóstico + posible ticket

SEMANA 08
Reconocimiento neuronal de referencia
+
evidencia visual persistente
+
ontología
→ predicción demostrable + registro + significado
```

La evolución relevante es que el proyecto deja de limitarse a generar una salida y empieza a conservar evidencia estructurada y relaciones semánticas que pueden ser auditadas.

---

## 14. Limitaciones

### 14.1. La MLP todavía no reconoce imágenes de incidentes TI

El repositorio no contiene actualmente un conjunto de imágenes etiquetadas de:

- capturas de pantalla;
- errores visuales;
- cableado;
- LEDs de equipos;
- daños físicos;
- otros incidentes visuales de soporte.

Por ello, entrenar una MLP de soporte TI con datos inventados produciría una evidencia académica engañosa.

`load_digits` se conserva como dataset controlado para comprobar la técnica de reconocimiento neuronal.

### 14.2. Las fichas PNG no son entradas de entrenamiento

Las tres imágenes generadas desde Semana 07 son evidencia visual de telemetría.

No se presentan como dataset de entrenamiento.

Tres ejemplos no son suficientes para validar un clasificador visual generalizable.

### 14.3. El accuracy pertenece exclusivamente a `load_digits`

El `96.22 %` no mide:

- calidad del diagnóstico de soporte;
- precisión del clasificador textual de Semana 02;
- calidad del sistema híbrido de Semana 05;
- precisión sobre capturas o fotografías reales.

### 14.4. Siguiente ampliación válida

Para convertir esta arquitectura en un reconocedor visual real del gestor de tickets se requiere primero un dataset propio etiquetado y trazable.

Solo después tendría sentido sustituir `load_digits` por imágenes reales del dominio.

---

## 15. Conclusiones

1. La Semana 08 demuestra correctamente el principio **modelo reconoce, base registra y ontología interpreta**.
2. La red neuronal se mantiene sobre el dataset controlado establecido por la clase, evitando atribuirle capacidades que el proyecto todavía no posee.
3. SQLite amplía la trazabilidad del proyecto almacenando evidencia derivada de casos ya existentes de Semana 07.
4. La ontología agrega más de las cinco relaciones propias solicitadas y las mantiene conectadas con conceptos que ya forman parte del gestor de tickets.
5. Exportar GraphML al final evita perder las relaciones agregadas después de la creación del grafo base.
6. La implementación conserva la continuidad del proyecto sin crear datos de producción inexistentes.

---

## 16. Estructura propuesta del repositorio después de Semana 08

```text
fundamentos_ai/
├── artifacts/
│   ├── modelo_mlp.pkl
│   ├── imagenes.db
│   ├── ontologia.graphml
│   └── evidencias_soporte/
│       ├── pc-direccion-01.png
│       ├── ws-diseno-cad-03.png
│       └── srv-base-datos-02.png
├── reports/
│   └── semana08.md
├── src/
│   └── semana08_red_ontologia.py
└── requirements.txt
```

---

## 17. Commit sugerido por la guía

Después de verificar ejecución y dependencias:

```bash
git add .
git commit -m "semana08-representaciones"
git status
```

Antes del commit debe comprobarse que `networkx` quedó registrado en `requirements.txt`.

---

## 18. Checklist de entrega

- [x] MLP implementada.
- [x] División entrenamiento/prueba reproducible.
- [x] Accuracy visible.
- [x] Modelo persistido con `pickle`.
- [x] SQLite generado.
- [x] Metadatos de imágenes registrados.
- [x] Evidencia propia del proyecto incorporada.
- [x] Ontología base construida.
- [x] Más de cinco relaciones propias del dominio.
- [x] Predicción concreta enlazada con la ontología.
- [x] GraphML exportado después de completar el grafo.
- [x] Limitaciones identificadas.
- [x] Código ejecutado y validado.
- [x] Integración coherente con el gestor de tickets.
