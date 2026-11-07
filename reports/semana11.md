# Semana 11: Benchmark de Modelos Supervisados y Architecture Decision Record (ADR) para Soporte TI

## 1. Ficha del Documento de Decisión Arquitectónica (ADR-003)

```text
=====================================================================================================
REGISTRO DE DECISIÓN ARQUITECTÓNICA (ARCHITECTURE DECISION RECORD)
=====================================================================================================
Identificador : ADR-003
Título        : Selección del modelo de clasificación supervisada para el triaje de tickets L1/L2
Fecha         : Octubre de 2026
Estado        : Aceptado y aplicado en producción
Autor         : Técnico de soporte TI L1/L2 y estudiante de Ingeniería de Sistemas
Proyecto      : Asistente de Soporte TI e Infraestructura con Inteligencia Artificial
Componentes   : src/semana11_benchmark.py, backend/routers/tickets.py, data/tickets_soporte.csv
=====================================================================================================
```

---

## 2. Contexto Operativo y Evolución del Sistema (Semanas 02 a 11)

En la mesa de ayuda técnica corporativa en Bogotá, la gestión de incidentes y requerimientos de infraestructura no puede depender de intuiciones ni de configuraciones arbitrarias. A lo largo del semestre, el sistema evolucionó desde un clasificador elemental hasta una plataforma completa de diagnóstico, búsqueda y visión artificial:

1. **Semana 02 (`src/semana02_fundamentos.py`):** Se implementó el primer clasificador supervisado multietiqueta combinando `"TfidfVectorizer"` con `"LogisticRegression"` bajo `"MultiOutputClassifier"`, logrando predecir categoría técnica, nivel de prioridad y tipo de ticket (incidente vs requerimiento).
2. **Semana 03 (`src/semana03_taxonomia.py`):** Se construyó el motor simbólico de explicabilidad (XAI) basado en reglas deterministas y un catálogo de activadores léxicos para clasificar requerimientos en 7 disciplinas de IA, validando 50 casos dorados de prueba.
3. **Semana 04 (`src/semana04_astar.py` y `src/semana04_minimax.py`):** Se formuló la planificación heurística informada $A^*$ sobre un grafo de estados ITIL con función $f(n) = g(n) + h(n)$ garantizando consistencia matemática frente a rutas bloqueadas, y se analizó la búsqueda adversarial Minimax para contrastar decisiones de suma cero frente a fallas operativas de hardware.
4. **Semana 05 (`src/semana05_sistema_hibrido.py`):** Se ensambló la arquitectura híbrida RAG combinando reglas inmediatas ("Fast-Path"), recuperación TF-IDF sobre 75 manuales procedimentales, validación estadística y un guardrail de contención al 20% para evitar alucinaciones en comandos de consola (PowerShell, CMD, Bash).
5. **Semana 07 (`src/semana07_representaciones.py`):** Se integró la telemetría de servidores en un espacio vectorial tridimensional $\mathbb{R}^3$ (CPU, RAM, temperatura), evaluando reglas simbólicas y procesando transiciones de alerta con un Autómata Finito Determinista (DFA).
6. **Semana 08 (`src/semana08_red_ontologia.py`):** Se introdujo una red neuronal artificial Perceptrón Multicapa (`"MLPClassifier"`) para clasificar capturas de errores en monitores (pantalla azul BSOD, red desconectada, disco lleno, fallo de aplicación), persistiendo eventos en SQLite y estructurando relaciones de conocimiento en una ontología GraphML.
7. **Semana 09 (`src/semana09_vision.py`):** Se implementó el pipeline de procesamiento digital de imágenes con filtros Canny, binarización global de Otsu y extracción OCR con Tesseract para recuperar códigos de parada (ej. `"0x0000007B"`) directamente desde capturas de pantalla.
8. **Semana 10 (`src/semana10_texturas.py`):** Se diseñó el extractor de 53 características cuantitativas combinando morfometría conexa, histogramas fotométricos de 32 niveles y texturas LBP uniformes ($P=16, R=2$) para clasificar severidad de desgaste en hojas de impresión escaneadas.

### 2.1 El problema técnico a resolver en la Semana 11

Con el crecimiento del sistema y la integración de la API REST en FastAPI, surgió una pregunta obligatoria para el entorno de producción: ¿cuál algoritmo supervisado debe liderar el motor principal de clasificación de tickets de soporte TI?

Hasta la Semana 10 se utilizaban configuraciones puntuales sin una comparación cuantitativa formal bajo condiciones de laboratorio idénticas. Para tomar una decisión arquitectónica responsable, la Semana 11 establece un protocolo de experimentación riguroso implementado en `src/semana11_benchmark.py`:

* Se comparan tres familias algorítmicas canónicas: un modelo lineal generalizado (`"LogisticRegression"`), un ensamble no lineal de árboles de decisión (`"RandomForestClassifier"`) y una red neuronal artificial (`"MLPClassifier"`).
* Se evalúan sobre el corpus real del proyecto: `"data/tickets_soporte.csv"`, compuesto por 1.000 tickets estructurados y balanceados exactamente en cuatro categorías operativas (`"hardware"`, `"software"`, `"red"`, `"accesos"` con 250 tickets cada una).
* Como validación multimodal complementaria, se ejecuta el mismo protocolo sobre `"data/imagenes_errores/etiquetas.csv"` (160 capturas de pantalla en vectores densos de 1.024 dimensiones generados a 32x32 píxeles).
* Se exige un mínimo de tres iteraciones independientes midiendo tiempos precisos de entrenamiento (`"fit_seconds"`) con `"perf_counter"`, exactitud (`"accuracy"`), macro F1-score y latencia de predicción por muestra, generando el archivo `"artifacts/benchmark.csv"`.

