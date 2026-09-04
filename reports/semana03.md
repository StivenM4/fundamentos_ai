# Semana 03: Taxonomía de problemas de IA y motor simbólico explicable

## 1. Alcance técnico y formulación del problema

El objetivo de esta fase es diseñar un motor de inferencia simbólica explicable (*XAI*) que clasifique requerimientos de soporte técnico dentro de las siete ramas fundamentales de la Inteligencia Artificial, recomendando la técnica computacional adecuada para iniciar la remediación.

En la gestión de infraestructura de TI, clasificar un ticket únicamente por categoría funcional (`hardware`, `red`, etc.) no indica al equipo de ingeniería qué tecnología debe desplegarse para solucionar el problema. El motor analiza el texto del ticket y determina la disciplina de IA involucrada:
* **Procesamiento de Lenguaje Natural (PLN):** Extracción de entidades, análisis semántico de quejas o clasificación de texto libre.
* **Visión por Computador:** Procesamiento de evidencia gráfica adjunta por el usuario (capturas de error, cables dañados, LEDs de switch o BSOD).
* **Aprendizaje Predictivo:** Modelado estadístico sobre logs históricos para pronosticar demanda de analistas o reincidencia de fallas.
* **Sistemas de Recomendación:** Recuperación de artículos de la base de conocimiento y sugerencia de soluciones previas resueltas.
* **Sistemas Expertos:** Evaluación determinista de políticas de escalamiento, matrices de impacto/urgencia y cumplimiento de SLAs.
* **IA Generativa:** Síntesis documental, redacción asistida de plantillas de cierre o borradores de respuesta técnica.
* **Robótica y Automatización (RPA):** Agentes de autorreparación remota, scripts desatendidos y macros de reinicio de servicios.

---

## 2. Transición metodológica: Modelo estadístico opaco vs. Motor declarativo explicable

Los clasificadores supervisados entrenados con vectores continuos funcionan como cajas negras: predicen una etiqueta pero no justifican la causa de su decisión. Para tareas de auditoría técnica y supervisión de SLAs, se implementó un motor basado en reglas y activadores léxicos:

| Criterio de diseño | Clasificador estadístico de caja negra | Motor simbólico explicable (Semana 03) | Justificación técnica |
|---|---|---|---|
| **Mecanismo de inferencia** | Ponderación de pesos continuos en matrices dispersas. | Escaneo determinista de patrones y activadores léxicos (*triggers*). | Trazabilidad completa: el sistema entrega la lista exacta de términos que motivaron la decisión. |
| **Tratamiento del requerimiento** | Asignación forzada a una única clase excluyente. | Inferencia jerárquica: categoría primaria y preservación de áreas secundarias. | Captura la naturaleza multimodal de los problemas de TI (ej. texto + captura de pantalla + automatización). |
| **Gestión del conocimiento** | Implícito en los parámetros del modelo; requiere reentrenamiento ante cambios. | Repositorio declarativo externo estructurado (`activadores_taxonomia.json`). | Desacopla la lógica de negocio del código ejecutable; permite a ingenieros L2 actualizar reglas sin tocar Python. |
| **Output del sistema** | Etiqueta de clase simple (`software`). | Cuádrupla estructurada: (Categoría Primaria, Áreas Secundarias, Triggers, Técnica Sugerida). | Proporciona al especialista una guía operativa inmediata para proceder. |
| **Resiliencia en producción** | Degrada su rendimiento ante vocabulario no visto en entrenamiento. | Inferencia directa por reglas + bloque de contingencia (*fallback*) a PLN estadístico. | Garantiza continuidad operativa en la mesa de ayuda sin lanzar excepciones al usuario. |

---

## 3. Dataset y catálogo de reglas

### 3.1. Evolución del corpus de evaluación
La prueba inicial con **20 casos** en `casos_ia_OLD.csv` (`OLD`) evidenció una limitación estructural: ignoraba por completo los requerimientos de **Robótica y RPA**, una disciplina crítica en operaciones modernas de TI donde la primera línea de defensa son bots de remediación automática.

Para subsanar esta brecha, se estructuró el dataset actual de **50 casos dorados** (`casos_ia.csv`) respaldado por un diccionario de 123 activadores técnicos en `activadores_taxonomia.json`:

