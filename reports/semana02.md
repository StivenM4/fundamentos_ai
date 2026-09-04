# Semana 02: Clasificación supervisada de tickets de soporte técnico en TI

## 1. Introducción y objetivos

El objetivo de esta práctica es trasladar los principios del aprendizaje supervisado —trabajados inicialmente con problemas de referencia como el conjunto de datos *Iris*— a un caso de uso práctico: el **Asistente de soporte TI**.

A diferencia de los ejercicios introductorios basados en medidas cuantitativas cerradas, este sistema analiza el texto redactado por los usuarios en sus solicitudes de servicio. A partir de esa información, el modelo aprende a predecir de manera simultánea tres variables clave para la gestión del soporte:

- **Categoría:** El área tecnológica correspondiente (*hardware*, *software*, *red* o *accesos*).
- **Prioridad:** El nivel de urgencia de la atención (*alta*, *media* o *baja*).
- **Tipo de caso (Incidente):** La distinción entre una falla que detiene el servicio (*sí*) y una consulta o trámite regular (*no*).

---

## 2. Transición metodológica: del caso clásico al análisis de texto

El flujo de trabajo habitual en ciencia de datos se mantiene: carga de datos, separación de muestras de entrenamiento y prueba, construcción de la secuencia de procesamiento (*pipeline*), entrenamiento del clasificador y evaluación final. No obstante, trabajar con lenguaje natural exige adaptar las herramientas y los métodos:

| Criterio | Ejemplo introductorio (*Iris*) | Proyecto de soporte TI | Justificación del cambio |
|---|---|---|---|
| **Origen de datos** | Funciones integradas (`load_iris()`) | Archivos estructurados (`tickets_soporte.csv`) | Simula la ingesta real de datos desde plataformas de mesas de ayuda. |
| **Variables de entrada** | 4 medidas numéricas de longitud y ancho | Texto no estructurado del ticket | Requiere transformar el lenguaje humano a un formato cuantitativo computable. |
| **Representación** | Estandarización numérica (`StandardScaler`) | Vectorización textual (`TfidfVectorizer`) | Permite ponderar la relevancia e importancia de cada palabra según su frecuencia. |
| **Variables objetivo** | Una única variable (especie de flor) | Tres variables simultáneas (categoría, prioridad, incidente) | Da respuesta a las múltiples dimensiones de triaje que exige el soporte técnico. |
| **Algoritmo base** | Regresión logística simple | Regresión logística multietiqueta/multisalida | Permite resolver tres problemas de clasificación en un único flujo de ejecución. |

---

## 3. Conjunto de datos y diseño experimental

### 3.1. Evolución del corpus: de 128 a 1.000 registros
Inicialmente se realizó una prueba piloto con **128 tickets**. Aunque este primer ejercicio permitió comprobar que el código y el flujo de trabajo funcionaban correctamente, la muestra era demasiado pequeña para reflejar las variadas formas en que los usuarios describen un problema, lo que dejaba un alto margen de incertidumbre en los resultados.

Para construir un modelo más confiable, el conjunto se amplió a **1.000 tickets documentados**, lo que brindó una base de datos más amplia, equilibrada y cercana al entorno de trabajo diario de una organización:

| Parámetro experimental | Línea base inicial | Corpus ampliado | Impacto metodológico |
|---|---:|---:|---|
| **Total de tickets** | 128 | **1.000** | Aumento de casi 8 veces en volumen textual y diversidad sintáctica. |
| **Muestras de entrenamiento (75 %)** | 96 | **750** | Mayor cobertura de coocurrencias de términos técnicos y contextos operativos. |
| **Muestras de prueba (25 %)** | 32 | **250** | Reducción drástica de la varianza del estimador y representatividad estadística. |
| **Peso individual por muestra en test** | 3.125 % ($\frac{1}{32}$) | **0.400 %** ($\frac{1}{250}$) | Un único error de clasificación ya no distorsiona drásticamente las métricas globales. |
| **Estructura de balance** | 32 por categoría | **250 por categoría** | Diseño factorial simétrico que anula el sesgo por clase mayoritaria. |
| **Semilla de aleatoriedad** | `random_state=42` | `random_state=42` | Garantiza la estricta reproducibilidad de las particiones estratificadas. |

### 3.2. Estructura del modelo
El sistema de clasificación integra tres etapas ordenadas:
1. **Transformación del texto (TF-IDF):** Convierte el texto de los tickets en valores numéricos proporcionales a la relevancia de cada palabra, destacando términos informativos y descartando términos comunes sin valor descriptivo.
2. **Estrategia multietiqueta (*MultiOutputClassifier*):** Permite predecir de forma paralela e independiente la categoría, la prioridad y la detección de incidentes.
3. **Clasificador base (Regresión Logística):** Modela la relación entre el peso de los términos presentes en cada solicitud y la probabilidad de pertenecer a cada una de las clases.

---

## 4. Resultados experimentales y análisis comparativo

