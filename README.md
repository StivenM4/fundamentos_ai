# Inteligencia Artificial

Proyecto acumulativo de la asignatura Inteligencia Artificial.

## Semana 02

Primer modelo de clasificación supervisada aplicado al proyecto acumulativo
**Asistente de soporte TI**. El modelo deja de usar Iris: recibe el texto de un
ticket y predice su categoría, prioridad y si es un incidente o una solicitud.

La práctica incluye 128 tickets sintéticos etiquetados, una separación
reproducible de entrenamiento (75 %) y prueba (25 %), y métricas de accuracy,
precisión, recall, F1 macro y matrices de confusión.


### Archivos

```text
data/tickets_soporte.csv
reports/semana02.md
src/semana02_fundamentos.py
```

### Tecnologías

- Python 3.13
- scikit-learn
- NumPy
- Pandas
- Matplotlib
- Jupyter

## Semana 03

Construcción de un motor de taxonomía de problemas de Inteligencia Artificial
aplicado al proyecto acumulativo **Asistente de soporte TI**.

El motor procesa 20 casos del dominio, identifica una categoría principal y
áreas secundarias, explica las palabras o frases que activaron cada regla y
recomienda una técnica inicial. Esta versión basada en reglas funciona como
complemento explicable del modelo supervisado de texto de la Semana 02 y como
línea base para futuros modelos de imágenes.

### Estructura añadida

```text
data/casos_ia.csv
reports/semana03.md
src/semana03_taxonomia.py
tests/test_semana03_taxonomia.py
```