---

## 3. Matriz de Razonamiento Práctico de Ingeniería

Siguiendo el estándar de análisis técnico aplicado en infraestructura y desarrollo de software, la evaluación se desglosa en la siguiente matriz:

```text
+-------------------------+---------------------------------------------------------------------------------+
| ELEMENTO DE RAZONAMIENTO| DEFINICIÓN EN EL PROYECTO DE SOPORTE TI                                         |
+-------------------------+---------------------------------------------------------------------------------+
| 1. ¿Qué se va a hacer?  | Evaluar de forma empírica tres modelos supervisados (logistic, forest, mlp)     |
|                         | sobre 1.000 tickets reales de texto y 160 capturas de errores de infraestructura.|
+-------------------------+---------------------------------------------------------------------------------+
| 2. ¿Cómo se va a hacer? | Empleando Scikit-Learn con un mismo particionamiento estratificado              |
|                         | (test_size=0.25, random_state=42), pipeline con TfidfVectorizer y               |
|                         | StandardScaler(with_mean=False), ejecutando 3 corridas cronometradas con         |
|                         | time.perf_counter para promediar tiempos y calcular desviaciones.               |
+-------------------------+---------------------------------------------------------------------------------+
| 3. ¿Por qué se hace?    | Porque en producción un sistema de mesa de ayuda no puede escoger algoritmos     |
|                         | por suposiciones; se requiere sustentar la relación entre precisión, latencia de|
|                         | respuesta, tiempo de reentrenamiento y costo computacional en servidor.         |
+-------------------------+---------------------------------------------------------------------------------+
| 4. ¿Qué resultado       | Una exactitud superior al 93% en los 3 modelos, un archivo consolidado          |
|    genera?              | "artifacts/benchmark.csv" con métricas auditables y la justificación técnica     |
|                         | para elegir el clasificador del backend FastAPI.                               |
+-------------------------+---------------------------------------------------------------------------------+
| 5. ¿Qué problemas o     | RandomForest y MLP consumen órdenes de magnitud adicionales de CPU al entrenar, |
|    limitaciones tiene?  | mientras que la matriz TF-IDF genera más de 1.500 características léxicas que   |
|                         | romperían la memoria si se convierten a matrices densas con StandardScaler.     |
+-------------------------+---------------------------------------------------------------------------------+
| 6. ¿Qué alternativa     | Una arquitectura desacoplada donde LogisticRegression atiende el triaje rápido  |
|    puede ser mejor?     | en caliente (inferencia en menos de 0.1 ms) y los modelos de ensamble o redes   |
|                         | neuronales se reservan para validación cruzada nocturna o vectores continuos.   |
+-------------------------+---------------------------------------------------------------------------------+
```

---

## 4. Explicación Detallada del Código (`src/semana11_benchmark.py`)

El script `src/semana11_benchmark.py` organiza el proceso de medición a través de un flujo limpio y reproducible:

```text
DATOS DE SOPORTE TI ("tickets_soporte.csv")
                    ↓
PARTICIÓN DETERMINISTA ESTRATIFICADA (train_test_split: 75% train / 25% test)
                    ↓
CICLO EXPERIMENTAL DE TRES CORRIDAS (Iteración 1, 2 y 3)
  ├── Modelo 1: "logistic" (LogisticRegression, max_iter=1000, solver="lbfgs")
  ├── Modelo 2: "forest"   (RandomForestClassifier, n_estimators=100, n_jobs=-1)
  └── Modelo 3: "mlp"      (MLPClassifier, capas=(64, 32), max_iter=300)
                    ↓
MEDICIÓN DE TIEMPOS DE ENTRENAMIENTO (perf_counter() en fit)
                    ↓
EVALUACIÓN DE INFERENCIA Y EXACTITUD (predict, accuracy_score, f1_macro)
                    ↓
CONSOLIDACIÓN ESTADÍSTICA (Media, Desviación Estándar, Mínimo, Máximo)
                    ↓
GENERACIÓN DE ARTEFACTOS ("artifacts/benchmark.csv" y "artifacts/benchmark_corridas.csv")
                    ↓
DECISIÓN TÉCNICA ARQUITECTÓNICA (ADR-003)
```

### 4.1 Módulos y librerías importadas

El código utiliza componentes estándar y robustos del ecosistema científico de Python:

* `pathlib.Path`: Administra rutas de archivos de manera independiente al sistema operativo (Windows, Linux, macOS), evitando fallas por barras inclinadas en scripts que corren en servidores mixtos.
* `time.perf_counter`: Proporciona un reloj monotónico de alta resolución para medir intervalos de tiempo en microsegundos y nanosegundos, insensible a ajustes del reloj del sistema operativo.
* `pandas`: Carga, filtra y manipula los datos tabulares desde los archivos CSV del proyecto.
* `sklearn.feature_extraction.text.TfidfVectorizer`: Transforma los textos de los incidentes en una representación vectorial ponderada según la frecuencia del término y su rareza inversa en el corpus (`"strip_accents='unicode'"` normaliza tildes y caracteres especiales comunes en reportes en español).
* `sklearn.model_selection.train_test_split`: Divide el conjunto de datos en entrenamiento (75%) y prueba (25%) manteniendo la distribución de clases mediante el parámetro `"stratify=y"`.
* `sklearn.pipeline.make_pipeline`: Empaqueta la transformación de características y el estimador en un único objeto serializable, evitando la fuga de información ("data leakage") durante la fase de ajuste.
* `sklearn.preprocessing.StandardScaler`: Escala los datos para que tengan media cero y varianza unitaria.
* `sklearn.linear_model.LogisticRegression`: Modelo lineal generalizado que optimiza la verosimilitud logística multiclase utilizando el optimizador L-BFGS.
* `sklearn.ensemble.RandomForestClassifier`: Ensamble de 100 árboles de decisión entrenados con muestras bootstrap ("Bagging") y selección aleatoria de atributos.
* `sklearn.neural_network.MLPClassifier`: Red neuronal Perceptrón Multicapa con dos capas ocultas (64 y 32 neuronas) y optimizador Adam con regularización L2.
* `sklearn.metrics.accuracy_score` y `precision_recall_fscore_support`: Calculan exactitud global y métricas agregadas tipo macro para clases balanceadas.

### 4.2 La regla técnica de `StandardScaler(with_mean=False)` en texto

Uno de los detalles técnicos más críticos del pipeline de texto implementado en la función `crear_pipeline_texto()` es el manejo del escalado sobre matrices dispersas:

```python
def crear_pipeline_texto(clf_instancia: Any) -> Pipeline:
    return make_pipeline(
        TfidfVectorizer(strip_accents="unicode"),
        StandardScaler(with_mean=False),
        clf_instancia,
    )
```

Cuando `TfidfVectorizer` procesa los 1.000 tickets, crea un vocabulario con más de 1.500 términos distintos. Cada ticket individual utiliza entre 10 y 30 palabras, lo que significa que más del 98% de los valores de la fila son ceros. Scikit-Learn almacena esto de manera eficiente como una matriz dispersa (`scipy.sparse.csr_matrix`), guardando únicamente las coordenadas y valores distintos de cero.

Si se configurara `StandardScaler(with_mean=True)`, el algoritmo intentaría restar la media a cada columna:
$$x_{\text{centrado}} = x - \mu$$

Dado que la media $\mu$ de cada palabra en el corpus es un valor positivo pequeño (por ejemplo, 0.003), restar $\mu$ a todas las celdas que tenían valor 0 las convertiría en $-0.003$. Esto destruiría la estructura dispersa ("densifying the matrix"), obligando a almacenar millones de números flotantes en memoria RAM. En un servidor con miles de tickets, esto provocaría una excepción `MemoryError` o un reinicio del proceso por falta de memoria (OOM). Al fijar `with_mean=False`, el escalador solo divide por la desviación estándar ($\sigma$), conservando los ceros intactos y manteniendo el consumo de memoria en rangos mínimos.

### 4.3 Partición de datos y aislamiento experimental

Para asegurar que la comparación sea justa y matemáticamente válida, los tres modelos deben evaluarse exactamente sobre los mismos datos. En la función `ejecutar_benchmark()`:

```python
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y,
)
```

* `test_size=0.25`: Se asignan 750 registros para entrenamiento y 250 registros para prueba.
* `random_state=42`: Fija la semilla pseudoaleatoria para que la partición sea idéntica en cualquier equipo o servidor.
* `stratify=y`: Garantiza que tanto en entrenamiento como en prueba cada categoría (`"hardware"`, `"software"`, `"red"`, `"accesos"`) tenga exactamente el 25% de representación (187 o 188 muestras de cada una en train, 62 o 63 en test).

### 4.4 Fabricación de los modelos y ciclo de tres corridas

La función `obtener_constructores_modelos()` utiliza funciones lambda para generar instancias limpias e independientes en cada corrida:

```python
def obtener_constructores_modelos(random_state: int = 42):
    return {
        "logistic": (
            "LogisticRegression",
            lambda: LogisticRegression(max_iter=1000, random_state=random_state, solver="lbfgs"),
        ),
        "forest": (
            "RandomForestClassifier",
            lambda: RandomForestClassifier(n_estimators=100, random_state=random_state, n_jobs=-1),
        ),
        "mlp": (
            "MLPClassifier",
            lambda: MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=random_state, learning_rate_init=0.001),
        ),
    }
```

Cada modelo se evalúa a través de un bucle de tres iteraciones (`num_runs = 3`). En cada iteración:
1. Se instancia el pipeline desde cero.
2. Se toma la marca de tiempo inicial con `t_fit_0 = perf_counter()`.
3. Se entrena con `pipeline.fit(X_train, y_train)`.
4. Se calcula el tiempo de ajuste `t_fit = perf_counter() - t_fit_0`.
5. Se toma la marca de inferencia `t_pred_0 = perf_counter()`.
6. Se predice sobre el conjunto de test `y_pred = pipeline.predict(X_test)`.
7. Se calcula la duración de la inferencia `t_pred = perf_counter() - t_pred_0`.
8. Se evalúa `accuracy_score` y `f1_macro`.