La ampliación del corpus permitió contrastar directamente cómo influye el volumen de datos en la capacidad de generalización del modelo. A continuación se presentan las métricas obtenidas sobre los grupos de prueba, formados por casos que el algoritmo nunca vio durante la etapa de entrenamiento:

### 4.1. Comparativa de desempeño: 128 tickets (línea base) vs. 1.000 tickets (corpus ampliado)

| Dimensión / Variable | Métrica evaluada | Línea base (128 tickets / 32 test) | Corpus ampliado (1.000 tickets / 250 test) | Diferencia absoluta ($\Delta$ p.p.) | Ganancia relativa (%) |
|---|---|---:|---:|---:|---:|
| **Categoría temática** | Exactitud (*Accuracy*) | 71.9 % | **96.0 %** | **+24.1 p.p.** | **+33.5 %** |
| | Precisión macro | 74.9 % | **96.1 %** | **+21.2 p.p.** | **+28.3 %** |
| | Sensibilidad macro (*Recall*) | 71.9 % | **96.0 %** | **+24.1 p.p.** | **+33.5 %** |
| | Puntuación F1 macro | 71.3 % | **96.0 %** | **+24.7 p.p.** | **+34.6 %** |
| **Nivel de prioridad** | Exactitud (*Accuracy*) | 84.4 % | **96.0 %** | **+11.6 p.p.** | **+13.7 %** |
| | Precisión macro | 88.9 % | **96.6 %** | **+7.7 p.p.** | **+8.7 %** |
| | Sensibilidad macro (*Recall*) | 87.2 % | **95.5 %** | **+8.3 p.p.** | **+9.5 %** |
| | Puntuación F1 macro | 85.4 % | **96.0 %** | **+10.6 p.p.** | **+12.4 %** |
| **Detección de incidente** | Exactitud (*Accuracy*) | 87.5 % | **99.6 %** | **+12.1 p.p.** | **+13.8 %** |
| | Precisión macro | 86.7 % | **99.6 %** | **+12.9 p.p.** | **+14.9 %** |
| | Sensibilidad macro (*Recall*) | 90.5 % | **99.6 %** | **+9.1 p.p.** | **+10.1 %** |
| | Puntuación F1 macro | 87.0 % | **99.6 %** | **+12.6 p.p.** | **+14.5 %** |

> *Nota explicativa:* La **Diferencia absoluta ($\Delta$ p.p.)** corresponde a la suma aritmética simple de puntos porcentuales. La **Ganancia relativa ($\%$)** representa el porcentaje de mejora con respecto al desempeño del modelo inicial: $\frac{\text{valor final} - \text{valor inicial}}{\text{valor inicial}} \times 100$.

### 4.2. Análisis de los resultados por dimensión

1. **Categoría temática (+24.7 p.p. en F1 macro):**
   Fue la mejora más notoria del experimento, con un crecimiento relativo del 34.6 %. Con 128 tickets, la exactitud era del 71.9 % debido a que el modelo confundía con frecuencia solicitudes de software y accesos. Al subir a 1.000 tickets, alcanzó un **96.0 %**, ya que contó con vocabulario suficiente para distinguir trámites de credenciales y permisos (como contraseñas, usuarios o accesos VPN) de fallas directas en el software (como errores de ejecución, lentitud o cierres imprevistos).

2. **Nivel de prioridad (+10.6 p.p. en F1 macro):**
   La exactitud pasó del 84.4 % al **96.0 %**. Al disponer de más ejemplos, el clasificador identificó con mayor claridad los términos que denotan urgencia o afectación generalizada (*"operación detenida"*, *"área sin servicio"*), asignándoles prioridad alta sin la vacilación que antes existía con la prioridad media.

3. **Detección de incidentes (+12.6 p.p. en F1 macro):**
   Obtuvo un rendimiento casi perfecto con un **99.6 %** de efectividad. De las 250 pruebas evaluadas, el sistema cometió **un único error por omisión** (un falso negativo) y **cero falsos positivos**. En un entorno operativo, esto garantiza que casi ningún incidente crítico pase por alto, evitando a su vez alertas innecesarias que desgasten al equipo de soporte.

### 4.3. Matrices de confusión (Evaluación sobre 250 tickets de prueba)

A continuación se detalla la correspondencia entre los valores reales observados (filas) y las predicciones emitidas por el modelo (columnas):

#### A. Categoría temática
| Real \ Predicción | Accesos | Hardware | Red | Software | Desempeño por clase |
|---|---:|---:|---:|---:|---|
| **Accesos** | **61** | 0 | 0 | 2 | 96.8 % de acierto (61/63) |
| **Hardware** | 0 | **58** | 0 | 4 | 93.5 % de acierto (58/62) |
| **Red** | 0 | 2 | **61** | 0 | 96.8 % de acierto (61/63) |
| **Software** | 0 | 2 | 0 | **60** | 96.8 % de acierto (60/62) |