| Parámetro experimental | Baseline preliminar (`OLD`) | Dataset actual de trabajo | Impacto operativo |
|---|---:|---:|---|
| **Archivo de casos** | `casos_ia_OLD.csv` | `casos_ia.csv` | Data actualmente consumida por las pruebas del asistente. |
| **Casos evaluados** | 20 casos | **50 casos documentados** | Incremento del 150 % en casuística y escenarios de borde. |
| **Cobertura disciplinar** | 6 ramas (sin Robótica) | **7 disciplinas completas** | Cobertura integral de scripts RPA, bots de autorreparación y agentes autónomos. |
| **Catálogo de activadores** | 61 términos | **123 activadores únicos** | Duplicación (+101.6 %) de la cobertura léxica técnica reconocida por el motor. |
| **Densidad de triggers** | 4.4 términos/caso | **4.2 términos/caso** | Mayor especificidad de coincidencia; menor tasa de activaciones espurias. |
| **Detección multimodal** | 8 casos (40.0 %) | **14 casos (28.0 %)** | Coexistencia precisa de señales secundarias sin perder la causa raíz. |
| **Validación manual de referencia** | 20 / 20 (100.0 %) | **50 / 50 (100.0 %)** | Cero falsos positivos o clasificaciones inconsistentes. |

### 3.2. Implementación del motor
El procesamiento en `src/semana03_taxonomia.py` se ejecuta en cuatro fases:
1. **Normalización:** Limpieza de diacríticos y puntuación preservando tokens compuestos (*"pantalla azul"*, *"base de conocimiento"*, *"enlace troncal"*).
2. **Escaneo léxico:** Búsqueda cruzada de las expresiones definidas en el archivo JSON contra el texto normalizado.
3. **Resolución jerárquica:** Asignación de la categoría primaria por conteo y peso de activadores coincidentes. Las ramas concurrentes se registran como `secondary_areas`.
4. **Mapeo procedural:** Asignación de la técnica inicial recomendada según la categoría principal detectada.

---

## 4. Evaluación experimental y resultados del motor

### 4.1. Métricas comparativas de cobertura y desempeño

| Dimensión de evaluación | Métrica | Baseline preliminar (`OLD`: 20 casos) | Dataset actual (`casos_ia.csv`: 50 casos) | Delta ($\Delta$) | Ganancia relativa (%) |
|---|---|---:|---:|---:|---:|
| **Efectividad global** | Coincidencia con referencia manual | 100.0 % (20/20) | **100.0 % (50/50)** | **0.0 p.p.** | **Consistencia determinista** |
| **Ramas cubiertas** | Total disciplinas de IA | 6 ramas | **7 ramas** | **+1 rama** | **+16.7 %** |
| **Vocabulario técnico** | Triggers únicos indexados | 61 términos | **123 términos** | **+62 términos** | **+101.6 %** |
| **Robótica y RPA** | Casos detectados | 0 casos (0.0 %) | **4 casos (8.0 %)** | **+4 casos** | **Capacidad nueva implementada** |
| **Lenguaje Natural** | Casos procesados | 5 casos (25.0 %) | **10 casos (20.0 %)** | **+5 casos** | **+100.0 % volumen** |
| **Visión Computacional** | Casos procesados | 3 casos (15.0 %) | **8 casos (16.0 %)** | **+5 casos** | **+166.7 % volumen** |
| **IA Generativa** | Casos procesados | 3 casos (15.0 %) | **7 casos (14.0 %)** | **+4 casos** | **+133.3 % volumen** |

### 4.2. Distribución en el dataset actual (`casos_ia.csv`)
* **Procesamiento de lenguaje natural:** 10 casos (20.0 %)
* **Visión por computador:** 8 casos (16.0 %)
* **Aprendizaje predictivo:** 7 casos (14.0 %)
* **Sistemas de recomendación:** 7 casos (14.0 %)
* **Sistemas expertos:** 7 casos (14.0 %)
* **IA generativa:** 7 casos (14.0 %)
* **Robótica / RPA:** 4 casos (8.0 %)

### 4.3. Evidencia completa de los 50 casos evaluados

