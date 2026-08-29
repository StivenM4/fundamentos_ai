# Inteligencia Artificial

Proyecto acumulativo de la asignatura Inteligencia Artificial aplicado a la
idea **Asistente de soporte TI**.

El repositorio reúne las prácticas de las semanas 02, 03 y 04. Cada semana
aborda una capacidad diferente del dominio: clasificación supervisada de
tickets, taxonomía explicable de problemas de IA y búsqueda de una secuencia de
atención de costo mínimo.

## Objetivo del proyecto

Desarrollar de forma acumulativa un prototipo académico de asistencia para
soporte TI. Con los componentes implementados hasta la Semana 04, el proyecto
permite estudiar tres partes del problema: clasificar la descripción de un
ticket, reconocer qué áreas y técnicas de IA se relacionan con diferentes casos
del dominio, y buscar una ruta de atención de costo mínimo en un grafo de
decisiones.

El repositorio demuestra estos conceptos con datos, reglas, costos y escenarios
predefinidos. No corresponde todavía a una aplicación operativa conectada a una
mesa de ayuda real.

## Alcance actual

El proyecto contiene tres implementaciones académicas:

1. Un clasificador supervisado que recibe el texto de un ticket y predice su
   categoría, prioridad y condición de incidente.
2. Un motor de reglas que clasifica casos del dominio en áreas de IA, conserva
   las frases que activaron la decisión y recomienda una técnica inicial.
3. Un planificador A* que parte de un ticket considerado previamente
   clasificado y busca una ruta de atención hasta resolver el incidente.

Los módulos se relacionan por el dominio y por su planteamiento, pero todavía
no forman un único flujo automático. El motor de la Semana 03 no llama al
modelo de la Semana 02 y el planificador de la Semana 04 no consume directamente
sus predicciones. Minimax se conserva como una práctica independiente sobre un
problema adversarial de tres en línea; no se utiliza para resolver tickets.

### Flujo conceptual actual

| Componente | Entrada real del módulo | Salida real del módulo | Relación con el proyecto |
|---|---|---|---|
| Semana 02 | Texto de `data/tickets_soporte.csv` | Categoría, prioridad e indicador de incidente | Clasificación supervisada del ticket |
| Semana 03 | Descripciones de `data/casos_ia.csv` | Categoría principal, áreas secundarias, activadores y técnica inicial | Taxonomía explicable de casos de IA relacionados con soporte |
| Semana 04: A* | Grafo, costos y estados bloqueados definidos en el script | Ruta, costo total y cantidad de estados explorados | Planificación de una secuencia de atención |
| Semana 04: Minimax | Un tablero de tres en línea | Utilidad de cada jugada disponible y mejor posición para `X` | Demostración independiente de búsqueda adversarial |

## Relación entre semanas

| Semana | Problema abordado | Implementación | Resultado principal |
|---|---|---|---|
| 02 | Clasificar tickets de soporte a partir de texto | TF-IDF, regresión logística y clasificación multisalida | Predicción de categoría, prioridad e incidente |
| 03 | Identificar áreas de IA presentes en casos de soporte | Reglas transparentes de palabras y frases clave | Categoría principal, áreas secundarias, activadores y técnica inicial |
| 04 | Seleccionar una secuencia de atención con costos y restricciones | Búsqueda informada A* | Ruta de costo mínimo desde `ticket_clasificado` hasta `incidente_resuelto` |

## Estructura relevante

```text
fundamentos_ai/
├── data/
│   ├── casos_ia.csv
│   └── tickets_soporte.csv
├── reports/
│   ├── semana02.md
│   ├── semana03.md
│   ├── semana03_ejecucion.txt
│   └── semana04.md
├── src/
│   ├── semana02_fundamentos.py
│   ├── semana03_taxonomia.py
│   ├── semana04_astar.py
│   └── semana04_minimax.py
├── tests/
│   ├── test_semana03_taxonomia.py
│   └── test_semana04_busqueda_juegos.py
├── README.md
└── requirements.txt
```

## Requisitos y preparación

