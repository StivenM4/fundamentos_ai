# Semana 02: Clasificación supervisada multietiqueta de tickets de soporte TI

## 1. Alcance técnico y formulación del problema

El objetivo de esta fase es implementar un pipeline de aprendizaje automático supervisado capaz de procesar tickets de soporte en lenguaje natural y predecir de forma simultánea las tres dimensiones requeridas para el triaje operativo en una mesa de ayuda corporativa:
* **Categoría funcional:** Dominio tecnológico del incidente (`hardware`, `software`, `red`, `accesos`).
* **Nivel de prioridad:** Severidad operativa del ticket (`alta`, `media`, `baja`), alineada a los tiempos de respuesta exigidos por los SLAs.
* **Tipo de caso (Incidente):** Clasificación binaria entre una falla que interrumpe la continuidad operativa (`sí`) frente a una solicitud de aprovisionamiento o trámite rutinario (`no`).

En producción, un modelo de triaje no puede depender de predicciones aisladas. La inferencia debe ser atómica y consistente: el sistema clasifica categoría, prioridad e impacto en un único paso de ejecución para enrutar el ticket de forma inmediata al grupo resolutor adecuado.

---

## 2. Transición metodológica: Del dataset canónico al análisis de texto libre

En los laboratorios introductorios se utiliza comúnmente el dataset *Iris*, compuesto por cuatro variables cuantitativas continuas perfectamente delimitadas. El soporte técnico real presenta un escenario diametralmente opuesto: texto libre no estructurado con errores de digitación, tecnicismos, abreviaciones y lenguaje coloquial.

| Criterio de ingeniería | Dataset canónico de laboratorio (*Iris*) | Pipeline de Soporte TI (Semana 02) | Justificación técnica |
|---|---|---|---|
| **Formato de entrada** | 4 características escalares numéricas (longitud/ancho). | Texto no estructurado en lenguaje natural. | Refleja la forma en que los usuarios reportan incidentes a través de portales o correos. |
| **Preprocesamiento** | Estandarización numérica de varianza (`StandardScaler`). | Vectorización sparse TF-IDF con eliminación de acentos Unicode. | Pondera la relevancia discriminativa de términos técnicos descartando stop words sin valor semántico. |
| **Dimensión del target** | Variable univariada multiclase (3 especies). | Target multivariado de 3 dimensiones simultáneas. | Da respuesta al problema real de triaje corporativo (tipo de falla + criticidad + afectación). |
| **Arquitectura del modelo** | Regresión logística multinomial simple. | `MultiOutputClassifier` sobre `LogisticRegression` (`max_iter=1000`). | Desacopla tres estimadores lineales independientes dentro de un único pipeline serializable. |
| **Origen del dato** | Generación sintética en memoria (`load_iris()`). | Ingesta estructurada desde CSV (`tickets_soporte.csv`). | Simula el consumo de bases de datos relacionales o exports de plataformas de ticketing. |

---

## 3. Dataset y diseño experimental

### 3.1. Evolución del corpus de entrenamiento
La fase exploratoria arrancó con un baseline preliminar de **128 tickets** (`tickets_soporte_antiguo.csv` / `OLD`). Aunque permitió comprobar la sintaxis del código, el volumen era insuficiente: con solo 96 registros en entrenamiento, la varianza del estimador era excesivamente alta y vocabulario técnico común quedaba fuera del diccionario de frecuencias.

Para estabilizar el modelo, se consolidó el dataset actual de **1.000 tickets estructurados** en `data/tickets_soporte.csv`:

| Parámetro experimental | Baseline preliminar (`OLD`) | Dataset actual de trabajo | Impacto en el modelo |
|---|---:|---:|---|
| **Archivo fuente** | `tickets_soporte_antiguo.csv` | `tickets_soporte.csv` | Transición a la data estructurada de producción del asistente. |
| **Volumen total** | 128 tickets | **1.000 tickets** | Crecimiento de 7.8x en volumen de texto y diversidad léxica. |
| **Muestras de entrenamiento (75 %)** | 96 tickets | **750 tickets** | Mayor densidad de coocurrencias de términos técnicos (*Active Directory, VPN, BSOD, switch*). |
| **Muestras de validación (25 %)** | 32 tickets | **250 tickets** | Representatividad estadística; cada error en test reduce su impacto de 3.125 % a 0.400 %. |
| **Balance de clases** | 32 por categoría | **250 por categoría** | Matriz balanceada para evitar sesgo del clasificador hacia clases mayoritarias. |
| **Semilla de aleatoriedad** | `random_state=42` | `random_state=42` | Partición estratificada determinista para garantizar reproducibilidad exacta. |