*Interpretación:* La diagonal principal reúne 239 de los 250 casos analizados (96.0 % global). Los pocos errores ocurrieron entre hardware y software, un escenario comprensible en reportes donde la falla de un equipo físico se origina en un controlador o programa.

#### B. Nivel de prioridad
| Real \ Predicción | Alta | Baja | Media | Desempeño por clase |
|---|---:|---:|---:|---|
| **Alta** | **93** | 0 | 2 | 97.9 % de acierto (93/95) |
| **Baja** | 4 | **56** | 1 | 91.8 % de acierto (56/61) |
| **Media** | 3 | 0 | **91** | 96.8 % de acierto (91/94) |

*Interpretación:* No hubo confusiones extremas entre prioridades opuestas: ningún caso de prioridad alta se clasificó como baja ni viceversa, lo que demuestra un criterio de asignación coherente y seguro.

#### C. Detección de incidentes
| Real \ Predicción | No (Solicitud estándar) | Sí (Incidente disruptivo) | Desempeño por clase |
|---|---:|---:|---|
| **No** | **126** | 0 | 100.0 % de especificidad (126/126) |
| **Sí** | 1 | **123** | 99.2 % de sensibilidad (123/124) |

*Interpretación:* Un 100 % de especificidad y un 99.2 % de acierto en la detección de incidentes reales confirman que el sistema es lo bastante confiable para apoyar la clasificación en una mesa de ayuda.

---

## 5. Discusión: Factores que explican el aumento de rendimiento

El paso de **128 a 1.000 tickets** fue la decisión determinante para estabilizar el modelo. Este avance se sustenta en cinco aspectos principales:

### 1. Mayor riqueza en el vocabulario técnico
En el ejercicio inicial de 128 registros (con apenas 96 tickets para entrenar), muchas palabras clave aparecían una sola vez o no estaban presentes en el entrenamiento, de modo que el modelo no sabía cómo interpretarlas durante la prueba. Con 750 tickets de entrenamiento, los términos técnicos característicos (*VPN, Active Directory, switch, monitor, base de datos, credenciales*) se repiten en distintas oraciones, lo que ayuda al modelo a calcular importancias numéricas mucho más precisas y generalizables.

### 2. Reducción de asociaciones erróneas por contexto
Con pocos datos, los clasificadores suelen aprender relaciones casuales que no son ciertas. Por ejemplo, si en la muestra inicial los tickets enviados desde contabilidad hablaban únicamente de impresoras, el sistema podía asumir por error que la palabra *"contabilidad"* siempre correspondía a *hardware*. Al ampliar la muestra a 1.000 tickets, las diferentes áreas de la empresa (*ventas, finanzas, recursos humanos*) aparecen en todas las categorías; esto permite al modelo ignorar esos cargos o departamentos y centrarse en las palabras que describen el problema real.

### 3. Diferenciación clara entre problemas y solicitudes rutinarias
El modelo aprendió con gran claridad el propósito comunicativo de los usuarios:
- **Incidentes:** Expresados con verbos y adjetivos que indican interrupción o falla operativa (*"se apagó", "no responde", "bloqueado", "caído", "error fatal"*).
- **Solicitudes de rutina:** Expresadas mediante un lenguaje formal y de trámite cotidiano (*"solicito", "requiero", "creación de usuario", "cotización", "programar"*).

Al contar con suficientes ejemplos balanceados de cada tipo, el modelo encontró un límite de separación muy claro entre una solicitud y una interrupción real.

### 4. Mayor representatividad y estabilidad en las evaluaciones
En la prueba con 32 casos, un único error modificaba el resultado global en un **3.1 %**, haciendo que la calificación fuera muy inestable y dependiera en gran medida del azar al dividir los datos. Con el grupo de prueba de 250 tickets, cada caso representa únicamente el **0.4 %** del total, lo que asegura que las métricas obtenidas reflejen fielmente cómo respondería el sistema ante nuevos casos en producción.

### 5. Control de sesgos mediante una distribución equilibrada
A diferencia de los entornos de soporte reales —donde ciertas fallas son mucho más comunes que otras—, este conjunto de 1.000 tickets se balanceó de manera uniforme entre todas las categorías y niveles de prioridad. Esto impidió que el modelo desarrollara preferencia por la opción más frecuente y lo forzó a aprender los patrones reales de cada clase.

---

## 6. Conclusiones

La experiencia de la Semana 02 confirma que la clasificación multietiqueta mediante `TfidfVectorizer` y `LogisticRegression` es una alternativa práctica, rápida y eficaz para la clasificación inicial de tickets de soporte técnico.

La comparativa entre los conjuntos de 128 y 1.000 tickets demuestra que la calidad y representatividad de los datos resultan más determinantes que la complejidad del algoritmo: un modelo lineal transparente y bien entrenado logró superar el **96.0 % de F1 macro** en todas las áreas y un **99.6 %** en la detección de incidentes. Estos resultados establecen una base metodológica sólida para el diseño de taxonomías más avanzadas (Semana 03) y la posterior planificación de tareas de resolución (Semana 04).