---

## 5. Modelos Comparados y Resultados Experimentales

La ejecución del benchmark sobre el corpus de 1.000 tickets de soporte TI arrojó los datos que se consolidaron en los archivos `"artifacts/benchmark_corridas.csv"` y `"artifacts/benchmark.csv"`.

### 5.1 Trazabilidad corrida por corrida (Tickets de soporte TI)

```text
+---------+----------+--------------------+-------------+--------------+----------+----------+
| CORRIDA | MODELO   | NOMBRE COMPLETO    | FIT TIME(s) | PRED TIME(s) | ACCURACY | F1 MACRO |
+---------+----------+--------------------+-------------+--------------+----------+----------+
| 1       | logistic | LogisticRegression | 0.0677 s    | 0.0210 s     | 93.60 %  | 93.58 %  |
| 2       | logistic | LogisticRegression | 0.0537 s    | 0.0126 s     | 93.60 %  | 93.58 %  |
| 3       | logistic | LogisticRegression | 0.0496 s    | 0.0162 s     | 93.60 %  | 93.58 %  |
+---------+----------+--------------------+-------------+--------------+----------+----------+
| 1       | forest   | RandomForest       | 0.4412 s    | 0.0616 s     | 94.40 %  | 94.42 %  |
| 2       | forest   | RandomForest       | 0.4286 s    | 0.0638 s     | 94.40 %  | 94.42 %  |
| 3       | forest   | RandomForest       | 0.4542 s    | 0.0696 s     | 94.40 %  | 94.42 %  |
+---------+----------+--------------------+-------------+--------------+----------+----------+
| 1       | mlp      | MLPClassifier      | 0.8127 s    | 0.0116 s     | 94.00 %  | 94.02 %  |
| 2       | mlp      | MLPClassifier      | 0.7616 s    | 0.0130 s     | 94.00 %  | 94.02 %  |
| 3       | mlp      | MLPClassifier      | 0.8493 s    | 0.0147 s     | 94.00 %  | 94.02 %  |
+---------+----------+--------------------+-------------+--------------+----------+----------+
```

### 5.2 Tabla consolidada de métricas y estadísticas agregadas

Los valores consolidados registrados en `"artifacts/benchmark.csv"` resumen el desempeño global:

```text
+----------+----------+----------+--------------+-------------+-------------------+----------------------+
| MODELO   | ACCURACY | F1 MACRO | FIT MEDIO(s) | STD FIT(s)  | LATENCIA TOTAL(s) | LATENCIA/TICKET (ms) |
+----------+----------+----------+--------------+-------------+-------------------+----------------------+
| logistic | 93.60 %  | 93.58 %  | 0.0570 s     | 0.0095 s    | 0.0166 s          | 0.0665 ms            |
| forest   | 94.40 %  | 94.42 %  | 0.4413 s     | 0.0128 s    | 0.0650 s          | 0.2599 ms            |
| mlp      | 94.00 %  | 94.02 %  | 0.8078 s     | 0.0441 s    | 0.0131 s          | 0.0525 ms            |
+----------+----------+----------+--------------+-------------+-------------------+----------------------+
```

### 5.3 Análisis de variabilidad entre ejecuciones

Al revisar las tres corridas, se aprecian dos comportamientos complementarios:

1. **Constancia estricta de la exactitud (`"accuracy"`):**  
   Para cada modelo, la métrica de exactitud es idéntica en las tres iteraciones (`"logistic"` = 0.9360, `"forest"` = 0.9440, `"mlp"` = 0.9400). Esto ocurre porque se fijó `random_state=42` tanto en la función `train_test_split()` como en los constructores de cada modelo. En consecuencia, la selección de hiperplanos en la regresión logística, los cortes de división en los árboles del bosque y los pesos iniciales en la red neuronal parten de estados idénticos, convergiendo a los mismos parámetros numéricos.

2. **Fluctuación de milisegundos en el tiempo de entrenamiento (`"fit_seconds"`):**  
   A diferencia del accuracy, el tiempo de ejecución presenta variaciones en el orden de milisegundos:
   * `"logistic"` varió entre `0.0496 s` y `0.0677 s` ($\sigma = 0.0095\text{ s}$).
   * `"forest"` osciló entre `0.4286 s` y `0.4542 s` ($\sigma = 0.0128\text{ s}$).
   * `"mlp"` fluctuó entre `0.7616 s` y `0.8493 s` ($\sigma = 0.0441\text{ s}$).  
   Estas diferencias no se deben al algoritmo, sino a factores físicos del sistema operativo Windows y del hardware:
   * **Planificador de hilos del kernel de Windows:** Durante la ejecución, el sistema operativo intercala hilos de procesos en segundo plano (antivirus, servicios de red, telemetría).
   * **Comportamiento de la memoria caché de la CPU:** En la primera corrida, los datos leídos del disco y compilados por la máquina virtual de Python deben transferirse desde la memoria RAM principal hacia la caché L1, L2 y L3 del procesador ("cold start" o arranque en frío). En las corridas subsecuentes, muchas páginas de memoria ya se encuentran cacheadas, reduciendo ligeramente el tiempo de acceso.
   * **Gestión térmica y escalado de frecuencia (Thermal Throttling / Turbo Boost):** El procesador ajusta dinámicamente sus frecuencias de reloj según la carga y la temperatura del núcleo en milisegundos puntuales.

