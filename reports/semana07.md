# Semana 07: Representaciones del reconocimiento en Inteligencia Artificial (Soporte TI)

## 1. Alcance técnico y principio fundamental

En los fundamentos de la Inteligencia Artificial existe un principio rector esencial: **"Reconocer exige representar"**. 

Un sistema computacional no interactúa de manera directa con los servidores físicos, cables o sistemas operativos; en su lugar, procesa **representaciones abstractas** diseñadas para capturar las propiedades clave de un fenómeno y filtrar el ruido innecesario.

Toda elección de una representación implica un compromiso (*trade-off*): **seleccionar cierta información útil implica inevitablemente perder otros detalles del fenómeno**.

En este módulo adaptamos al proyecto del **Asistente de Soporte TI** tres formas fundamentales de representar la realidad de los sistemas:

1. **Representación Numérica (Espacio vectorial en $\mathbb{R}^n$):** Modela magnitudes métricas continuas de rendimiento de servidores (temperatura, carga, errores) y evalúa qué tan lejos están de una línea base deseable mediante distancias geométricas (norma euclidiana $L_2$).
2. **Representación Simbólica (Lógica y conjuntos de hechos):** Modela conceptos cualitativos y relaciones causales discretas mediante hechos y reglas condicionales (`.issubset()`), ofreciendo diagnósticos totalmente explicables (*Explainable AI - XAI*).
3. **Reconocimiento mediante Autómata (Autómata Finito Determinista - DFA):** Modela la dinámica temporal de eventos o trazas de logs, reconociendo secuencias críticas de alarma (patrón `'01'`) sin necesidad de memoria arbitraria.
4. **Puente Híbrido:** Transductor sensorial que convierte lecturas analógicas continuas en hechos simbólicos discretos a través de umbrales operativos (SLAs).

---

## 2. Las tres representaciones explicadas de manera simple

### 2.1 Representación Numérica: Telemetría y distancias en servidores

En el monitoreo de infraestructura de TI, medimos magnitudes numéricas de los servidores en tiempo real. En nuestro sistema, cada observación se almacena en un vector de tres dimensiones:

```python
sample = np.array([72.0, 0.85, 3.0])
```

Cada posición tiene un significado concreto:
* `72.0`: Temperatura actual del procesador (72 °C).
* `0.85`: Nivel de uso o carga de la CPU (85 %).
* `3.0`: Tasa de errores observada (3 errores por minuto).

Para saber si el servidor opera en condiciones normales, definimos un vector de referencia saludable según el SLA corporativo:

```python
reference = np.array([70.0, 0.80, 2.0])
```

#### ¿Cómo compara el sistema ambos estados?
1. **Diferencia vectorial (`sample - reference`):** Resta cada valor con su correspondiente de referencia:
   $$\Delta \vec{x} = [72.0 - 70.0, \; 0.85 - 0.80, \; 3.0 - 2.0] = [2.0, \; 0.05, \; 1.0]$$
2. **Cálculo de la distancia euclidiana (`np.linalg.norm()`):** Mide la longitud de la discrepancia sumando los cuadrados y calculando la raíz cuadrada:
   $$\text{Distancia} = \sqrt{2.0^2 + 0.05^2 + 1.0^2} = \sqrt{4 + 0.0025 + 1} = \sqrt{5.0025} \approx 2.237$$

**Utilidad práctica:** Un valor numérico de distancia cercano a `0.0` indica estabilidad; distancias elevadas disparan alertas automáticas de anomalía estadística.

---

### 2.2 Representación Simbólica: Razonamiento mediante hechos y reglas

En lugar de calcular distancias matemáticas, la representación simbólica razona con **conceptos e ideas cualitativas**.

Los síntomas detectados se almacenan como un conjunto de hechos afirmados (`facts`):

```python
facts = {"temperatura_alta", "carga_alta", "errores_presentes"}
```

Para inferir un diagnóstico, el sistema evalúa reglas lógicas de producción utilizando la operación de subconjuntos (`.issubset()`):

```python
if {"temperatura_alta", "carga_alta"}.issubset(facts):
    print("Conclusión simbólica: riesgo_termico")
```

El método `.issubset()` verifica si todas las premisas requeridas por la regla están presentes dentro de los hechos conocidos. Si es así, se emite la conclusión.

