# Semana 03: taxonomía de problemas de IA para soporte TI

## Objetivo y dominio

Este motor clasifica problemas del asistente de soporte TI en siete áreas de IA y recomienda una técnica inicial. El proyecto acumulativo busca evolucionar esta línea base hacia modelos propios que analicen texto e imágenes, clasifiquen tickets y recuperen soluciones de casos anteriores.

## Resultados

Se procesaron **20 casos**. Coincidencia con la referencia manual: **20/20 (100%)**.

| Caso | Categoría principal | Áreas secundarias | Palabras o frases activadoras | Técnica inicial |
|---:|---|---|---|---|
| 1 | Procesamiento de lenguaje natural | Ninguna | `texto`, `clasificar`, `tickets` | clasificador de texto con TF-IDF y regresión logística |
| 2 | Visión por computador | Ninguna | `reconocer`, `captura de pantalla`, `pantallazo` | red convolucional o modelo de visión preentrenado |
| 3 | Aprendizaje predictivo | Ninguna | `predecir`, `caso recurrente` | clasificación o regresión supervisada con datos históricos |
| 4 | Sistemas de recomendación | Ninguna | `recomendar`, `casos resueltos`, `base de conocimiento`, `solucion similar` | recuperación por similitud semántica de casos resueltos |
| 5 | Sistemas expertos | Procesamiento de lenguaje natural | `impacto`, `urgencia`, `sla` | motor de reglas con criterios de impacto, urgencia y SLA |
| 6 | IA generativa | Ninguna | `generar`, `redactar` | modelo generativo con recuperación de conocimiento y revisión humana |
| 7 | Procesamiento de lenguaje natural | Ninguna | `descripcion textual`, `intencion`, `entidades` | clasificador de texto con TF-IDF y regresión logística |
| 8 | Aprendizaje predictivo | Procesamiento de lenguaje natural, Sistemas expertos | `pronosticar`, `probabilidad`, `tiempo de resolucion` | clasificación o regresión supervisada con datos históricos |
| 9 | Visión por computador | Ninguna | `imagen`, `inspeccionar` | red convolucional o modelo de visión preentrenado |
| 10 | Sistemas de recomendación | Ninguna | `recomendar`, `tecnico adecuado`, `ruta de escalamiento`, `soluciones similares` | recuperación por similitud semántica de casos resueltos |
| 11 | Sistemas expertos | Ninguna | `reglas de diagnostico`, `restablecer la contrasena` | motor de reglas con criterios de impacto, urgencia y SLA |
| 12 | IA generativa | Ninguna | `generativo`, `crear pasos` | modelo generativo con recuperación de conocimiento y revisión humana |
| 13 | Procesamiento de lenguaje natural | Ninguna | `texto`, `extraer`, `ticket`, `mensaje de error` | clasificador de texto con TF-IDF y regresión logística |
| 14 | Aprendizaje predictivo | Procesamiento de lenguaje natural | `predecir`, `anticipar`, `demanda` | clasificación o regresión supervisada con datos históricos |
| 15 | Visión por computador | Ninguna | `visual`, `reconocer`, `interfaz`, `captura de pantalla` | red convolucional o modelo de visión preentrenado |
| 16 | Sistemas de recomendación | Ninguna | `recomendar`, `sugerir`, `articulo`, `casos resueltos`, `base de conocimiento` | recuperación por similitud semántica de casos resueltos |
| 17 | Procesamiento de lenguaje natural | Visión por computador, Sistemas de recomendación, Robótica | `texto`, `clasificar`, `ticket` | clasificador de texto con TF-IDF y regresión logística |
| 18 | Sistemas expertos | Ninguna | `diagnosticar`, `prioridad`, `impacto`, `urgencia`, `sla` | motor de reglas con criterios de impacto, urgencia y SLA |
| 19 | IA generativa | Procesamiento de lenguaje natural | `generar`, `redactar` | modelo generativo con recuperación de conocimiento y revisión humana |
| 20 | Procesamiento de lenguaje natural | Visión por computador, Sistemas de recomendación | `texto`, `ticket` | clasificador de texto con TF-IDF y regresión logística |

## Cinco reglas propias del dominio

1. **Visión por computador — `captura de pantalla`, `pantallazo`:** permite interpretar la evidencia visual que el usuario adjunta al ticket.
2. **Procesamiento de lenguaje natural — `ticket`, `incidente`, `mensaje de error`:** representa el texto libre que debe entender y clasificar el asistente.
3. **Aprendizaje predictivo — `caso recurrente`, `reincidencia`:** sirve para anticipar fallas repetitivas usando el historial de soporte.
4. **Sistemas de recomendación — `caso resuelto`, `base de conocimiento`, `solución similar`:** conecta un problema nuevo con respuestas ya validadas.
5. **Sistemas expertos — `prioridad`, `impacto`, `urgencia`, `SLA`:** formaliza criterios operativos usados para priorizar y escalar tickets.

## Comparación y discrepancias

No se encontraron discrepancias en la categoría principal: los 20 resultados coinciden con la referencia manual. Aun así, varios casos son multimodales; por eso las áreas secundarias conservan señales que una clasificación única ocultaría.

Por ejemplo, el caso 17 se clasifica principalmente como procesamiento de lenguaje natural y también activa Visión por computador, Sistemas de recomendación y Robótica. Esta combinación es coherente con un ticket que incluye texto, imágenes, recomendación y un robot de soporte remoto.

## Limitaciones y mejoras propuestas

- Las reglas detectan coincidencias literales; no comprenden sinónimos, negaciones ni contexto.
- Todos los activadores tienen el mismo peso y los empates dependen de un orden fijo.
- La referencia de 20 casos es pequeña y diseñada para la práctica; no mide desempeño con tickets reales.
- El motor identifica menciones de imágenes, pero todavía no procesa los píxeles adjuntos.
- Una palabra puede activar un área secundaria aunque su importancia real sea baja.

Como siguiente paso se propone reunir y anonimizar tickets históricos, definir etiquetas con técnicos, separar entrenamiento/validación/prueba y medir precisión, exhaustividad y F1. Para texto se puede iniciar con TF-IDF y regresión logística; para imágenes, con un modelo de visión preentrenado. Sus representaciones pueden combinarse en un clasificador multimodal, mientras la recomendación de soluciones puede usar similitud semántica sobre casos resueltos. Las respuestas generadas deben citar la base de conocimiento y mantener revisión humana, trazabilidad y control de datos sensibles.

## Reproducción

```powershell
python src/semana03_taxonomia.py
python -m unittest discover -s tests -v
```
