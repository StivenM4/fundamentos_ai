# Asistente de Soporte TI - Fundamentos de Inteligencia Artificial

Repositorio del proyecto de la asignatura **Inteligencia Artificial**, enfocado en la formulación, diseño e implementación de un prototipo modular de **Asistente para Operaciones y Soporte de Infraestructura TI**.

El proyecto cubre cuatro capacidades operativas del ciclo de vida de incidentes en una mesa de ayuda corporativa (semanas 02 a 05):
1. **Triaje y clasificación supervisada multietiqueta (Semana 02):** Inferencia atómica simultánea de categoría técnica, nivel de prioridad (SLA) e indicador de incidente sobre texto libre no estructurado.
2. **Taxonomía explicable XAI y motor simbólico (Semana 03):** Diagnóstico declarativo desacoplado que clasifica casos en 7 disciplinas de IA, identifica activadores léxicos (*triggers*), preserva requerimientos multimodales y prescribe una técnica computacional de inicio.
3. **Planificación heurística A\* en grafos ITIL y análisis adversarial (Semana 04):** Búsqueda informada de la secuencia de remediación óptima de costo mínimo bajo restricciones operativas con heurística consistente demostrada, contrastada frente a la toma de decisiones competitiva (Minimax).
4. **Sistema híbrido explicable y trazable con RAG (Semana 05):** Inferencia multinivel sinérgica que articula reglas deterministas (*Fast-Path*), recuperación de información sobre 75 procedimientos técnicos validados, clasificación de dominio supervisada y un guardrail de contención al 20 % para prevenir alucinaciones.

---

## 1. Arquitectura modular y flujo conceptual

Cada módulo aborda un desafío específico del dominio de soporte e infraestructura de TI de forma determinista y modular:

| Módulo | Enfoque de IA | Datos de entrada | Salida técnica / Payload | Función en la operación de soporte |
|---|---|---|---|---|
| **Semana 02: Triaje supervisado** | Machine Learning supervisado (`TF-IDF` + `MultiOutputClassifier` con `LogisticRegression`) | Descripciones en texto libre de `data/tickets_soporte.csv` (1.000 tickets) | Tupla: `(categoría, prioridad, incidente)` | Enrutamiento inmediato al grupo resolutor adecuado y determinación de criticidad de SLA en < 5 ms. |
| **Semana 03: Taxonomía XAI** | Inteligencia Artificial Simbólica y Explicable (*XAI*) basada en reglas declarativas | Casos de `data/casos_ia.csv` (50 casos dorados) y reglas de `data/activadores_taxonomia.json` | Cuádrupla: `(categoría_primaria, áreas_secundarias, triggers, técnica_sugerida)` | Identificación transparente de la rama de IA requerida para solucionar la falla con justificación auditable. |
| **Semana 04: Planificador A\*** | Búsqueda heurística informada en grafos de decisión ITIL ($f(n) = g(n) + h(n)$) | Grafo dirigido de 11 estados, 16 transiciones ponderadas y conjunto de nodos bloqueados | Secuencia ordenada de remediación, costo acumulado en horas y estados explorados | Determinación de la ruta de menor esfuerzo técnico para restablecer el servicio evitando caminos redundantes. |
| **Semana 04: Búsqueda Adversarial** | Teoría de juegos y búsqueda minimax en árboles de decisión de suma cero | Estado de tablero 3x3 en memoria | Evaluación de utilidad ($\{-1, 0, 1\}$) por casilla y mejor jugada para `X` | Demostración comparativa de toma de decisiones bajo competencia estricta frente a fallas estocásticas de TI. |
| **Semana 05: Sistema híbrido** | Sistema híbrido (Reglas expertas + RAG TF-IDF con Similitud Coseno + ML Supervisado) | Consultas técnicas en lenguaje natural y `data/base_conocimiento.txt` (75 manuales) | Cuádrupla de auditoría: `(reglas, evidencia, similitud, clase)` | Remediación guiada libre de alucinaciones con trazabilidad documental completa y validación de dominio. |

