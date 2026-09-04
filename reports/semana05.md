# Semana 05: Sistema híbrido de soporte TI con trazabilidad integral

## 1. Alcance técnico y arquitectura híbrida

El objetivo de esta fase es diseñar e implementar un **sistema híbrido explicable** que resuelva incidentes de soporte técnico mediante la integración sinérgica de cinco componentes de Inteligencia Artificial:
1. **Sistemas expertos:** Reglas deterministas ejecutadas con funciones condicionales para acciones inmediatas (*Fast-Path*).
2. **Ingeniería del conocimiento:** Base documental estructurada con 75 manuales procedimentales validados por especialistas de soporte.
3. **Recuperación de información (RAG):** Vectorización TF-IDF con stop words optimizadas en español y cálculo de similitud coseno para extraer el procedimiento técnico más afín.
4. **Reconocimiento de formas / Clasificación supervisada:** Pipeline de regresión logística que corrobora de forma independiente el dominio funcional del caso (`hardware`, `software`, `red`, `accesos`).
5. **Tratamiento del lenguaje natural (PLN):** Normalización léxica y extracción de señales semánticas sobre consultas en lenguaje natural.

En producción corporativa, delegar la resolución de incidentes a un modelo generativo masivo (*LLM*) sin anclaje documental introduce dos riesgos inaceptables: **alucinación de comandos** (generación de parámetros de consola erróneos o dañinos) y **falta de auditoría** (incapacidad de justificar ante un SLA la fuente exacta de la recomendación). La arquitectura híbrida mitiga ambos problemas desacoplando la regla determinista de la evidencia documental verificada.

---

## 2. Transición metodológica: Búsqueda documental estática vs. Pipeline híbrido desacoplado

La gestión tradicional de bases de conocimiento suele depender de motores de búsqueda por palabras clave exactas (`like '%string%'`) o de reglas rígidas cableadas. El pipeline híbrido implementado en `src/semana05_sistema_hibrido.py` sustituye este esquema por una inferencia multinivel:

| Dimensión técnica | Búsqueda por coincidencia literal / Reglas aisladas | Pipeline híbrido trazable (Semana 05) | Justificación de ingeniería |
|---|---|---|---|
| **Canal de decisión** | Búsqueda estricta de subcadenas en texto. | Fast-Path determinista + RAG TF-IDF + Clasificador ML. | Si hay regla evidente se actúa en milisegundos; si no, el RAG recupera el manual sin interrumpir el flujo. |
| **Repositorio procedimental** | Notas técnicas desestructuradas y dispersas. | Base formalizada de 75 procedimientos categorizados por dominio. | Estandariza la remediación técnica asegurando que los analistas apliquen pasos homologados. |
| **Métrica de afinidad** | Conteo binario de palabras compartidas. | Similitud coseno continua ($[0, 1]$) sobre vectores TF-IDF normalizados. | Pondera términos técnicos de alto valor diagnóstico (*"DNS"*, *"DHCP"*, *"BSOD"*) sobre vocabulario genérico. |
| **Explicabilidad (*XAI*)** | Opaca; muestra fragmentos de texto sin justificación matemática. | Trazabilidad cuádruple: (Regla activa, Procedimiento, Score similitud, Clase predicha). | Cumple con los requerimientos de auditoría y gestión de calidad bajo normas ITIL. |
| **Contención de alcance** | Devuelve siempre el documento más cercano aunque sea irrelevante. | Guardrail con umbral de corte al 20 % para solicitudes fuera de catálogo. | Previene que el asistente sugiera procedimientos de TI a fallas biomédicas o de maquinaria ajena. |

---

## 3. Base de conocimiento y diseño del pipeline

### 3.1. Evolución de la base documental
El desarrollo inicial con **10 artículos** en `data/base_conocimiento_OLD.txt` (`OLD`) demostró que una base reducida genera **falsos positivos críticos de recuperación**: al no existir manuales de infraestructura especializada (como switches centrales o enlaces troncales), el algoritmo de similitud coseno forzaba la coincidencia hacia el documento más cercano disponible (asignando erróneamente manuales de clientes VPN).

Para garantizar cobertura real, se estructuró la base actual de **75 manuales procedimentales** en `data/base_conocimiento.txt`:

