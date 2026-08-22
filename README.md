# Inteligencia Artificial

Proyecto acumulativo de la asignatura Inteligencia Artificial.

## Semana 02

Configuración del entorno de trabajo y creación del primer modelo de clasificación supervisada.

### Tecnologías

- Python 3.13
- scikit-learn
- NumPy
- Pandas
- Matplotlib
- Jupyter

## Semana 03

Construcción de un motor de taxonomía de problemas de Inteligencia Artificial
aplicado al proyecto acumulativo **Asistente de soporte TI híbrido y
multimodal**.

El motor procesa 20 casos del dominio, identifica una categoría principal y
áreas secundarias, explica las palabras o frases que activaron cada regla y
recomienda una técnica inicial. Esta versión basada en reglas funciona como
línea base para futuros modelos propios de texto e imágenes.

### Estructura añadida

```text
data/casos_ia.csv
reports/semana03.md
reports/semana03_ejecucion.txt
src/semana03_taxonomia.py
tests/test_semana03_taxonomia.py
```

### Ejecución

Desde la raíz del repositorio y con el entorno virtual activo:

```powershell
python src/semana03_taxonomia.py
python -m unittest discover -s tests -v
```

El primer comando genera nuevamente el reporte y la evidencia de ejecución. El
segundo ejecuta las seis pruebas automáticas de la práctica.