---

## 2. Estructura del repositorio

```text
fundamentos_ai/
├── data/
│   ├── activadores_taxonomia.json      # Catálogo declarativo de 123 activadores técnicos (Semana 03)
│   ├── base_conocimiento.txt          # Base formalizada de 75 manuales procedimentales (Semana 05)
│   ├── base_conocimiento_OLD.txt      # Baseline preliminar de 10 manuales (Semana 05)
│   ├── casos_ia.csv                   # 50 casos dorados de evaluación para taxonomía (Semana 03)
│   ├── casos_ia_OLD.csv               # Baseline preliminar de 20 casos (Semana 03)
│   ├── tickets_soporte.csv            # Dataset balanceado de 1.000 tickets de soporte (Semana 02)
│   └── tickets_soporte_antiguo.csv    # Baseline preliminar de 128 tickets (Semana 02)
├── reports/
│   ├── semana02.md                    # Reporte técnico: Clasificación supervisada multietiqueta
│   ├── semana03.md                    # Reporte técnico: Taxonomía XAI y motor simbólico
│   ├── semana04.md                    # Reporte técnico: Planificación A* en grafos ITIL y Minimax
│   └── semana05.md                    # Reporte técnico: Sistema híbrido trazable con RAG
├── src/
│   ├── semana02_fundamentos.py        # Pipeline de vectorización TF-IDF y clasificación multisalida
│   ├── semana03_taxonomia.py          # Motor simbólico de escaneo léxico y clasificación jerárquica
│   ├── semana04_astar.py              # Implementación de A* sobre grafo ITIL con 3 escenarios
│   ├── semana04_minimax.py            # Implementación formal de Minimax sobre tres en línea
│   └── semana05_sistema_hibrido.py    # Pipeline híbrido desacoplado (Reglas + RAG + Clasificador ML)
├── tests/
│   ├── test_semana03_taxonomia.py     # Suite de pruebas unitarias del motor de taxonomía
│   └── test_semana05_sistema_hibrido.py # Suite de pruebas unitarias del sistema híbrido
├── README.md
└── requirements.txt                   # Dependencias de entorno
```

---

## 3. Preparación del entorno y ejecución

### 3.1. Requisitos e instalación
El proyecto requiere **Python 3.10+**. Las dependencias externas se concentran en `pandas` y `scikit-learn` para los pipelines de las semanas 02 y 05; los módulos de las semanas 03 y 04 operan exclusivamente con la biblioteca estándar de Python (`heapq`, `json`, `csv`, `re`, `unicodedata`).

```bash
# Creación y activación de entorno virtual
python3 -m venv .venv
source .venv/bin/activate       # En Windows: .venv\Scripts\activate

# Instalación de dependencias
pip install -r requirements.txt
```

### 3.2. Ejecución directa de los módulos
Cada componente puede ejecutarse de manera independiente desde la raíz del proyecto para validar su inferencia:

```bash
# 1. Pipeline supervisado de triaje (Semana 02)
python3 src/semana02_fundamentos.py

# 2. Motor taxonómico simbólico y explicable (Semana 03)
python3 src/semana03_taxonomia.py

# 3. Planificador A* en grafo ITIL (Semana 04)
python3 src/semana04_astar.py

# 4. Demostración adversarial Minimax (Semana 04)
python3 src/semana04_minimax.py

# 5. Sistema híbrido explicable y trazable (Semana 05)
python3 src/semana05_sistema_hibrido.py
```

### 3.3. Pruebas automatizadas
Para ejecutar la suite completa de pruebas unitarias automatizadas (14 pruebas verificadas):

```bash
python3 -m unittest discover -s tests -v
```

---

## 4. Semana 02: Clasificación supervisada multietiqueta de tickets