#### Catálogo ampliado de reglas para Soporte TI:
* **Riesgo térmico:** Si `{"temperatura_alta", "carga_alta"}` $\subseteq$ `facts` $\implies$ `"riesgo_termico"`.
* **Degradación de servicio:** Si `{"carga_alta", "errores_presentes"}` $\subseteq$ `facts` $\implies$ `"degradacion_servicio"`.
* **Inestabilidad de hardware:** Si `{"temperatura_alta", "errores_presentes"}` $\subseteq$ `facts` $\implies$ `"inestabilidad_hardware"`.
* **Incidente crítico P1:** Si `{"temperatura_alta", "carga_alta", "errores_presentes"}` $\subseteq$ `facts` $\implies$ `"incidente_critico_p1"`.

**Utilidad práctica:** Mientras que la distancia $2.237$ no le dice a un técnico qué hacer, la conclusión `"riesgo_termico"` o `"incidente_critico_p1"` ofrece una explicación clara, auditable y directamente accionable.

---

### 2.3 Reconocimiento por Autómatas: Análisis de logs y eventos temporales

Para vigilar flujos de logs o eventos cronológicos, utilizamos un **Autómata Finito Determinista (DFA)**. 

El autómata analiza cadenas de símbolos provenientes de los sensores del servidor:
* `'0'`: Pulso de latido normal (*heartbeat OK*).
* `'1'`: Evento de degradación o advertencia de fallo.

El objetivo del autómata `accepts_01(text)` es detectar si la secuencia de eventos culmina exactamente en el patrón crítico `'01'` (un período que parecía normal seguido de un fallo súbito no recuperado).

#### Estados del autómata:
* `q0`: Estado inicial / operación regular.
* `q1`: Se acaba de leer un `'0'` (posible inicio del patrón de alerta).
* `q2`: Estado de aceptación. Se leyó un `'1'` viniendo de `q1`, completando la secuencia `'01'`.

#### Tabla de transiciones

| Estado actual | Símbolo leído | Siguiente estado | Significado operativo |
|---|---:|---|---|
| `q0` | `0` | `q1` | Se detecta un latido normal. El autómata queda preparado para verificar si el siguiente evento es un fallo. |
| `q0` | `1` | `q0` | Se registra un fallo sin un `0` inmediatamente anterior. No se completa el patrón crítico `01`. |
| `q1` | `0` | `q1` | Continúan los latidos normales. El último símbolo sigue siendo `0`, por lo que permanece a la espera de un posible `1`. |
| `q1` | `1` | `q2` | Se completa el patrón crítico `01`: un latido normal seguido inmediatamente por un evento de fallo. |
| `q2` | `0` | `q1` | Después de detectar `01`, aparece un nuevo latido normal. Este `0` puede iniciar un nuevo patrón crítico. |
| `q2` | `1` | `q0` | Después de detectar `01`, aparece otro fallo. Como el último símbolo ya no es `0`, el patrón `01` deja de estar activo. |

> **Estado de aceptación:** `q2`.  
> Una cadena es aceptada cuando, después de procesar todos sus símbolos, el autómata termina en `q2`. Esto significa que la secuencia termina con el patrón `01`.

#### Ejemplo paso a paso con la cadena `'1101'`:
1. Inicia en `q0`.
2. Lee `'1'` $\to$ va a `q0`.
3. Lee `'1'` $\to$ va a `q0`.
4. Lee `'0'` $\to$ pasa a `q1`.
5. Lee `'1'` $\to$ pasa a `q2` (Estado de aceptación).
6. **Resultado:** `True` (Secuencia aceptada, alerta activada).

En cambio, ante `'1110'`, culmina en `q1` $\ne$ `q2` $\implies$ **Resultado:** `False` (Rechazada).

---

### 2.4 Puente Híbrido: De lecturas continuas a hechos lógicos

Para unir ambos mundos, implementamos la función `discretizar_telemetria()`, que actúa como sensor lógico comparando el vector continuo con umbrales de SLA:

```python
def discretizar_telemetria(sample: np.ndarray) -> Set[str]:
    temp, carga, errores = sample[0], sample[1], sample[2]
    facts = set()
    if temp >= 71.0: facts.add("temperatura_alta")
    if carga >= 0.82: facts.add("carga_alta")
    if errores >= 2.5: facts.add("errores_presentes")
    return facts
```