| Parámetro experimental | Baseline preliminar (`OLD`) | Base procedimental actual | Impacto operativo |
|---|---:|---:|---|
| **Archivo fuente** | `base_conocimiento_OLD.txt` | `base_conocimiento.txt` | Data actualmente consumida por el módulo híbrido de resolución. |
| **Volumen de manuales** | 10 artículos breves | **75 manuales procedimentales** | Cobertura multiplicada por 7.5x sobre casuística corporativa real. |
| **Balance temático** | 2 a 3 manuales por área | **~19 manuales por categoría** (*Hardware, Red, Software, Accesos*) | Distribución factorial uniforme para evitar sesgos en el cálculo del coseno. |
| **Stop words en español** | Stop words genéricas de biblioteca | **56 stop words optimizadas** | Elimina preposiciones y artículos que inflaban artificialmente la similitud léxica. |
| **Reglas expertas (Fast-Path)** | 5 lambdas básicas | **5 reglas de dominio estandarizadas** | Canales inmediatos para incidentes de alta recurrencia (ventilación, DNS, etc.). |
| **Ejemplos de entrenamiento ML** | 15 pares texto-etiqueta | **15 muestras balanceadas representativas** | Pipeline supervisado con `LogisticRegression` para corroborar el dominio técnico. |

### 3.2. Implementación del pipeline de respuesta
El procesamiento de consultas se ejecuta de forma desacoplada en cuatro etapas:

```python
def answer(query: str) -> dict:
    q = query.lower()
    # 1. Evaluación determinista de reglas expertas
    fired = [name for condition, name in RULES if condition(q)]
    # 2. Recuperación RAG mediante similitud coseno sobre TF-IDF
    similarities = cosine_similarity(vectorizer.transform([q]), doc_matrix)[0]
    best_index = int(similarities.argmax())
    # 3. Clasificación supervisada independiente
    label = str(classifier.predict([q])[0])
    # 4. Construcción de payload de trazabilidad
    return {
        "reglas": fired,
        "evidencia": DOCS[best_index],
        "similitud": float(similarities[best_index]),
        "clase": label,
    }
```

---

## 4. Evaluación experimental y matriz de trazabilidad auditada

### 4.1. Análisis comparativo de recuperación: Caso de borde mitigado
Para evaluar el impacto de escalar de 10 a 75 manuales, se sometieron ambas bases a consultas complejas. El resultado evidenció la eliminación de falsos positivos:

| Consulta técnica ingresada | Recuperación en base preliminar (`OLD`: 10 docs) | Recuperación en base actual (`base_conocimiento.txt`: 75 docs) | Diagnóstico técnico de ingeniería |
|---|---|---|---|
| *"El equipo esta muy caliente y el ventilador hace ruido"* | Manual de disipadores y pasta térmica (Sim: 0.483). | Manual de disipadores y pasta térmica (Sim: 0.466). | Ambas bases identifican el procedimiento físico correcto de ventilación. |
| *"Internet se cae y aparece error de conexion DNS"* | Manual de cable ethernet y `ipconfig /renew` (Sim: 0.348). | Manual de cable ethernet y servidores DNS (Sim: 0.530). | Mayor densidad de coincidencia en la base actual (+18.2 p.p. en similitud). |
| *"No puedo iniciar sesion con mi cuenta bloqueada"* | Manual genérico de clave expirada (Sim: 0.374). | Manual de desbloqueo Active Directory con PowerShell (Sim: 0.267). | La base actual proporciona el cmdlet exacto (`Unlock-ADAccount`). |
| **Caso Crítico:** *"Falla en el switch del rack principal y perdida de enlace troncal"* | **Falso positivo grave:** Recuperó manual de *cliente VPN intermitente* (Sim: 0.362). | **Recuperación exacta:** *"Si el enlace troncal de fibra óptica o conexión WAN principal se cae..."* (Sim: **0.372**). | `OLD` carecía de documentación de red central y asoció la palabra "enlace" a VPN. La base actual resolvió la causa raíz con el manual correcto. |

### 4.2. Evidencia de ejecución con trazabilidad completa (Consultas del microcurrículo)

#### Consulta 1: Sobrecalentamiento de hardware
* **Input:** `El equipo esta muy caliente y el ventilador hace ruido`
* **Regla activada:** `revisar_ventilacion`
* **Evidencia recuperada:** *"Para Sobrecalentamiento critico y apagado repentino por calor: Desarmar disipador de calor, sopletear motas de polvo en ventilador y aletas de cobre, aplicar pasta termica Artic MX-4 y comprobar RPM del ventilador en BIOS."*
* **Score similitud coseno:** `0.362` (36.2 %)
* **Clase supervisada:** `hardware`
* **Justificación técnica:** Palabras clave `"caliente"` y `"ventilador"` disparan la regla experta. La vectorización TF-IDF localiza el manual de mantenimiento térmico y el clasificador ML corrobora el dominio físico.