### 4.1. Alcance y planteamiento de ingeniería
En una mesa de ayuda corporativa, un ticket reportado en lenguaje natural debe clasificarse de forma instantánea y coherente. El sistema procesa texto libre con abreviaciones, tecnicismos y lenguaje coloquial, entregando de forma simultánea:
* **Categoría funcional:** Dominio de infraestructura afectado (`hardware`, `software`, `red`, `accesos`).
* **Prioridad:** Criticidad técnica vinculada a los acuerdos de nivel de servicio (`alta`, `media`, `baja`).
* **Incidente:** Clasificación binaria que separa una interrupción operativa (`sí`) de un requerimiento administrativo rutinario (`no`).

### 4.2. Evolución del dataset de tickets
Se superó el baseline preliminar de **128 tickets** (`tickets_soporte_antiguo.csv` / `OLD`), cuya reducida representatividad generaba alta varianza y sobreajuste, escalando al dataset de producción de **1.000 tickets estructurados** (`data/tickets_soporte.csv`):

| Parámetro experimental | Baseline preliminar (`OLD`) | Dataset actual de trabajo | Impacto operativo |
|---|---:|---:|---|
| **Archivo fuente** | `tickets_soporte_antiguo.csv` | `tickets_soporte.csv` | Corpus de producción representativo de mesa de ayuda. |
| **Volumen total** | 128 tickets | **1.000 tickets** | Aumento de 7.8x en volumen textual y diversidad léxica. |
| **Entrenamiento (75 %)** | 96 tickets | **750 tickets** | Densificación del vocabulario TF-IDF (*Active Directory, switch, VPN, BSOD*). |
| **Test de validación (25 %)** | 32 tickets | **250 tickets** | Robustez estadística; el peso de cada fallo pasa de 3.125 % a 0.400 %. |
| **Balance de clases** | 32 por categoría | **250 por categoría** | Matriz balanceada para evitar sesgo hacia incidentes frecuentes. |
| **Reproducibilidad** | `random_state=42` | `random_state=42` | Partición estratificada determinista. |

### 4.3. Pipeline del modelo
```python
model = make_pipeline(
    TfidfVectorizer(strip_accents="unicode"),
    MultiOutputClassifier(
        LogisticRegression(
            max_iter=1000,
            random_state=42,
        )
    ),
)
```

### 4.4. Resultados cuantitativos verificados (250 tickets no vistos)

| Dimensión de salida | Métrica de evaluación | Baseline preliminar (`OLD`: 32 test) | Dataset actual (`tickets_soporte.csv`: 250 test) | Delta absoluto ($\Delta$) | Ganancia relativa (%) |
|---|---|---:|---:|---:|---:|
| **Categoría funcional** | Exactitud (*Accuracy*) | 71.9 % | **96.0 %** | **+24.1 p.p.** | **+33.5 %** |
| | Precisión macro | 74.9 % | **96.1 %** | **+21.2 p.p.** | **+28.3 %** |
| | Sensibilidad (*Recall*) | 71.9 % | **96.0 %** | **+24.1 p.p.** | **+33.5 %** |
| | Puntuación F1 macro | 71.3 % | **96.0 %** | **+24.7 p.p.** | **+34.6 %** |
| **Nivel de prioridad** | Exactitud (*Accuracy*) | 84.4 % | **96.0 %** | **+11.6 p.p.** | **+13.7 %** |
| | Precisión macro | 88.9 % | **96.6 %** | **+7.7 p.p.** | **+8.7 %** |
| | Sensibilidad (*Recall*) | 87.2 % | **95.5 %** | **+8.3 p.p.** | **+9.5 %** |
| | Puntuación F1 macro | 85.4 % | **96.0 %** | **+10.6 p.p.** | **+12.4 %** |
| **Detección de incidentes** | Exactitud (*Accuracy*) | 87.5 % | **99.6 %** | **+12.1 p.p.** | **+13.8 %** |
| | Precisión macro | 86.7 % | **99.6 %** | **+12.9 p.p.** | **+14.9 %** |
| | Sensibilidad (*Recall*) | 90.5 % | **99.6 %** | **+9.1 p.p.** | **+10.1 %** |
| | Puntuación F1 macro | 87.0 % | **99.6 %** | **+12.6 p.p.** | **+14.5 %** |