| Caso | Categoría principal | Áreas secundarias | Triggers activos | Técnica inicial recomendada |
|---:|---|---|---|---|
| 1 | Procesamiento de lenguaje natural | Ninguna | `texto`, `clasificar`, `tickets` | clasificador de texto con TF-IDF y regresión logística |
| 2 | Visión por computador | Ninguna | `captura`, `captura de pantalla`, `pantallazo` | red convolucional o modelo de visión preentrenado |
| 3 | Aprendizaje predictivo | Ninguna | `predecir`, `siguiente semana`, `caso recurrente` | clasificación o regresión supervisada con datos históricos |
| 4 | Sistemas de recomendación | Ninguna | `recomendar`, `solucion similar`, `casos resueltos`, `base de conocimiento` | recuperación por similitud semántica de casos resueltos |
| 5 | Sistemas expertos | Procesamiento de lenguaje natural | `priorizar`, `impacto`, `urgencia`, `cumplimiento del sla`, `sla` | motor de reglas con criterios de impacto, urgencia y SLA |
| 6 | IA generativa | Procesamiento de lenguaje natural | `generar`, `redactar` | modelo generativo con recuperación de conocimiento y revisión humana |
| 7 | Procesamiento de lenguaje natural | Ninguna | `descripcion textual`, `intencion`, `entidades`, `descripcion`, `solicitud` | clasificador de texto con TF-IDF y regresión logística |
| 8 | Aprendizaje predictivo | Procesamiento de lenguaje natural, Sistemas expertos | `pronosticar`, `tiempo de resolucion`, `probabilidad` | clasificación o regresión supervisada con datos históricos |
| 9 | Visión por computador | Ninguna | `imagen`, `inspeccionar`, `puertos`, `cables`, `luces` | red convolucional o modelo de visión preentrenado |
| 10 | Sistemas de recomendación | Sistemas expertos | `recomendar`, `soluciones similares`, `tecnico adecuado`, `ruta de escalamiento` | recuperación por similitud semántica de casos resueltos |
| 11 | Sistemas expertos | Ninguna | `reglas`, `reglas de diagnostico` | motor de reglas con criterios de impacto, urgencia y SLA |
| 12 | IA generativa | Ninguna | `asistente generativo`, `crear pasos` | modelo generativo con recuperación de conocimiento y revisión humana |
| 13 | Procesamiento de lenguaje natural | Ninguna | `texto`, `extraer`, `ticket`, `mensaje de error` | clasificador de texto con TF-IDF y regresión logística |
| 14 | Aprendizaje predictivo | Procesamiento de lenguaje natural | `predecir`, `demanda`, `cuantos tecnicos` | clasificación o regresión supervisada con datos históricos |
| 15 | Visión por computador | Ninguna | `interfaz`, `visual`, `anomalia visual`, `captura`, `captura de pantalla` | red convolucional o modelo de visión preentrenado |
| 16 | Sistemas de recomendación | Ninguna | `recomendar`, `casos resueltos`, `articulo`, `base de conocimiento` | recuperación por similitud semántica de casos resueltos |
| 17 | Procesamiento de lenguaje natural | Visión por computador, Sistemas de recomendación, Robótica | `texto`, `clasificar`, `ticket` | clasificador de texto con TF-IDF y regresión logística |
| 18 | Sistemas expertos | Ninguna | `impacto`, `urgencia`, `reglas`, `diagnosticar mediante reglas`, `prioridad`, `sla` | motor de reglas con criterios de impacto, urgencia y SLA |
| 19 | IA generativa | Procesamiento de lenguaje natural | `generar`, `redactar`, `resumen tecnico`, `respuesta final` | modelo generativo con recuperación de conocimiento y revisión humana |
| 20 | Procesamiento de lenguaje natural | Visión por computador, Sistemas de recomendación | `texto`, `ticket` | clasificador de texto con TF-IDF y regresión logística |
| 21 | Procesamiento de lenguaje natural | Ninguna | `clasificar`, `extraer`, `correo`, `queja`, `peticion`, `mensaje de error`, `correo de queja` | clasificador de texto con TF-IDF y regresión logística |
| 22 | Visión por computador | Ninguna | `inspeccionar`, `foto`, `screenshot`, `foto del error`, `pantalla azul` | red convolucional o modelo de visión preentrenado |
| 23 | Aprendizaje predictivo | Ninguna | `predecir`, `probabilidad`, `patron`, `historico` | clasificación o regresión supervisada con datos históricos |
| 24 | Sistemas de recomendación | Ninguna | `articulo`, `base de conocimiento`, `articulo kb` | recuperación por similitud semántica de casos resueltos |
| 25 | Sistemas expertos | Procesamiento de lenguaje natural | `reglas`, `matriz de prioridad`, `severidad`, `prioridad`, `sla` | motor de reglas con criterios de impacto, urgencia y SLA |
| 26 | IA generativa | Ninguna | `generar`, `borrador de respuesta` | modelo generativo con recuperación de conocimiento y revisión humana |
| 27 | Robótica | Ninguna | `autonomo`, `bot de soporte`, `script de autorreparacion` | percepción y planificación conectadas con sensores del dispositivo |
| 28 | Procesamiento de lenguaje natural | Ninguna | `extraer`, `chat`, `conversacion`, `vocabulario` | clasificador de texto con TF-IDF y regresión logística |
| 29 | Visión por computador | Ninguna | `imagen`, `puertos`, `cables`, `luces`, `parpadeo` | red convolucional o modelo de visión preentrenado |
| 30 | Aprendizaje predictivo | Procesamiento de lenguaje natural | `siguiente semana`, `tendencia`, `proyeccion`, `volumen esperado` | clasificación o regresión supervisada con datos históricos |
| 31 | Sistemas de recomendación | Ninguna | `recomendar`, `casos resueltos`, `manual tecnico`, `faq`, `historial de soluciones` | recuperación por similitud semántica de casos resueltos |
| 32 | Sistemas expertos | Ninguna | `runbook`, `arbol de decision`, `escalamiento`, `escalamiento l2` | motor de reglas con criterios de impacto, urgencia y SLA |
| 33 | IA generativa | Procesamiento de lenguaje natural | `redactar`, `plantilla de cierre` | modelo generativo con recuperación de conocimiento y revisión humana |
| 34 | Robótica | Ninguna | `automatizacion`, `automatizacion rpa` | percepción y planificación conectadas con sensores del dispositivo |
| 35 | Procesamiento de lenguaje natural | Ninguna | `descripcion textual`, `clasificar`, `intencion`, `descripcion`, `ticket`, `ticket de soporte` | clasificador de texto con TF-IDF y regresión logística |
| 36 | Visión por computador | Ninguna | `visual`, `anomalia visual`, `lineas en pantalla`, `captura`, `captura de pantalla` | red convolucional o modelo de visión preentrenado |
| 37 | Aprendizaje predictivo | Ninguna | `pronosticar`, `frecuencia`, `tiempo estimado`, `reincidencia` | clasificación o regresión supervisada con datos históricos |
| 38 | Sistemas de recomendación | Ninguna | `casos resueltos`, `documentacion`, `sugerencia` | recuperación por similitud semántica de casos resueltos |
| 39 | Sistemas expertos | Procesamiento de lenguaje natural | `urgencia`, `cumplimiento del sla`, `regla fija`, `sla` | motor de reglas con criterios de impacto, urgencia y SLA |
| 40 | IA generativa | Ninguna | `crear pasos`, `parafrasear`, `asistente conversacional` | modelo generativo con recuperación de conocimiento y revisión humana |
| 41 | Robótica | Ninguna | `autonomo`, `reinicio automatico`, `agente autonomo` | percepción y planificación conectadas con sensores del dispositivo |
| 42 | Procesamiento de lenguaje natural | Ninguna | `texto`, `entidades`, `extraer`, `idioma`, `ticket` | clasificador de texto con TF-IDF y regresión logística |
| 43 | Visión por computador | Ninguna | `camara`, `foto`, `grafico`, `displayport` | red convolucional o modelo de visión preentrenado |
| 44 | Aprendizaje predictivo | Ninguna | `regresion`, `riesgo de retraso` | clasificación o regresión supervisada con datos históricos |
| 45 | Sistemas de recomendación | Ninguna | `recomendar`, `base de conocimiento`, `mejor opcion`, `solucion mas votada` | recuperación por similitud semántica de casos resueltos |
| 46 | Sistemas expertos | Procesamiento de lenguaje natural | `politica`, `flujo de aprobacion`, `aprobacion`, `prioridad` | motor de reglas con criterios de impacto, urgencia y SLA |
| 47 | IA generativa | Procesamiento de lenguaje natural | `generar`, `redaccion automatica` | modelo generativo con recuperación de conocimiento y revisión humana |
| 48 | Robótica | Ninguna | `robot`, `robot de soporte`, `soporte remoto`, `macro de ejecucion` | percepción y planificación conectadas con sensores del dispositivo |
| 49 | Procesamiento de lenguaje natural | Ninguna | `clasificar`, `extraer`, `parrafo`, `consulta`, `ticket` | clasificador de texto con TF-IDF y regresión logística |
| 50 | Visión por computador | Ninguna | `video`, `inspeccionar` | red convolucional o modelo de visión preentrenado |