### 5.4 Benchmark complementario sobre capturas de errores (Visión multimodal)

Como prueba de contraste sobre características densas, se evaluaron los mismos tres modelos sobre las 160 capturas de pantalla de `"data/imagenes_errores/"` normalizadas a vectores de 1.024 dimensiones:

```text
+----------+----------+----------+--------------+-------------+-------------------+----------------------+
| MODELO   | ACCURACY | F1 MACRO | FIT MEDIO(s) | STD FIT(s)  | LATENCIA TOTAL(s) | LATENCIA/MUESTRA(ms) |
+----------+----------+----------+--------------+-------------+-------------------+----------------------+
| logistic | 62.50 %  | 60.34 %  | 0.3095 s     | 0.1001 s    | 0.0011 s          | 0.0281 ms            |
| mlp      | 60.00 %  | 58.34 %  | 0.3225 s     | 0.0332 s    | 0.0013 s          | 0.0323 ms            |
| forest   | 57.50 %  | 53.27 %  | 0.3636 s     | 0.0247 s    | 0.0460 s          | 1.1497 ms            |
+----------+----------+----------+--------------+-------------+-------------------+----------------------+
```

En este conjunto visual, `"logistic"` mantuvo el mejor desempeño (62.50%), demostrando que en espacios de alta dimensionalidad (1.024 píxeles) con un volumen limitado de muestras (160 imágenes), los modelos lineales generalizados sufren menos sobreajuste ("overfitting") que los árboles de decisión o las redes neuronales no regularizadas.

---

## 6. Decisión Técnica Arquitectónica (ADR-003) y Justificación

```text
=====================================================================================================
DECISIÓN ARQUITECTÓNICA FORMAL: SELECCIÓN DEL CLASIFICADOR DE TRIAJE L1/L2
=====================================================================================================
Modelo Principal Aceptado para Inferencia en Caliente : "logistic" (LogisticRegression)
Rol del Modelo en la Arquitectura                     : Motor en línea para la API REST FastAPI
Modelo Secundario / Validador en Lote                 : "forest" (RandomForestClassifier)
=====================================================================================================
```

### 6.1 Justificación técnica de la decisión

Para seleccionar el modelo de producción se evaluaron tres factores críticos en la operación de soporte:

1. **Relación entre exactitud y costo computacional:**  
   `"forest"` obtuvo la mayor exactitud sobre tickets con un `94.40%`, mientras que `"logistic"` alcanzó un `93.60%`. La diferencia entre ambos es de apenas dos tickets adicionales clasificados correctamente de un total de 250 muestras de prueba ($0.80\%$ de margen).  
   Sin embargo, el costo de obtener ese $0.80\%$ adicional es desproporcionado:
   * El tiempo de entrenamiento de `"forest"` (`0.4413 s`) es **7.74 veces mayor** que el de `"logistic"` (`0.0570 s`).
   * La latencia de inferencia por ticket de `"forest"` (`0.2599 ms`) es **3.91 veces más lenta** que la de `"logistic"` (`0.0665 ms`).  
   En un entorno donde la mesa de ayuda atiende cientos de radicaciones simultáneas o reentrena sus modelos de manera incremental cuando los técnicos cierran tickets, `"logistic"` ofrece una eficiencia computacional notablemente superior.

2. **Explicabilidad técnica (XAI) para la mesa de ayuda:**  
   En la gestión de incidentes L1/L2, los técnicos y coordinadores no aceptan decisiones basadas en "cajas negras". Si el sistema enruta un ticket a la cola de `"red"`, debe ser capaz de justificar qué términos causaron esa decisión.  
   En `"LogisticRegression"`, los coeficientes calculados por el optimizador L-BFGS corresponden directamente al peso logarítmico de cada término léxico:
   $$z_k = \beta_{0, k} + \sum_{j=1}^{M} \beta_{j, k} \cdot x_j$$
   Esto permite inspeccionar de inmediato qué palabras (como `"switch"`, `"vlan"`, `"gateway"`, `"ip"`) empujaron la probabilidad hacia la clase `"red"`. En contraste, en `"RandomForestClassifier"` la importancia de características se dispersa a lo largo de 100 árboles con divisiones de Gini no lineales, y en `"MLPClassifier"` los pesos quedan distribuidos en combinaciones no interpretables entre 64 y 32 neuronas ocultas.

3. **Huella de memoria y estabilidad en producción:**  
   El modelo serializado de `"logistic"` (vectorizador TF-IDF + pesos lineales) ocupa menos de 150 KB en disco y se carga de forma instantánea en la memoria de la API FastAPI. Un modelo de `"forest"` con 100 estimadores y miles de nodos internos consume más de 5 MB de memoria serializada y exige mayor ancho de banda si se sincroniza entre múltiples instancias de contenedores.

---

## 7. Ventajas, Limitaciones y Consecuencias del Modelo Seleccionado