### 4.5. Hallazgos clave de ingeniería
* **Densidad léxica vs complejidad de modelo:** `LogisticRegression` alcanzó un **96.0 % F1 macro** y un **99.6 % en detección de incidentes** sin necesidad de arquitecturas neuronales pesadas.
* **Control de errores en frontera:** En categorías hubo 239 aciertos sobre 250; las 11 discrepancias ocurrieron exclusivamente en la frontera difusa entre hardware y software (fallas físicas reportadas mediante errores de aplicación en pantalla).
* **Consistencia crítica de SLAs:** Cero confusiones entre prioridades opuestas (`Alta` clasificada como `Baja`). En incidentes se obtuvo **100 % de especificidad** (cero falsas alarmas operativas) y **99.2 % de sensibilidad** (123 de 124 incidentes reales capturados).

---

## 5. Semana 03: Taxonomía XAI y motor simbólico explicable

### 5.1. Alcance y planteamiento de ingeniería
Saber que un ticket es de `software` o `red` no indica a ingeniería qué tecnología de IA debe emplearse para su solución. Este motor analiza el requerimiento técnico y determina la disciplina computacional adecuada mediante un modelo simbólico transparente (*XAI*):
1. **Procesamiento de Lenguaje Natural (PLN):** Análisis de texto libre, intención y entidades.
2. **Visión por Computador:** Inspección de capturas de pantalla de error, cableado o luces de rack.
3. **Aprendizaje Predictivo:** Modelado sobre métricas históricas de tickets y demanda técnica.
4. **Sistemas de Recomendación:** Búsqueda y sugerencia de artículos de base de conocimiento y casos previos.
5. **Sistemas Expertos:** Aplicación de árboles de decisión, matrices de impacto/urgencia y políticas de escalamiento.
6. **IA Generativa:** Síntesis y redacción asistida de plantillas de respuesta o resúmenes de cierre.
7. **Robótica y Automatización (RPA):** Despliegue de scripts desatendidos, macros de reinicio y agentes autónomos de remediación.

### 5.2. Evolución del catálogo y dataset
Frente al baseline inicial de **20 casos** (`casos_ia_OLD.csv` / `OLD`), que omitía totalmente la disciplina de **Robótica y RPA**, se construyó el dataset actual de **50 casos dorados** (`data/casos_ia.csv`) con un diccionario externo estructurado en `data/activadores_taxonomia.json`:

| Parámetro experimental | Baseline preliminar (`OLD`) | Dataset actual de trabajo | Impacto técnico |
|---|---:|---:|---|
| **Archivo de casos** | `casos_ia_OLD.csv` | `casos_ia.csv` | Catálogo ampliado de validación. |
| **Casos evaluados** | 20 casos | **50 casos dorados** | Crecimiento del 150 % en casuística técnica. |
| **Disciplinas de IA** | 6 ramas (sin Robótica) | **7 ramas completas** | Cobertura integral incluyendo bots de autorreparación y scripts RPA. |
| **Catálogo de activadores** | 61 términos | **123 activadores únicos** | Incremento de +101.6 % en cobertura léxica técnica especializada. |
| **Detección multimodal** | 8 casos (40.0 %) | **14 casos (28.0 %)** | Identificación precisa de señales secundarias concurrentes. |
| **Efectividad verificada** | 20 / 20 (100 %) | **50 / 50 (100 %)** | Coincidencia exacta con la referencia manual establecida. |