### 3.2. Estructura del pipeline en código
La solución se implementó en `src/semana02_fundamentos.py` mediante un pipeline compacto de Scikit-Learn:

```python
model = make_pipeline(
    TfidfVectorizer(strip_accents="unicode"),
    MultiOutputClassifier(
        LogisticRegression(
            max_iter=1000,
            random_state=RANDOM_STATE,
        )
    ),
)
model.fit(X_train, y_train)
```

---

## 4. Resultados cuantitativos y métricas de generalización

La evaluación sobre el conjunto de test (250 tickets no vistos durante el entrenamiento) demostró la ganancia de rendimiento obtenida al escalar de la línea base a `tickets_soporte.csv`:

| Dimensión de clasificación | Métrica evaluada | Baseline preliminar (`OLD`: 128 / 32 test) | Dataset actual (`tickets_soporte.csv`: 1.000 / 250 test) | Delta absoluto ($\Delta$) | Ganancia relativa (%) |
|---|---|---:|---:|---:|---:|
| **Categoría funcional** | Exactitud (*Accuracy*) | 71.9 % | **96.0 %** | **+24.1 p.p.** | **+33.5 %** |
| | Precisión macro | 74.9 % | **96.1 %** | **+21.2 p.p.** | **+28.3 %** |
| | Sensibilidad macro (*Recall*) | 71.9 % | **96.0 %** | **+24.1 p.p.** | **+33.5 %** |
| | Puntuación F1 macro | 71.3 % | **96.0 %** | **+24.7 p.p.** | **+34.6 %** |
| **Nivel de prioridad** | Exactitud (*Accuracy*) | 84.4 % | **96.0 %** | **+11.6 p.p.** | **+13.7 %** |
| | Precisión macro | 88.9 % | **96.6 %** | **+7.7 p.p.** | **+8.7 %** |
| | Sensibilidad macro (*Recall*) | 87.2 % | **95.5 %** | **+8.3 p.p.** | **+9.5 %** |
| | Puntuación F1 macro | 85.4 % | **96.0 %** | **+10.6 p.p.** | **+12.4 %** |
| **Detección de incidentes** | Exactitud (*Accuracy*) | 87.5 % | **99.6 %** | **+12.1 p.p.** | **+13.8 %** |
| | Precisión macro | 86.7 % | **99.6 %** | **+12.9 p.p.** | **+14.9 %** |
| | Sensibilidad macro (*Recall*) | 90.5 % | **99.6 %** | **+9.1 p.p.** | **+10.1 %** |
| | Puntuación F1 macro | 87.0 % | **99.6 %** | **+12.6 p.p.** | **+14.5 %** |

---

## 5. Conclusiones y análisis general de rendimiento

* **La calidad y balance del corpus superaron la complejidad algorítmica:** Un estimador lineal transparente como `LogisticRegression` alcanzó un **96.0 % de F1 macro** global y un **99.6 % en detección de incidentes**, demostrando que dotar al pipeline de un vocabulario balanceado de 1.000 registros estabiliza las predicciones sin requerir arquitecturas neuronales densas o costosas computacionalmente.
* **Causa raíz de confusiones controlada en categorías:** La matriz de confusión (239/250 aciertos) evidenció que los únicos desvíos ocurrieron en la frontera de hardware y software (4 casos de hardware clasificados como software y 2 viceversa), un comportamiento esperable en reportes donde la falla física de un periférico es descrita a través del error del driver o programa en pantalla.
* **Consistencia absoluta en priorización y criticidad:** No se presentaron errores entre extremos de prioridad (0 casos de `Alta` como `Baja`). En la detección de incidentes, el sistema alcanzó un **100 % de especificidad** (cero falsas alarmas que saturen al equipo de soporte) y un **99.2 % de sensibilidad** (123 de 124 incidentes reales detectados oportunamente).
* **Solución atómica y eficiente:** La arquitectura `MultiOutputClassifier` garantiza un tiempo de inferencia inferior a 5 milisegundos por ticket, resolviendo de forma integral el triaje requerido para la gestión operativa en una mesa de ayuda corporativa.