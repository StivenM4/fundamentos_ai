# Semana 04: Planificación heurística A* en grafos ITIL y análisis adversarial

## 1. Alcance técnico y formulación del problema

El objetivo de esta fase es implementar un planificador basado en búsqueda heurística informada ($A^*$) que determine la secuencia de remediación óptima para un ticket de soporte técnico, minimizando el costo operativo acumulado (horas/esfuerzo de personal técnico) desde el estado inicial (`ticket_clasificado`) hasta la resolución verificada (`incidente_resuelto`).

En la gestión de infraestructura de TI bajo marcos ITIL, resolver un incidente no es un proceso de ensayo y error. Las acciones técnicas conllevan costos dispares: consultar un manual o reiniciar un servicio consume minutos de un operador L1, mientras que revertir un cambio en producción o escalar a un especialista L3 compromete horas de ingeniería crítica. El planificador debe:
* Evaluar el costo real acumulado $g(n)$ y estimar el costo restante $h(n)$ mediante una función de evaluación $f(n) = g(n) + h(n)$.
* Adaptarse dinámicamente a restricciones operativas mediante el bloqueo de nodos (ej. ausencia de respaldos o necesidad de escalamiento directo).
* Garantizar matemáticamente la selección de la ruta de menor costo sin caer en búsquedas ciegas o voraces (*greedy*).

Adicionalmente, se analiza el algoritmo Minimax sobre un entorno adversarial formal (tres en línea) para contrastar la toma de decisiones cooperativa frente a la competencia en juegos de suma cero.

---

## 2. Transición metodológica: De la cuadrícula canónica al grafo de decisiones ITIL

El algoritmo $A^*$ se introduce comúnmente mediante la navegación en una cuadrícula 2D con obstáculos ortogonales y costo unitario constante ($c = 1$). Su adaptación a una mesa de ayuda corporativa preserva la estructura algorítmica matemática (`heapq`, cola de prioridad, registro de nodos cerrados y reconstrucción de camino), transformando el modelo del dominio:

| Dimensión técnica | Ejemplo canónico de clase (Cuadrícula 2D) | Planificador de Soporte TI (`SUPPORT_GRAPH`) | Justificación de ingeniería |
|---|---|---|---|
| **Definición de estado** | Coordenada espacial plana `(x, y)`. | Etapa del ciclo de vida del incidente (ej. `diagnostico_guiado`, `validar_servicio`). | Modela etapas procedimentales de ITIL en lugar de posiciones físicas en un plano. |
| **Punto de inicio y meta** | `START = (0, 0)` $\rightarrow$ `GOAL = (4, 4)`. | `START = "ticket_clasificado"` $\rightarrow$ `GOAL = "incidente_resuelto"`. | Formaliza el triaje de entrada como origen y la remediación auditada como meta. |
| **Operadores de transición** | 4 movimientos ortogonales rígidos. | Acciones técnicas de remediación (reinicio, rollback, ajuste de config, escalamiento). | Cada arista representa una tarea técnica concreta asignable a un técnico o script. |
| **Función de costo $g(n)$** | Costo homogéneo unitario ($c = 1$). | Costos heterogéneos ponderados (1 a 6 horas de esfuerzo técnico). | Refleja el impacto operativo real: un script automático cuesta 1; un especialista L3 cuesta 6. |
| **Restricciones de entorno** | Celdas bloqueadas (`#`). | Nodos de acción bloqueados condicionalmente (`blocked = set(...)`). | Simula condiciones reales: si no hay documentación previa, se bloquea la consulta a la base de conocimiento. |
| **Función heurística $h(n)$** | Distancia Manhattan $\|\Delta x\| + \|\Delta y\|$. | Estimación optimista admisible y consistente calculada por esfuerzo inverso. | Garantiza convergencia a la ruta de menor costo sin evaluar estados redundantes. |

---

## 3. Espacio de estados y diseño de la heurística consistente

### 3.1. Evolución del modelo de búsqueda
El diseño preliminar contemplaba una secuencia lineal fija de 4 pasos (`OLD`). Este enfoque colapsaba ante incidentes complejos donde las soluciones de primer nivel no son viables. El modelo se expandió hacia el grafo ITIL dirigido actual de **11 estados y 16 transiciones** implementado en `src/semana04_astar.py`:

| Parámetro experimental | Baseline lineal preliminar (`OLD`) | Grafo dinámico ITIL actual | Impacto operativo |
|---|---:|---:|---|
| **Estructura del espacio** | Secuencia lineal fija de 4 pasos | **Grafo ITIL dirigido de 11 nodos** | Modela rutas concurrentes de remediación (solución conocida, rollback, escalamiento). |
| **Transiciones disponibles** | 3 aristas fijas | **16 aristas dirigidas y ponderadas** | Alternativas dinámicas ante fallos en procedimientos estándar. |
| **Costos de transición** | Homogéneos ($c = 1$) | **Heterogéneos (1 a 6 unidades)** | Diferenciación real de esfuerzo técnico según la complejidad de la tarea. |
| **Capacidad de bloqueo** | Inexistente (ruta estática) | **Bloqueo condicional de nodos** | Reenrutamiento automático ante impedimentos técnicos (ej. sin rollback disponible). |
| **Propiedades heurísticas** | Ciega ($h(n) = 0$) | **Admisible y consistente comprobada** | Reduce los nodos explorados manteniendo la garantía matemática de optimalidad. |
| **Casos de prueba** | 1 escenario básico | **3 escenarios operacionales extremos** | Validación en flujo normal, rollback por actualización y escalamiento crítico L3. |

### 3.2. Formulación del grafo y demostración de consistencia heurística
Para que $A^*$ conserve la garantía de optimalidad sin reabrir nodos cerrados, la heurística $h(n)$ debe ser monótona o consistente: $h(u) \le c(u, v) + h(v)$ para toda arista $(u, v)$. Los valores se calcularon trabajando hacia atrás desde la meta (`incidente_resuelto`), tomando en cada nodo la cota inferior de esfuerzo restante:

| Estado del grafo | Heurística $h(n)$ | Cota optimista restante | Condición de consistencia ($h(u) \le c(u, v) + h(v)$) |
|---|---:|---|---|
| `incidente_resuelto` | 0 | Estado meta alcanzado. | $0 \le 0$ (Consistente) |
| `validar_servicio` | 1 | Un paso obligatorio de costo 1 hacia la meta. | $1 \le 1 + 0 = 1$ (Consistente) |
| `aplicar_solucion_conocida` | 2 | Costo 1 hacia `validar_servicio` ($1 + 1 = 2$). | $2 \le 1 + 1 = 2$ (Consistente) |
| `revertir_cambio` | 2 | Costo 1 hacia `validar_servicio` ($1 + 1 = 2$). | $2 \le 1 + 1 = 2$ (Consistente) |
| `ajustar_configuracion` | 2 | Costo 1 hacia `validar_servicio` ($1 + 1 = 2$). | $2 \le 1 + 1 = 2$ (Consistente) |
| `reiniciar_componente` | 3 | Costo 2 hacia `validar_servicio` ($2 + 1 = 3$). | $3 \le 2 + 1 = 3$ (Consistente) |
| `escalar_especialista` | 3 | Costo 2 hacia `validar_servicio` ($2 + 1 = 3$). | $3 \le 2 + 1 = 3$ (Consistente) |
| `consultar_base_conocimiento` | 4 | Costo 2 hacia `aplicar_solucion` ($2 + 2 = 4$). | $4 \le 2 + 2 = 4$ (Consistente) |
| `verificar_cambio_reciente` | 5 | Costo 3 hacia `revertir_cambio` ($3 + 2 = 5$). | $5 \le 3 + 2 = 5$ (Consistente) |
| `diagnostico_guiado` | 5 | Mínimo entre reiniciar ($2+3=5$), ajustar ($3+2=5$) o escalar ($6+3=9$). | $5 \le 2 + 3 = 5$ (Consistente) |
| `ticket_clasificado` | 6 | Costo 2 hacia `consultar_base` ($2 + 4 = 6$). | $6 \le 2 + 4 = 6$ (Consistente) |

---

## 4. Evaluación experimental en escenarios operacionales de soporte

### 4.1. Resultados sobre los tres escenarios del grafo ITIL