Los comandos siguientes se ejecutan desde la raíz `fundamentos_ai` y utilizan
`python3`, nombre habitual del ejecutable en macOS.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pandas scikit-learn
```

Las dependencias externas importadas directamente por el código se concentran
en la Semana 02:

- `pandas` para cargar `data/tickets_soporte.csv`.
- `scikit-learn` para vectorizar el texto, entrenar los clasificadores y
  calcular las métricas.

Las implementaciones de las semanas 03 y 04 usan la biblioteca estándar de
Python. El archivo `requirements.txt` conserva el listado versionado del
entorno incluido en el repositorio.

## Ejecución del proyecto

Cada módulo se ejecuta por separado desde la raíz `fundamentos_ai`:

```bash
python3 src/semana02_fundamentos.py
python3 src/semana03_taxonomia.py
python3 src/semana04_astar.py
python3 src/semana04_minimax.py
```

Estos comandos no conforman una tubería automática. Su ejecución consecutiva
permite reproducir las prácticas, pero un script no entrega todavía su resultado
al siguiente.

## Semana 02: clasificación supervisada

`src/semana02_fundamentos.py` carga 128 tickets etiquetados desde
`data/tickets_soporte.csv`. Cada registro contiene:

- `texto`: descripción del ticket.
- `categoria`: `hardware`, `software`, `red` o `accesos`.
- `prioridad`: `alta`, `media` o `baja`.
- `incidente`: `si` o `no`.

Los datos se separan de manera reproducible en 96 muestras de entrenamiento y
32 de prueba, con `random_state=42` y estratificación por categoría. El pipeline
combina `TfidfVectorizer`, `MultiOutputClassifier` y
`LogisticRegression`.

### Resultados verificados

| Salida | Accuracy | Precisión macro | Recall macro | F1 macro |
|---|---:|---:|---:|---:|
| Categoría | 0.719 | 0.749 | 0.719 | 0.713 |
| Prioridad | 0.844 | 0.889 | 0.872 | 0.854 |
| Incidente | 0.875 | 0.867 | 0.905 | 0.870 |

### Ejecución

```bash
python3 src/semana02_fundamentos.py
```

El análisis completo, incluidas las matrices de confusión y las limitaciones
del conjunto de datos, se encuentra en `reports/semana02.md`.

## Semana 03: taxonomía explicable

`src/semana03_taxonomia.py` procesa los 20 casos de `data/casos_ia.csv`. El
motor normaliza el texto y aplica reglas de palabras o frases clave para
identificar una categoría principal entre siete áreas de IA:

- Procesamiento de lenguaje natural.
- Visión por computador.
- Aprendizaje predictivo.
- Sistemas de recomendación.
- Sistemas expertos.
- IA generativa.
- Robótica.

Además de la categoría principal, conserva las áreas secundarias, los
activadores encontrados, los puntajes por categoría y una técnica inicial
asociada a la clasificación.

La ejecución actual clasifica los 20 casos y obtiene 20 coincidencias frente a
la referencia manual definida en el módulo. Esta comparación valida el conjunto
de casos de la práctica; no representa una medición sobre tickets reales.

### Ejecución

```bash
python3 src/semana03_taxonomia.py
```

El comando muestra los resultados y vuelve a generar:

- `reports/semana03.md`.
- `reports/semana03_ejecucion.txt`.

## Semana 04: búsqueda informada y juegos

### A* aplicado al soporte TI

`src/semana04_astar.py` representa la atención como un grafo de 11 estados y
16 transiciones. Los costos son unidades relativas de esfuerzo y la heurística
estima de forma optimista el costo restante hasta `incidente_resuelto`.

Se implementaron y verificaron tres escenarios:

| Caso | Decisión obtenida | Costo | Estados explorados |
|---|---|---:|---:|
| Solución conocida disponible | Consultar la base de conocimiento y aplicar la solución conocida | 6 | 5 |
| Solución conocida costosa | Verificar y revertir un cambio reciente | 7 | 6 |
| Incidente complejo con restricciones | Ejecutar diagnóstico y escalar al especialista | 12 | 7 |

La prueba automatizada también verifica la consistencia de la heurística en
cada transición del grafo.

### Minimax como práctica independiente

`src/semana04_minimax.py` implementa Minimax para tres en línea. El jugador `X`
maximiza una utilidad de `1`, el jugador `O` la minimiza y un empate tiene
utilidad `0`.

| Tablero | Utilidades por posición disponible | Mejor posición para `X` |
|---|---|---:|
| Referencia | `{5: 0, 6: 1, 7: 0}` | 6 |
| Modificado | `{2: 1, 5: 0, 6: -1, 7: -1, 8: -1}` | 2 |

### Ejecución

```bash
python3 src/semana04_astar.py
python3 src/semana04_minimax.py
```

La formulación, las rutas completas, la evidencia de ejecución y las
limitaciones se documentan en `reports/semana04.md`.

## Pruebas automatizadas

Desde la raíz del proyecto:

```bash
python3 -m unittest discover -s tests -v
```

La suite contiene 12 pruebas y cubre:

- Normalización y clasificación del motor de taxonomía.
- Carga de los 20 casos y comparación con su referencia manual.
- Las tres rutas esperadas de A* y sus costos.
- Consistencia de la heurística de A*.
- Las decisiones de Minimax en los dos tableros incluidos.

La ejecución verificada finaliza con las 12 pruebas aprobadas. Actualmente no
hay una prueba automatizada específica para el clasificador de la Semana 02;
sus resultados se obtienen al ejecutar el script correspondiente.

## Alcance de los resultados

Las métricas y decisiones incluidas en este README fueron reproducidas con los
archivos presentes en el repositorio. El 20/20 de la Semana 03 mide coincidencia
con la referencia manual definida para esos mismos 20 casos; no es una métrica
de generalización. De igual forma, las rutas de la Semana 04 son óptimas dentro
del grafo y los costos configurados en `semana04_astar.py`, no frente a un
proceso real de soporte.

## Limitaciones actuales

- Los 128 tickets de la Semana 02 son datos sintéticos y el conjunto es pequeño
  para representar una operación real de soporte.
- El motor de la Semana 03 depende de coincidencias literales; no comprende
  sinónimos, negaciones ni el contexto completo de una descripción.
- El planificador de la Semana 04 utiliza un grafo y costos definidos para la
  demostración académica, no tiempos históricos ni valores de SLA.
- A* supone que cada acción conduce al estado indicado y no modela la
  probabilidad de fallo.
- Los scripts de las tres semanas todavía se ejecutan por separado.
- El repositorio no incluye interfaz gráfica, API, base de datos ni conexión con
  una plataforma real de gestión de tickets.