```text
+-------------------+---------------------------------------------------------------------------------+
| ASPECTO           | EVALUACIÓN EN PRODUCCIÓN PARA "LOGISTICREGRESSION"                              |
+-------------------+---------------------------------------------------------------------------------+
| Ventajas          | 1. Velocidad de ajuste ultrarrápida (0.057 s para 1.000 tickets).              |
| Principales       | 2. Latencia de inferencia en sub-milisegundo (0.066 ms por ticket).             |
|                   | 3. Explicabilidad matemática directa mediante coeficientes lineales beta.        |
|                   | 4. Excelente generalización sobre matrices dispersas TF-IDF de alta dimensión.  |
|                   | 5. Consumo mínimo de memoria RAM y serialización ligera en disco.              |
+-------------------+---------------------------------------------------------------------------------+
| Limitaciones      | 1. Asume fronteras de decisión lineales entre los términos del vocabulario.     |
| Conocidas         | 2. No captura interacciones cruzadas complejas entre palabras distantes         |
|                   |    a menos que se utilicen n-gramas explícitos.                                 |
|                   | 3. Sensible a desbalances severos de clases si no se ajustan los pesos.         |
+-------------------+---------------------------------------------------------------------------------+
| Consecuencias     | Lo que se gana: tiempo de respuesta instantáneo en la consola web de soporte,  |
| Operativas        | posibilidad de reentrenar en caliente desde la API (/api/models/train) sin      |
|                   | congelar el servidor y transparencia en auditorías ITIL.                        |
|                   | Lo que se sacrifica: el 0.8% marginal de exactitud que alcanzaba RandomForest.  |
|                   | Qué vigilar: degradación de métricas cuando ingresen tickets con vocabulario     |
|                   | técnico nuevo (jergas no presentes en el dataset original).                     |
+-------------------+---------------------------------------------------------------------------------+
```

### 7.1 Integración con la arquitectura global del sistema

La elección de `"logistic"` se integra con el ecosistema completo del proyecto:

```text
[USUARIO RADICA TICKET]
         ↓
Consola Web (Node.js + Express en Puerto 3000)
         ↓  (Petición HTTP POST /api/tickets/analyze)
API REST (Python + FastAPI en Puerto 8000)
         ↓
PIPELINE EN PRODUCCIÓN:
  ├── 1. Triaje Rápido en Caliente : LogisticRegression (0.066 ms) -> categoría, prioridad, tipo
  ├── 2. Explicabilidad Simbólica : Catálogo de activadores léxicos XAI (Semana 03)
  ├── 3. Asistente Procedimental  : Sistema Híbrido RAG sobre 75 manuales (Semana 05)
  └── 4. Auditoría y Trazabilidad : Persistencia SQL en SQLite / PostgreSQL (Semana 08)
```

---

## 8. Ecosistema Tecnológico y Relación entre Lenguajes de Programación

En el diseño de software corporativo de soporte TI, la selección del lenguaje de programación debe responder a las fortalezas operativas de cada plataforma:

### 8.1 ¿Por qué se utilizó Python para la experimentación y los modelos de IA?

* **Ecosistema científico consolidado:** Python concentra las bibliotecas de referencia mundial para ciencia de datos (`scikit-learn`, `numpy`, `pandas`, `scipy`). Estas bibliotecas no están programadas exclusivamente en Python; sus núcleos matemáticos están implementados en C, C++ y Fortran (mediante BLAS y LAPACK), lo que permite operaciones matriciales vectorizadas a máxima velocidad.
* **Prototipado rápido y trazabilidad:** La sintaxis concisa de Python permite escribir pipelines reproducibles de benchmarking en pocas líneas de código, integrando medición de tiempos, cálculo de matrices y serialización de modelos con un estándar común.
* **Integración nativa con FastAPI:** A través de FastAPI y Uvicorn, Python expone los modelos entrenados como servicios web REST asíncronos y tipados con Pydantic, desacoplando la computación matemática de la capa de interfaz de usuario.

### 8.2 ¿Por qué se utilizó Node.js y Express para la aplicación web?

* **Concurrencia basada en eventos no bloqueantes:** La interfaz de usuario (`frontend/`) atiende múltiples peticiones simultáneas de técnicos de soporte que consultan dashboards, radican solicitudes y visualizan estados de tickets. El bucle de eventos ("Event Loop") de Node.js es ideal para manejar cientos de conexiones HTTP concurrentes con baja huella de memoria.
* **Separación de responsabilidades:** Dejar que Node.js sirva las páginas HTML (mediante plantillas EJS y Bootstrap 5) y consuma las APIs de Python mediante peticiones HTTP internas desacopla el ciclo de vida del cliente del ciclo de vida de los modelos. Si un modelo se está reentrenando, el servidor web de Node.js continúa respondiendo sin interrupción a los usuarios.

### 8.3 Comparación frente a entornos empresariales (Java y C# / .NET)

En grandes infraestructuras corporativas (como bancos o entidades gubernamentales en Colombia), es común encontrar backends principales desarrollados en Java (Spring Boot) o C# (.NET Core):

* **Java / Spring Boot:** Excelente para sistemas transaccionales monolíticos y arquitecturas de microservicios empresariales de alta concurrencia. Sin embargo, para Machine Learning el ecosistema (ej. Weka, Deeplearning4j) es menos flexible y tiene menor dinamismo que Python. La solución corporativa estándar consiste en mantener el core transaccional en Java y consumir los microservicios de IA en Python vía REST o gRPC.
* **C# / .NET Core:** Con la biblioteca ML.NET, Microsoft ofrece integración nativa de modelos supervisados en entornos Windows Server. No obstante, la comunidad científica y la disponibilidad de herramientas de visión, procesamiento de lenguaje natural y explicabilidad siguen teniendo en Python su principal fuente de innovación.