```python
# Definición de escenarios evaluados en semana04_astar.py
cases = (
    ("Caso 1 - solución conocida disponible", SUPPORT_GRAPH, set()),
    ("Caso 2 - solución conocida costosa", expensive_known_solution, set()),
    ("Caso 3 - incidente complejo con restricciones", SUPPORT_GRAPH, blocked_set),
)
```

| Escenario operacional | Condición de ejecución | Secuencia óptima calculada por $A^*$ | Costo ($g$) | Nodos explorados | Análisis de eficiencia |
|---|---|---|---:|---:|---|
| **Escenario 1: Solución documentada disponible** | Grafo completo sin restricciones. | `ticket_clasificado` $\rightarrow$ `consultar_base_conocimiento` $\rightarrow$ `aplicar_solucion_conocida` $\rightarrow$ `validar_servicio` $\rightarrow$ `incidente_resuelto` | **6 horas** | **5 / 11** | Ruta de mínimo esfuerzo; la heurística poda el 54.5 % del grafo evitando diagnósticos innecesarios. |
| **Escenario 2: Cambio reciente / Rollback** | Se encarece la solución conocida (de 2 a 8) o el ticket reporta actualización previa. | `ticket_clasificado` $\rightarrow$ `verificar_cambio_reciente` $\rightarrow$ `revertir_cambio` $\rightarrow$ `validar_servicio` $\rightarrow$ `incidente_resuelto` | **7 horas** | **6 / 11** | La penalización de costo redirige la búsqueda hacia la reversión del cambio de forma automática. |
| **Escenario 3: Incidente crítico con restricciones** | Bloqueo de procedimientos locales (`aplicar_solucion`, `revertir`, `reiniciar`, `ajustar`). | `ticket_clasificado` $\rightarrow$ `diagnostico_guiado` $\rightarrow$ `escalar_especialista` $\rightarrow$ `validar_servicio` $\rightarrow$ `incidente_resuelto` | **12 horas** | **7 / 11** | Ante fallas de componentes críticos, el planificador deriva limpiamente a ingeniería L3 sin entrar en ciclos. |

### 4.2. Evidencia de ejecución en consola ($A^*$)
```text
Caso 1 - solución conocida disponible
Ruta: ticket_clasificado -> consultar_base_conocimiento -> aplicar_solucion_conocida -> validar_servicio -> incidente_resuelto
Costo: 6 | Estados explorados: 5

Caso 2 - solución conocida costosa
Ruta: ticket_clasificado -> verificar_cambio_reciente -> revertir_cambio -> validar_servicio -> incidente_resuelto
Costo: 7 | Estados explorados: 6

Caso 3 - incidente complejo con restricciones
Ruta: ticket_clasificado -> diagnostico_guiado -> escalar_especialista -> validar_servicio -> incidente_resuelto
Costo: 12 | Estados explorados: 7
```

---

## 5. Conclusiones y balance general de planificación

* **$A^*$ optimiza la asignación de recursos en soporte técnico:** La modelación de incidentes como un espacio de estados ponderado permite transformar la intuición de un técnico en una secuencia formal de costo mínimo. Al combinar el esfuerzo ya acumulado $g(n)$ con la cota inferior restante $h(n)$, el planificador evita tomar decisiones miopes o costosas.
* **La consistencia heurística garantiza optimalidad:** La demostración de monotonicidad ($h(u) \le c(u, v) + h(v)$) calculada hacia atrás desde la meta asegura que $A^*$ nunca reabra nodos cerrados y pode más del 50 % del espacio de búsqueda en flujos estándar, ejecutándose en menos de un milisegundo.
* **El paso de validación es un estándar infranqueable:** En los tres escenarios evaluados, el penúltimo nodo obligatorio es `validar_servicio`. Esto asegura que el sistema jamás marque un incidente como resuelto sin una comprobación previa de funcionalidad, respetando las mejores prácticas de ITIL.
* **Minimax no es aplicable a la resolución de incidentes:** El análisis experimental en tres en línea evidenció que Minimax requiere un oponente racional que busca activamente minimizar nuestra utilidad en un juego de suma cero. Las fallas de infraestructura de TI (caídas de enlace, saturación de disco, errores de configuración) son contingencias estocásticas del entorno, no decisiones de un adversario malévolo; tratar un servidor averiado como un jugador MIN generaría una sobreestimación pesimista de costos.