### 5.3. Distribución del corpus evaluado (`casos_ia.csv`)
* **Procesamiento de lenguaje natural:** 10 casos (20.0 %)
* **Visión por computador:** 8 casos (16.0 %)
* **Aprendizaje predictivo:** 7 casos (14.0 %)
* **Sistemas de recomendación:** 7 casos (14.0 %)
* **Sistemas expertos:** 7 casos (14.0 %)
* **IA generativa:** 7 casos (14.0 %)
* **Robótica / RPA:** 4 casos (8.0 %)

### 5.4. Hallazgos clave de ingeniería
* **Multimodalidad operativa (Caso 17):** Un requerimiento de TI rara vez es unidisciplinar. En el Caso 17, el sistema asigna como categoría primaria PLN (`texto`, `clasificar`, `ticket`), pero preserva como áreas secundarias **Visión por computador**, **Sistemas de recomendación** y **Robótica**, permitiendo detonar múltiples capacidades sin truncar la causa raíz.
* **Desacoplamiento de reglas:** La separación de los 123 activadores en `activadores_taxonomia.json` permite a los administradores L2 incorporar nuevo léxico de software o hardware sin modificar código ejecutable en Python.
* **Trazabilidad auditable:** Cada inferencia retorna la lista exacta de *triggers* que motivaron la decisión, facilitando la auditoría técnica frente a modelos de caja negra.

---

## 6. Semana 04: Planificación heurística A* en grafos ITIL y análisis adversarial

### 6.1. Alcance y planteamiento de ingeniería
Resolver un incidente en infraestructura bajo normas ITIL exige optimizar el uso de horas de ingeniería técnica. El algoritmo $A^*$ evalúa en cada paso la función $f(n) = g(n) + h(n)$, donde $g(n)$ representa el costo real acumulado de las acciones ejecutadas y $h(n)$ es la cota optimista de esfuerzo restante hasta alcanzar `incidente_resuelto`.

### 6.2. Modelado del espacio de estados y costos
Se evolucionó de un flujo lineal estático de 4 pasos (`OLD`) a un grafo dirigido ponderado de **11 estados y 16 transiciones** que refleja flujos reales de soporte:

| Dimensión de búsqueda | Cuadrícula 2D canónica | Planificador de Soporte ITIL (`SUPPORT_GRAPH`) | Justificación de ingeniería |
|---|---|---|---|
| **Definición de estado** | Coordenada espacial `(x, y)`. | Fase procedimental del ciclo de vida del incidente. | Modela transiciones técnicas formales de ITIL. |
| **Origen y Meta** | `(0, 0)` $\rightarrow$ `(4, 4)`. | `ticket_clasificado` $\rightarrow$ `incidente_resuelto`. | Triaje inicial como partida; validación técnica como cierre. |
| **Costos de transición** | Homogéneo ($c = 1$). | Heterogéneo ponderado (1 a 6 horas de esfuerzo técnico). | Reiniciar un servicio cuesta 2; escalar a ingeniería L3 cuesta 6. |
| **Restricciones** | Paredes de cuadrícula. | Nodos bloqueados condicionalmente (`blocked_set`). | Simula impedimentos reales (ej. no hay backups para rollback). |
| **Heurística $h(n)$** | Distancia Manhattan. | Estimación admisible y consistente calculada por esfuerzo inverso. | Garantiza optimalidad matemática podando caminos costosos. |

### 6.3. Consistencia heurística demostrada
Para evitar reabrir nodos cerrados y asegurar la convergencia en tiempo óptimo, la heurística cumple la condición de monotonicidad $h(u) \le c(u, v) + h(v)$ en todas las transiciones:

| Estado del grafo | Heurística $h(n)$ | Cota optimista restante | Condición de consistencia ($h(u) \le c(u, v) + h(v)$) |
|---|---:|---|---|
| `incidente_resuelto` | 0 | Estado meta alcanzado. | $0 \le 0$ (Consistente) |
| `validar_servicio` | 1 | Un paso de costo 1 hacia la meta. | $1 \le 1 + 0 = 1$ (Consistente) |
| `aplicar_solucion_conocida` | 2 | Costo 1 hacia `validar_servicio` ($1 + 1 = 2$). | $2 \le 1 + 1 = 2$ (Consistente) |
| `revertir_cambio` | 2 | Costo 1 hacia `validar_servicio` ($1 + 1 = 2$). | $2 \le 1 + 1 = 2$ (Consistente) |
| `ajustar_configuracion` | 2 | Costo 1 hacia `validar_servicio` ($1 + 1 = 2$). | $2 \le 1 + 1 = 2$ (Consistente) |
| `reiniciar_componente` | 3 | Costo 2 hacia `validar_servicio` ($2 + 1 = 3$). | $3 \le 2 + 1 = 3$ (Consistente) |
| `escalar_especialista` | 3 | Costo 2 hacia `validar_servicio` ($2 + 1 = 3$). | $3 \le 2 + 1 = 3$ (Consistente) |
| `consultar_base_conocimiento` | 4 | Costo 2 hacia `aplicar_solucion` ($2 + 2 = 4$). | $4 \le 2 + 2 = 4$ (Consistente) |
| `verificar_cambio_reciente` | 5 | Costo 3 hacia `revertir_cambio` ($3 + 2 = 5$). | $5 \le 3 + 2 = 5$ (Consistente) |
| `diagnostico_guiado` | 5 | $\min(2+3, 3+2, 6+3) = 5$. | $5 \le 2 + 3 = 5$ (Consistente) |
| `ticket_clasificado` | 6 | Costo 2 hacia `consultar_base` ($2 + 4 = 6$). | $6 \le 2 + 4 = 6$ (Consistente) |

### 6.4. Evaluación sobre escenarios operacionales

| Escenario operacional | Condición de entorno | Secuencia óptima calculada por $A^*$ | Costo ($g$) | Nodos explorados | Eficiencia |
|---|---|---|---:|---:|---|
| **Escenario 1: Solución conocida disponible** | Grafo estándar sin restricciones. | `ticket_clasificado` $\rightarrow$ `consultar_base_conocimiento` $\rightarrow$ `aplicar_solucion_conocida` $\rightarrow$ `validar_servicio` $\rightarrow$ `incidente_resuelto` | **6 horas** | **5 / 11** | Poda del 54.5 % del grafo; mínimo esfuerzo operativo. |
| **Escenario 2: Cambio reciente / Rollback** | Solución conocida costosa o actualización reportada. | `ticket_clasificado` $\rightarrow$ `verificar_cambio_reciente` $\rightarrow$ `revertir_cambio` $\rightarrow$ `validar_servicio` $\rightarrow$ `incidente_resuelto` | **7 horas** | **6 / 11** | Reenrutamiento automático ante penalización de costo. |
| **Escenario 3: Incidente crítico L3** | Procedimientos de L1 bloqueados (`aplicar`, `revertir`, `reiniciar`, `ajustar`). | `ticket_clasificado` $\rightarrow$ `diagnostico_guiado` $\rightarrow$ `escalar_especialista` $\rightarrow$ `validar_servicio` $\rightarrow$ `incidente_resuelto` | **12 horas** | **7 / 11** | Derivación controlada a ingeniería especializada sin ciclos. |

### 6.5. Análisis contrastivo: Búsqueda adversarial (Minimax)
* **Entorno de prueba (Tres en línea):** En un juego de suma cero con tablero 3x3, Minimax evalúa todas las hojas terminales maximizando la utilidad de `X` ($+1$) y minimizando la de `O` ($-1$).
  * En el tablero de referencia (`['X', 'O', 'X', 'O', 'X', ' ', ' ', ' ', 'O']`), evalúa `{5: 0, 6: 1, 7: 0}`, seleccionando de forma óptima la casilla **6** para ganar.
  * En el tablero de bloqueo (`['X', ' ', ' ', 'O', 'O', ' ', ' ', ' ', 'X']`), evalúa `{2: 1, 5: 0, 6: -1, 7: -1, 8: -1}`, seleccionando la casilla **2** para evitar la derrota.