---

## 9. Respuestas Técnicas a las Preguntas de Control de la Guía

Para validar la solidez conceptual del laboratorio y su aplicación al soporte técnico, se resuelven formalmente las seis preguntas de control:

### Pregunta 1: ¿Por qué es necesario usar el mismo `train_test_split` para todos los modelos?

**Respuesta técnica:**  
En el método científico y en la ingeniería de pruebas, para comparar el rendimiento de múltiples tratamientos o algoritmos es obligatorio aislar las variables y mantener condiciones experimentales estrictamente idénticas.

Si cada modelo recibiera una partición diferente de entrenamiento y prueba:
* Un modelo podría recibir por azar un subconjunto de prueba con tickets redactados de forma clara, directa y con términos técnicos explícitos (ej. *"falla en el cable de red utp switch cisco"*), resultando en una exactitud artificialmente elevada.
* Otro modelo podría recibir tickets ambiguos, con errores ortográficos o frases confusas (ej. *"no me deja entrar al sistema ayuda"*), viéndose penalizado injustamente en su métrica.

Al aplicar una única partición fija con `train_test_split(..., test_size=0.25, random_state=42, stratify=y)`, los 250 tickets evaluados son exactamente los mismos para `"logistic"`, `"forest"` y `"mlp"`. Esto garantiza que cualquier diferencia en exactitud, precisión o F1-score provenga exclusivamente de la capacidad matemática del algoritmo para modelar las fronteras de decisión, eliminando el sesgo de partición.

---

### Pregunta 2: ¿Por qué el tiempo de entrenamiento varía entre corridas pero el accuracy no?

**Respuesta técnica:**  
Esta discrepancia responde a la separación fundamental entre la **lógica matemática determinista** del algoritmo y la **naturaleza física y concurrente** del sistema operativo:

1. **Exactitud constante:**  
   Al fijar el hiperparámetro `random_state=42`, todos los generadores pseudoaleatorios inician con la misma semilla:
   * La partición de datos es idéntica.
   * La inicialización de coeficientes y pesos parte de los mismos valores.
   * La selección de características en cada árbol de decisión del bosque sigue el mismo orden pseudoaleatorio.  
   Dado que los datos de entrada y la secuencia de pasos numéricos son idénticos, los modelos convergen exactamente a la misma solución matemática en cada corrida, produciendo predicciones idénticas y, por ende, el mismo valor de exactitud (`accuracy`).

2. **Tiempo de entrenamiento variable:**  
   La medición del tiempo con `time.perf_counter` registra el tiempo de reloj de pared ("wall-clock time") que le toma al procesador ejecutar las instrucciones de máquina. Este tiempo está sujeto a factores externos no deterministas del sistema:
   * **Planificación del kernel de Windows:** El despachador de procesos asigna y retira cuantos de tiempo de CPU a los hilos de Scikit-Learn para atender interrupciones de hardware, servicios de red y programas en segundo plano.
   * **Efectos de caché de CPU (L1/L2/L3):** La primera iteración suele ser ligeramente más lenta ("cold cache") porque los datos deben transferirse desde la memoria RAM. En las corridas siguientes, las estructuras residen en caché, acelerando las instrucciones.
   * **Gestión de energía y calor del procesador:** Tecnologías como Intel Turbo Boost o AMD Precision Boost varían la frecuencia de reloj del procesador según la temperatura interna en rangos de milisegundos.

---

### Pregunta 3: ¿Qué modelo fue el más rápido y cuál el más preciso en los tickets de soporte?

**Respuesta técnica:**  
Con base en los datos certificados en `"artifacts/benchmark.csv"`:

* **El modelo más rápido:**  
  `"logistic"` (`LogisticRegression`), registrando un tiempo de entrenamiento promedio de **`0.0570 s`** (con un mínimo de `0.0496 s`) y una latencia de predicción de tan solo **`0.0665 ms`** por ticket. Fue **7.74 veces más rápido de entrenar** que `"forest"` y **14.17 veces más rápido** que `"mlp"`.
* **El modelo más preciso:**  
  `"forest"` (`RandomForestClassifier`), alcanzando una exactitud del **`94.40 %`** y un macro F1-score del **`94.42 %`**, superando por 0.40% a `"mlp"` (`94.00 %`) y por 0.80% a `"logistic"` (`93.60 %`).

---

### Pregunta 4: ¿En qué escenario del soporte TI preferirías un modelo más rápido sobre uno más preciso?

**Respuesta técnica:**  
En la operación de infraestructura TI existen dos escenarios concretos donde la velocidad y la baja latencia priman sobre un incremento marginal de exactitud:

1. **Triaje interactivo en tiempo real durante la radicación web:**  
   Cuando un usuario final en Bogotá escribe su requerimiento en el portal web (`/portal-usuario`), el sistema debe autocompletar la categoría técnica y sugerir manuales procedimentales de inmediato. Una latencia de predicción sub-milisegundo (`0.0665 ms` en `"logistic"`) garantiza que la interfaz de usuario no sufra bloqueos ni retrasos perceptibles, ofreciendo una experiencia fluida.