Permite que una lectura analógica como `[72.0, 0.85, 3.0]` se convierta automáticamente en los hechos `{"temperatura_alta", "carga_alta", "errores_presentes"}` y detone los diagnósticos correspondientes.

---

## 3. Matriz comparativa formal de representaciones

| Criterio de comparación | 1. Representación Numérica | 2. Representación Simbólica | 3. Reconocimiento por Autómata (DFA) |
|---|---|---|---|
| **Formato del dato** | Vector de magnitudes continuas $\vec{x} \in \mathbb{R}^n$ (ej. `[72.0, 0.85, 3.0]`). | Conjunto discreto de símbolos/conceptos (ej. `{"temperatura_alta", "carga_alta"}`). | Cadena finita de eventos temporales $\Sigma^*$ (ej. `"1101"`). |
| **Operación matemática base** | Diferencia vectorial y norma euclidiana $\Vert{}\vec{x} - \vec{y}\Vert{}_2$. | Inclusión de conjuntos $A \subseteq B$ e inferencia lógica. | Transición de estados $\delta(q, \sigma)$ sobre un grafo de estados. |
| **¿Qué preguntas responde?** | *¿Qué tan desviado está el servidor de su estado saludable? ¿Hay anomalía métrica?* | *¿Cuál es la causa raíz del incidente? ¿Qué reglas de atención o escalamiento aplican?* | *¿Ocurrió la secuencia crítica de eventos en el orden temporal exacto previsto?* |
| **Ventajas técnicas** | - Admite mediciones precisas y gradaciones finas.<br>- Base para modelos de regresión, redes neuronales y clustering.<br>- Muy veloz mediante operaciones vectorizadas (`numpy`). | - Totalmente transparente y explicable (*Explainable AI*).<br>- Fácil de auditar por ingenieros y comités de soporte.<br>- No se ve afectada por diferencias de escala entre variables. | - Tiempo de ejecución estrictamente lineal $O(N)$.<br>- Memoria constante $O(1)$ (solo recuerda el estado actual).<br>- Ideal para procesar flujos masivos de logs en tiempo real. |
| **Limitaciones técnicas** | - Opacidad semántica: la distancia por sí sola no indica qué componente falló.<br>- Requiere normalización si las unidades son heterogéneas. | - Umbrales rígidos (un valor de 70.9 °C no activa la regla aunque esté muy cerca).<br>- Dificultad para modelar grados de severidad continuos. | - Solo reconoce lenguajes regulares; no puede contar eventos arbitrarios.<br>- No retiene el contexto previo más allá del estado actual. |
| **¿Qué información se pierde?** | **Se pierde la semántica cualitativa:** Dos problemas completamente distintos pueden dar la misma distancia matemática. | **Se pierde la magnitud continua:** No distingue entre una temperatura de 71.5 °C y una de 98.0 °C (ambas son `"temperatura_alta"`). | **Se pierde el historial y la duración:** No sabe qué camino exacto se tomó en el pasado ni cuánto tiempo duró cada estado. |

---

## 4. Diagrama del flujo híbrido integrado y despacho automático de tickets

```
┌─────────────────────────────────┐
│   Telemetría Numérica (Equipo)  │
│   sample = [72.0, 0.85, 3.0]    │
│   (CPU °C, RAM/CPU %, Errores)  │
└───────────────┬─────────────────┘
                │
                ├─────────────────────────────────────────┐
                ▼                                         ▼
┌───────────────────────────────┐         ┌───────────────────────────────┐
│     Métrica Euclidiana        │         │ Puente de Discretización      │
│  ||sample - baseline||_2      │         │ (Umbrales de SLA en Python)   │
│  Distancia = 2.237            │         └───────────────┬───────────────┘
└───────────────┬───────────────┘                         │
                │                                         ▼
                │                         ┌───────────────────────────────┐
                │                         │      Hechos Simbólicos        │
                │                         │  {"temperatura_alta",         │
                │                         │   "carga_alta",               │
                │                         │   "errores_presentes"}        │
                │                         └───────────────┬───────────────┘
                │                                         │
                │                                         ▼
                │                         ┌───────────────────────────────┐
                │                         │ Inferencia Lógica (.issubset) │
                │                         │ -> riesgo_termico             │
                │                         │ -> degradacion_servicio       │
                │                         │ -> incidente_critico_p1       │
                │                         └───────────────┬───────────────┘
                │                                         │
                ▼                                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               EVALUACIÓN INTEGRAL DE SALUD DEL EQUIPO                   │
│   ¿Distancia > 1.5?  O  ¿Hay diagnósticos?  O  ¿Autómata detectó 01?     │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                ┌───────────────────┴───────────────────┐
                ▼ (Sí: No Saludable)                    ▼ (No: Saludable)
┌─────────────────────────────────────────┐   ┌───────────────────────────┐
│     DESPACHO AUTOMÁTICO DE TICKET       │   │   OPERACIÓN NORMAL        │
│ • ID: TCK-28527 (Prioridad: ALTA)       │   │ • Métricas dentro de SLA  │
│ • Equipo: WS-DISENO-CAD-03              │   │ • No requiere ticket      │
│ • Acción: Limpieza disipador / pasta CPU│   └───────────────────────────┘
└─────────────────────────────────────────┘
```