---

## 5. Conclusiones y hallazgos generales sobre explicabilidad

* **La multimodalidad es intrínseca a la operación de soporte:** El análisis evidenció que los requerimientos reales rara vez pertenecen a una única disciplina aislada. El Caso 17 demuestra la necesidad de preservar áreas secundarias: un ticket que reporta texto libre, adjunta una captura gráfica, solicita un artículo técnico y detona una macro de ejecución no puede forzarse a una sola categoría sin perder señales críticas de atención.
* **El desacoplamiento del conocimiento garantiza mantenibilidad:** Gestionar los 123 activadores en `activadores_taxonomia.json` independiza la base de reglas del código Python. Esto permite que especialistas de infraestructura incorporen terminología nueva de software o hardware sin modificar la lógica del motor ni arriesgar regresiones en el entorno de ejecución.
* **La incorporación de Robótica y RPA cerró la brecha operativa:** Incluir formalmente la automatización desatendida en el dataset actual (`casos_ia.csv`) permite identificar cuándo un ticket no requiere intervención humana presencial, sino la ejecución de un agente de autorreparación o script de remediación remota.
* **Explicabilidad determinista como estándar de auditoría:** Frente a la opacidad de los modelos basados en redes neuronales, este motor entrega la evidencia exacta (`triggers`) que motivó la clasificación, garantizando transparencia absoluta para la justificación de decisiones ante supervisores de TI y auditorías de calidad.