* **Incompatibilidad técnica con soporte de TI:** Minimax asume la existencia de un contrincante racional malévolo enfocado activamente en perjudicar al operador. En infraestructura de TI, las averías de hardware, caídas de enlace y errores de software son **eventos estocásticos del entorno**, no decisiones de un adversario de suma cero. Modelar un servidor caído mediante Minimax llevaría a un sobrecosto irracional al asumir siempre el peor escenario intencionado.

---

## 7. Semana 05: Sistema híbrido de soporte TI con trazabilidad integral

### 7.1. Alcance y arquitectura híbrida desacoplada
En operaciones reales de TI, delegar la resolución de incidentes exclusivamente a modelos generativos masivos (*LLMs*) introduce dos riesgos críticos: **alucinación de comandos técnicos** (parámetros de consola inventados o destructivos) y **falta de auditoría** ante incumplimientos de SLAs.

El módulo implementado en `src/semana05_sistema_hibrido.py` sustituye este riesgo articulando de forma sinérgica cuatro capas de inferencia:
1. **Reglas expertas (Fast-Path):** Evaluación determinista en milisegundos mediante funciones condicionales para acciones inmediatas sobre incidentes de alta recurrencia (`revisar_ventilacion`, `revisar_conectividad`, `revisar_acceso`, `revisar_software`, `revisar_pantalla`, `revisar_impresion`).
2. **Base de conocimiento procedimental:** 75 manuales técnicos homologados en `data/base_conocimiento.txt`, organizados equitativamente entre las cuatro áreas operativas.
3. **Recuperación de información (RAG):** Vectorización TF-IDF con 56 stop words depuradas en español y similitud coseno para extraer el procedimiento exacto más afín a la consulta no estructurada.
4. **Clasificación supervisada independiente:** Pipeline con `LogisticRegression` que corrobora de forma estadística el dominio funcional (`hardware`, `software`, `red`, `accesos`).

### 7.2. Evolución de la base documental procedimental
Frente al baseline preliminar de **10 artículos** (`data/base_conocimiento_OLD.txt` / `OLD`), se estructuró la base de producción de **75 manuales procedimentales** (`data/base_conocimiento.txt`), eliminando falsos positivos graves de recuperación:

| Parámetro experimental | Baseline preliminar (`OLD`) | Base procedimental actual | Impacto operativo |
|---|---:|---:|---|
| **Archivo fuente** | `base_conocimiento_OLD.txt` | `base_conocimiento.txt` | Base técnica de producción del asistente. |
| **Volumen de manuales** | 10 artículos breves | **75 manuales procedimentales** | Multiplicación de 7.5x en cobertura técnica corporativa. |
| **Balance temático** | 2 a 3 manuales por área | **~19 manuales por categoría** | Cobertura homogénea en *Hardware, Red, Software y Accesos*. |
| **Stop words en español** | Genéricas | **56 stop words optimizadas** | Elimina términos neutros que distorsionaban el ángulo del coseno. |
| **Reglas expertas** | 5 lambdas simples | **5 reglas estandarizadas** | Respuestas deterministas inmediatas en milisegundos. |
| **Ejemplos de ML supervisado** | 15 muestras | **15 muestras representativas** | Validación cruzada del dominio tecnológico del ticket. |

### 7.3. Mitigación de casos de borde críticos
En la base preliminar (`OLD`), al no existir manuales de infraestructura central de red, una consulta como *"Falla en el switch del rack principal y perdida de enlace troncal"* producía un **falso positivo grave**: el sistema asociaba erróneamente la palabra "enlace" a un procedimiento de *cliente VPN intermitente* (Similitud: 0.362).