---

## 5. Evidencia de ejecución reproducible

### 5.1 Ejecución del módulo principal con simulación en consola (`python src/semana07_representaciones.py`)

```text
======================================================================
MONITORIZACION Y RECONOCIMIENTO TI - SEMANA 07
======================================================================
1. Numerica (Distancia SLA): 2.237 | Muestra: [72.0, 0.85, 3.0]
2. Simbolica (Diagnosticos): ['riesgo_termico', 'degradacion_servicio', 'inestabilidad_hardware', 'incidente_critico_p1']
3. Automata DFA (Patron 01): 1101->True, 1110->False, 0001->True

======================================================================
ESTADO DE EQUIPOS EN TIEMPO REAL
======================================================================

[EQUIPO: PC-DIRECCION-01]
  * Telemetria:      CPU: 70.0C | Carga: 80% | Errores: 2.0/min
  * Logs temporales: '0000'
  * Estado:          [OK] SALUDABLE (Dentro de SLA)
----------------------------------------------------------------------

[EQUIPO: WS-DISENO-CAD-03]
  * Telemetria:      CPU: 72.0C | Carga: 85% | Errores: 3.0/min
  * Logs temporales: '1101'
  * Estado:          [ALERTA] NO SALUDABLE (Anomalia detectada)
  * Ticket generado: TCK-44968 (Prioridad: ALTA)
  * Diagnostico:     riesgo_termico, degradacion_servicio, inestabilidad_hardware, incidente_critico_p1
  * Alerta automata: SI (Patron 01 detectado)
  * Accion sugerida: Verificar pasta termica, limpieza de disipador y ventilador de CPU. | Inspeccionar procesos fugitivos de alta carga y liberar memoria RAM. | Ejecutar diagnostico SMART de disco y test de modulos de memoria. | Alerta automata (01): aislar equipo para evitar corte abrupto no programado.
----------------------------------------------------------------------

[EQUIPO: SRV-BASE-DATOS-02]
  * Telemetria:      CPU: 76.5C | Carga: 92% | Errores: 5.0/min
  * Logs temporales: '0001'
  * Estado:          [ALERTA] NO SALUDABLE (Anomalia detectada)
  * Ticket generado: TCK-38524 (Prioridad: ALTA)
  * Diagnostico:     riesgo_termico, degradacion_servicio, inestabilidad_hardware, incidente_critico_p1
  * Alerta automata: SI (Patron 01 detectado)
  * Accion sugerida: Verificar pasta termica, limpieza de disipador y ventilador de CPU. | Inspeccionar procesos fugitivos de alta carga y liberar memoria RAM. | Ejecutar diagnostico SMART de disco y test de modulos de memoria. | Alerta automata (01): aislar equipo para evitar corte abrupto no programado.
----------------------------------------------------------------------
======================================================================


## 6. Conclusiones

1. **No existe una representación universal superior:** La representación numérica es indispensable para detectar anomalías sutiles en datos continuos; la simbólica es necesaria para generar explicaciones comprensibles ante auditorías y operadores humanos; y los autómatas son la herramienta idónea para vigilar secuencias cronológicas de logs de forma ultra eficiente.
2. **El poder de la arquitectura híbrida en la Mesa de Ayuda:** Al combinar representaciones mediante un puente de discretización y un autómata temporal, el Asistente de Soporte TI es capaz de evaluar la salud integral de estaciones y servidores, notificando al técnico en el instante exacto del fallo y generando tickets de remediación automáticos sin intervención manual ni falsos positivos.