2. **Reentrenamiento continuo en caliente ("Online/Active Learning") tras el cierre de turnos:**  
   En mesas de ayuda con miles de tickets mensuales, es una buena práctica técnica reajustar los clasificadores al final del día incorporando los tickets validados por los analistas L2. Con `"logistic"`, el reentrenamiento tarda apenas `0.0570 s`, lo que permite ejecutarlo directamente en la API REST sin degradar el rendimiento del servidor ni requerir ventanas de mantenimiento programadas. En cambio, entrenar un ensamble o una red profunda sobre decenas de miles de registros demandaría minutos de CPU intensiva, aumentando el riesgo de saturación del servidor de producción.

---

### Pregunta 5: ¿Por qué se mide el tiempo de entrenamiento 3 veces en lugar de 1 sola?

**Respuesta técnica:**  
En ingeniería de sistemas y evaluación de desempeño ("benchmarking"), una única medición aislada carece de significancia estadística y es altamente vulnerable al ruido del entorno operativo.

Si se realizara una sola corrida:
* La medición podría coincidir con un pico transitorio de actividad en el sistema operativo (por ejemplo, una sincronización de OneDrive, un análisis de Windows Defender o una ráfaga de red), arrojando un tiempo anormalmente alto ("outlier").
* O podría registrar un valor atípicamente bajo que no refleje el comportamiento representativo del servidor bajo carga normal.

Al ejecutar un mínimo de tres iteraciones independientes:
1. Se calcula la **media aritmética**, obteniendo un estimador central robusto del tiempo de cómputo.
2. Se calcula la **desviación estándar** ($\sigma$), cuantificando la dispersión y la estabilidad temporal del algoritmo.
3. Se identifican los valores **mínimo y máximo**, permitiendo evaluar los escenarios de mejor y peor caso para los Acuerdos de Nivel de Servicio (SLA) del sistema.

---

### Pregunta 6: ¿Cómo influye el tamaño del dataset en la diferencia de tiempos entre modelos lineales y ensambles/redes neuronales?

**Respuesta técnica:**  
El impacto del volumen de datos sobre el tiempo de entrenamiento está determinado por la **complejidad computacional asintótica** de cada familia de algoritmos:

1. **Modelos lineales generalizados (`"LogisticRegression"`):**  
   Tienen una complejidad aproximada de $\mathcal{O}(N \cdot M)$ por iteración del solver, donde $N$ es el número de muestras (tickets) y $M$ es el número de atributos (palabras en el vocabulario). El crecimiento del tiempo frente al incremento de registros es esencialmente lineal. Si el dataset pasa de 1.000 a 100.000 tickets, el tiempo de ajuste pasa de milisegundos a pocos segundos.

2. **Ensambles de árboles de decisión (`"RandomForestClassifier"`):**  
   Para construir cada uno de los $T$ árboles, el algoritmo debe ordenar o evaluar los mejores puntos de corte en un subconjunto de características para cada nodo. La complejidad típica es de $\mathcal{O}(T \cdot M' \cdot N \log N)$. Al crecer $N$, el factor $N \log N$ multiplicado por los 100 árboles provoca que el tiempo crezca mucho más rápido que en los modelos lineales. Con 100.000 tickets, el entrenamiento de un bosque aleatorio puede tardar varios minutos y requerir múltiples núcleos de CPU al 100%.

3. **Redes neuronales artificiales (`"MLPClassifier"`):**  
   La propagación hacia adelante y la retropropagación del error ("backpropagation") requieren múltiples multiplicaciones de matrices en cada época de entrenamiento sobre todas las capas ocultas: $\mathcal{O}(E \cdot N \cdot (M \cdot H_1 + H_1 \cdot H_2 + \dots))$, donde $E$ es el número de épocas y $H_i$ el tamaño de las capas. Si $N$ y el vocabulario aumentan significativamente, el número de operaciones de punto flotante explota, requiriendo aceleración por hardware (GPU/TPU) para mantener tiempos tolerables.

En resumen: a medida que el conjunto de datos de soporte TI crece, la brecha de tiempo a favor del modelo lineal se amplía de manera exponencial, convirtiendo a `"LogisticRegression"` en la alternativa más escalable y sostenible para infraestructura local o servidores en la nube con recursos acotados.

---

## 10. Referencias a Archivos y Artefactos del Repositorio

* Código fuente del benchmark: [`src/semana11_benchmark.py`](file:///c:/Users/User/Music/fundamentos_ai/src/semana11_benchmark.py)
* Suite de pruebas unitarias: [`tests/test_semana11_benchmark.py`](file:///c:/Users/User/Music/fundamentos_ai/tests/test_semana11_benchmark.py)
* Artefacto consolidado principal: [`artifacts/benchmark.csv`](file:///c:/Users/User/Music/fundamentos_ai/artifacts/benchmark.csv)
* Detalle de corridas individuales: [`artifacts/benchmark_corridas.csv`](file:///c:/Users/User/Music/fundamentos_ai/artifacts/benchmark_corridas.csv)
* Evidencia multimodal de imágenes: [`artifacts/benchmark_imagenes.csv`](file:///c:/Users/User/Music/fundamentos_ai/artifacts/benchmark_imagenes.csv)
* Dataset de tickets de soporte TI: [`data/tickets_soporte.csv`](file:///c:/Users/User/Music/fundamentos_ai/data/tickets_soporte.csv)