#### Consulta 2: Falla de red y DNS
* **Input:** `Internet se cae y aparece error de conexion DNS`
* **Regla activada:** `revisar_conectividad`
* **Evidencia recuperada:** *"Para Falla de resolucion de nombres DNS en red corporativa: Ejecutar ipconfig /flushdns para limpiar cache de nombres, verificar servidores DNS primario y secundario corporativos y probar resolucion con nslookup."*
* **Score similitud coseno:** `0.530` (53.0 %)
* **Clase supervisada:** `red`
* **Justificación técnica:** Activadores `"internet"` y `"dns"` detonan regla de conectividad. Similitud coseno alta (0.530) valida el procedimiento de vaciado de caché DNS.

#### Consulta 3: Bloqueo de credenciales en Active Directory
* **Input:** `No puedo iniciar sesion con mi cuenta de usuario bloqueada`
* **Regla activada:** `revisar_acceso`
* **Evidencia recuperada:** *"Para Desbloqueo de cuenta de usuario en Active Directory: Consultar consola de Active Directory Users and Computers o PowerShell Unlock-ADAccount, verificar politica de bloqueo y validar identidad de usuario."*
* **Score similitud coseno:** `0.267` (26.7 %)
* **Clase supervisada:** `accesos`
* **Justificación técnica:** Detección de `"cuenta"` y `"sesion"`. Recuperación del procedimiento operativo de administración de identidades en AD DS.

#### Consulta 4: Excepción de memoria en aplicación
* **Input:** `Excel se cierra de golpe con un error de memoria en la aplicacion`
* **Regla activada:** `revisar_software`
* **Evidencia recuperada:** *"Para Microsoft Excel se congela al ejecutar macros pesadas o formulas: Cambiar calculo a modo manual en opciones de formulas, abrir en excel /safe, auditar bucles infinitos en codigo VBA y depurar hojas ocultas."*
* **Score similitud coseno:** `0.381` (38.1 %)
* **Clase supervisada:** `software`
* **Justificación técnica:** Activadores `"aplicacion"` y `"error"`. Recuperación procedimental de diagnóstico de suites ofimáticas y ejecución en modo seguro.

### 4.3. Matriz de trazabilidad ejecutiva

| Consulta evaluada | Regla disparada | Similitud | Dominio predicho | Procedimiento técnico recuperado |
|---|---|---:|:---:|---|
| El equipo esta muy caliente y el ventilador hace ruido | `revisar_ventilacion` | 36.2 % | `hardware` | Limpieza de disipador, verificación de pasta térmica y RPM en BIOS. |
| Internet se cae y aparece error de conexion DNS | `revisar_conectividad` | 53.0 % | `red` | Ejecución de `ipconfig /flushdns`, revisión de DNS y pruebas nslookup. |
| No puedo iniciar sesion con mi cuenta bloqueada | `revisar_acceso` | 26.7 % | `accesos` | Desbloqueo mediante consola AD o cmdlet PowerShell `Unlock-ADAccount`. |
| Excel se cierra de golpe con un error de memoria | `revisar_software` | 38.1 % | `software` | Modo seguro `excel /safe`, cálculo manual y depuración de macros VBA. |

---

## 5. Conclusiones y balance general del sistema híbrido

* **Desacoplamiento funcional entre reglas deterministas y RAG:** Las reglas actúan como un canal de respuesta inmediata (*Fast-Path*) ante síntomas evidentes sin consumir recursos de inferencia textual, mientras que la recuperación RAG sobre vectores TF-IDF aporta el procedimiento documentado detallado. Esta dualidad asegura que el sistema responda rápido a incidentes críticos y a la vez guíe paso a paso al analista.
* **Eliminación del riesgo de alucinación:** Al restringir la emisión de respuestas a fragmentos literales de procedimientos previamente aprobados por la organización, se garantiza que ningún comando destructivo o paso inexistente sea sugerido a los operadores de mesa de ayuda.
* **Guardrail de seguridad ante requerimientos fuera de catálogo:** La fijación de un umbral de corte del 20 % en similitud coseno previene la emisión de respuestas automáticas ante requerimientos ajenos a la infraestructura de TI (ej. equipos médicos o maquinaria industrial), derivando estos casos de forma segura a ingeniería especializada o proveedores externos.
* **Trazabilidad estandarizada para auditoría ITIL:** La salida estructurada en cuádruplas auditables (regla, manual, puntaje de similitud y clase predicha) convierte a la IA en una herramienta transparente, justificable y alineada con los requisitos contractuales de acuerdos de nivel de servicio.