En la base actual de 75 manuales, el motor recupera con exactitud el procedimiento requerido: *"Si el enlace troncal de fibra óptica o conexión WAN principal se cae..."* (Similitud: **0.372**), erradicando la recomendación errónea.

### 7.4. Cuádrupla de trazabilidad en consultas evaluadas

```python
# Payload estructurado de auditoría retornado por answer()
{
    "reglas": fired_rules,       # Reglas expertas detonadas (Fast-Path)
    "evidencia": best_doc,       # Fragmento literal del manual recuperado
    "similitud": cosine_score,   # Puntuación continua de afinidad semántica
    "clase": predicted_label     # Dominio corroborado por el clasificador ML
}
```

| Consulta técnica ingresada | Regla detonada | Similitud | Dominio predicho | Procedimiento técnico homologado recuperado |
|---|---|---:|:---:|---|
| *El equipo esta muy caliente y el ventilador hace ruido* | `revisar_ventilacion` | 36.2 % | `hardware` | Desarmar disipador, sopletear polvo, aplicar pasta térmica Artic MX-4 y auditar RPM en BIOS. |
| *Internet se cae y aparece error de conexion DNS* | `revisar_conectividad` | 53.0 % | `red` | Ejecutar `ipconfig /flushdns`, verificar servidores DNS corporativos y probar con `nslookup`. |
| *No puedo iniciar sesion con mi cuenta bloqueada* | `revisar_acceso` | 26.7 % | `accesos` | Desbloqueo mediante Active Directory Users and Computers o PowerShell `Unlock-ADAccount`. |
| *Excel se cierra de golpe con un error de memoria* | `revisar_software` | 38.1 % | `software` | Abrir en `excel /safe`, cambiar cálculo a manual y auditar bucles en macros VBA. |

### 7.5. Hallazgos clave de ingeniería
* **Guardrail de contención al 20 %:** Consultas ajenas a TI (ej. instrumental médico o fallas industriales) caen por debajo del umbral de corte del 20 % en similitud coseno, impidiendo que el sistema recomiende procedimientos inadecuados.
* **Cero alucinaciones operativas:** Al restringir la evidencia al catálogo formalizado, el analista L1/L2 recibe instrucciones técnicas verificadas, sin parámetros de comandos inventados.
* **Auditoría ITIL completa:** La trazabilidad cuádruple permite certificar ante auditorías internas el origen de cada recomendación técnica.

---

## 8. Conclusiones y balance general de ingeniería (Semanas 02 a 05)

* **Complementariedad de paradigmas de IA:** La operación de una mesa de ayuda moderna requiere combinar múltiples enfoques. El Machine Learning supervisado (Semana 02) aporta triaje atómico en milisegundos; el motor simbólico XAI (Semana 03) clasifica la tecnología de IA requerida con explicación causal; la búsqueda informada $A^*$ (Semana 04) optimiza la ruta de remediación minimizando horas de soporte bajo normas ITIL; y el sistema híbrido RAG (Semana 05) garantiza remediación libre de alucinaciones anclada a manuales validados.
* **Gobierno y calidad del dato como factor determinante:** La robustez de los cuatro módulos se consolidó al migrar de conjuntos preliminares a datasets representativos: 1.000 tickets balanceados, 50 casos dorados con 123 activadores, un grafo con heurística consistente comprobada y 75 manuales técnicos procedimentales.
* **Trazabilidad y validación como estándares de soporte corporativo:** Tanto en la planificación ($A^*$, donde el paso `validar_servicio` es obligatorio antes del cierre) como en la resolución híbrida (con cuádruplas auditables y guardrail al 20 %), el diseño prioriza la seguridad operativa, la transparencia y el cumplimiento estricto de SLAs.
