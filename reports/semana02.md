# Semana 02: clasificación supervisada de tickets de soporte TI

## Objetivo

Adaptar el primer modelo de clasificación supervisada al proyecto acumulativo **Asistente de soporte TI**. En lugar de clasificar flores del conjunto Iris, el modelo recibe el texto de un ticket y predice tres datos útiles para soporte:

- **Categoría:** hardware, software, red o accesos.
- **Prioridad:** alta, media o baja.
- **Incidente:** sí o no.

## Cambios frente al ejemplo Iris

El flujo original se conserva: cargar datos, separar entrenamiento y prueba, crear un pipeline, entrenar con `fit`, predecir con `predict` y evaluar los resultados.

| Ejemplo Iris | Proyecto de soporte TI |
|---|---|
| `load_iris()` | `pandas.read_csv()` |
| Cuatro medidas numéricas de flores | Texto libre del ticket |
| `StandardScaler` | `TfidfVectorizer` |
| Una especie de flor | Categoría, prioridad e incidente |
| Regresión logística | Regresión logística multisalida |

TF-IDF es necesario porque la regresión logística no procesa texto directamente. Esta transformación convierte las palabras de cada ticket en valores numéricos.

## Datos

Se emplea el archivo `data/tickets_soporte.csv`, que contiene **128 tickets etiquetados**

Los datos se dividieron de manera reproducible usando `random_state=42`:

- Entrenamiento: **96 tickets (75 %)**.
- Prueba: **32 tickets (25 %)**.

La división se estratificó por categoría para conservar ejemplos de hardware, software, red y accesos en el conjunto de prueba.

## Modelo

El pipeline utiliza:

1. `TfidfVectorizer` para representar el texto numéricamente.
2. `MultiOutputClassifier` para administrar las tres salidas.
3. `LogisticRegression` como clasificador supervisado de cada salida.

## Resultados sobre el conjunto de prueba

| Salida | Accuracy | Precisión macro | Recall macro | F1 macro |
|---|---:|---:|---:|---:|
| Categoría | 0.719 | 0.749 | 0.719 | 0.713 |
| Prioridad | 0.844 | 0.889 | 0.872 | 0.854 |
| Incidente | 0.875 | 0.867 | 0.905 | 0.870 |

### Matriz de confusión: categoría

Las filas representan la etiqueta real y las columnas la predicción.

| Real \ Predicción | accesos | hardware | red | software |
|---|---:|---:|---:|---:|
| accesos | 7 | 0 | 0 | 1 |
| hardware | 2 | 4 | 2 | 0 |
| red | 0 | 1 | 7 | 0 |
| software | 3 | 0 | 0 | 5 |

### Matriz de confusión: prioridad

| Real \ Predicción | alta | baja | media |
|---|---:|---:|---:|
| alta | 9 | 0 | 0 |
| baja | 0 | 8 | 5 |
| media | 0 | 0 | 10 |

### Matriz de confusión: incidente

| Real \ Predicción | no | sí |
|---|---:|---:|
| no | 17 | 4 |
| sí | 0 | 11 |

## Interpretación

El modelo presenta su mejor resultado al identificar incidentes y su mayor dificultad al distinguir categorías con vocabulario parecido. Las métricas provienen únicamente de los 32 tickets reservados para prueba, que no participaron en el entrenamiento.

Este conjunto es suficiente para demostrar el procedimiento de la Semana 02, pero todavía es pequeño. Para una aplicación real se necesitarían más tickets históricos anonimizados y etiquetas revisadas por el equipo de soporte.

