# Semana 04: marco tecnológico de IA aplicado al soporte TI

## 1. Problema del proyecto

El proyecto acumulativo es un **Asistente de soporte TI**. La Semana 02 clasifica el texto de un ticket por categoría, prioridad e incidente; la Semana 03 identifica las técnicas de IA relacionadas con el dominio. En esta semana se agrega un planificador que parte de un ticket previamente clasificado y busca una secuencia razonable de acciones hasta el estado `incidente_resuelto`.

El problema elegido consiste en seleccionar la secuencia de atención con menor costo entre alternativas como consultar la base de conocimiento, revisar cambios recientes, ejecutar un diagnóstico, aplicar una solución, validar el servicio o escalar a un especialista.

La integración con la Semana 02 es actualmente **conceptual**: `ticket_clasificado` representa la salida que produciría el modelo, pero `semana04_astar.py` todavía no importa ni ejecuta `semana02_fundamentos.py`. Los programas permanecen independientes. Una integración futura deberá recibir directamente la categoría, la prioridad y el indicador de incidente para seleccionar el grafo y ajustar sus costos.

## 2. Formulación como espacio de estados

| Elemento | Representación en el proyecto |
|---|---|
| Estado inicial | `ticket_clasificado`: representa un ticket que se considera previamente clasificado. |
| Estados posibles | Etapas del soporte, por ejemplo `consultar_base_conocimiento`, `diagnostico_guiado`, `revertir_cambio` y `validar_servicio`. |
| Acciones u operadores | Ejecutar el paso de atención que conecta el estado actual con un sucesor. |
| Transición | Pasar a la siguiente etapa válida y sumar su costo. |
| Sucesores | Acciones disponibles en `SUPPORT_GRAPH` que no estén bloqueadas. |
| Meta | `incidente_resuelto`. |
| Costo de camino | Suma de unidades de esfuerzo de cada transición. Un paso automático cuesta menos que un escalamiento. |
| Heurística | Estimación optimista de las unidades de esfuerzo que faltan para resolver el incidente. |
| Selección | A* expande primero el estado con menor `f(n) = g(n) + h(n)`. |

### Adaptación del ejemplo de cuadrícula

La estructura del algoritmo presentado en clase se conservó. Lo que cambió fue la representación del dominio:

| Cuadrícula de la guía | Grafo del asistente de soporte TI |
|---|---|
| Una coordenada `(fila, columna)` | Una etapa del proceso de soporte. |
| `START = (0, 0)` | `START = "ticket_clasificado"`. |
| `GOAL = (4, 4)` | `GOAL = "incidente_resuelto"`. |
| Moverse arriba, abajo, izquierda o derecha | Ejecutar una acción de diagnóstico o solución. |
| `neighbors(node)` genera celdas vecinas | `neighbors()` genera transiciones registradas en `SUPPORT_GRAPH`. |
| Una celda `#` es un obstáculo | Un estado bloqueado es una acción no disponible. |
| Cada movimiento cuesta 1 | Cada transición tiene un costo de esfuerzo diferente. |
| Distancia Manhattan | Estimación del esfuerzo mínimo restante. |

Se mantienen `heapq`, la frontera priorizada, `came_from`, el costo acumulado y la reconstrucción de la ruta. Por ello se trata de una adaptación del ejemplo y no de un algoritmo diferente. La modificación de obstáculos solicitada en el ejemplo se representa mediante el bloqueo de acciones o estados y se comprueba observando el cambio de ruta.

### Grafo de decisiones

El grafo contiene tres rutas principales:

1. Consultar conocimiento y aplicar una solución conocida.
2. Verificar un cambio reciente y revertirlo.
3. Realizar diagnóstico guiado, aplicar una corrección local o escalar.

Después de cualquier corrección se debe validar el servicio antes de declarar el incidente resuelto. Un estado bloqueado representa una acción no disponible o no aplicable al ticket actual.

## 3. Pertinencia de A*

A* es pertinente porque el asistente debe elegir una ruta dentro de un conjunto de acciones con costos diferentes. No basta con seleccionar el siguiente paso mediante una regla aislada: es necesario considerar el costo ya acumulado `g(n)` y una estimación de lo que todavía falta `h(n)`.

Los valores de `HEURISTIC` se obtuvieron a partir de los costos definidos para el escenario base. Se calcularon hacia atrás desde la meta, tomando en cada estado la alternativa ideal de menor esfuerzo:

| Estado | `h(n)` | Cálculo o justificación |
|---|---:|---|
| `incidente_resuelto` | 0 | Ya se alcanzó la meta. |
| `validar_servicio` | 1 | Un paso de costo 1 hasta la meta. |
| `aplicar_solucion_conocida` | 2 | Llegar a validación cuesta 1 y finalizar cuesta 1. |
| `revertir_cambio` | 2 | Llegar a validación cuesta 1 y finalizar cuesta 1. |
| `reiniciar_componente` | 3 | Llegar a validación cuesta 2 y finalizar cuesta 1. |
| `ajustar_configuracion` | 2 | Llegar a validación cuesta 1 y finalizar cuesta 1. |
| `escalar_especialista` | 3 | Llegar a validación cuesta 2 y finalizar cuesta 1. |
| `diagnostico_guiado` | 5 | Mínimo entre reiniciar `2 + 3`, ajustar `3 + 2` o escalar `6 + 3`. |
| `consultar_base_conocimiento` | 4 | Aplicar la solución cuesta 2 y desde allí faltan 2. |
| `verificar_cambio_reciente` | 5 | Revertir cuesta 3 y desde allí faltan 2. |
| `ticket_clasificado` | 6 | Consultar cuesta 2 y desde allí faltan 4. |

En el grafo base estos valores coinciden con el costo mínimo restante. Cuando una acción se encarece o se bloquea, continúan funcionando como una estimación optimista. La prueba automatizada verifica la consistencia en cada transición:

```text
h(estado) <= costo(estado, sucesor) + h(sucesor)
```

Al ser consistente, la heurística también es admisible y no sobreestima el costo óptimo en este grafo. Por ello A* conserva la garantía de encontrar la solución de menor costo cuando existe una ruta. Los valores representan unidades relativas de esfuerzo y no tiempos históricos reales.

## 4. Funcionamiento del algoritmo

`semana04_astar.py` adapta el código de la presentación:

1. La frontera es una cola de prioridad administrada con `heapq`.
2. `cost` almacena `g(n)`, el costo real acumulado.
3. `HEURISTIC` proporciona `h(n)`.
4. La prioridad se calcula como `new_cost + HEURISTIC[nxt]`.
5. `came_from` registra las transiciones para reconstruir la secuencia final.
6. Los estados bloqueados no se generan como sucesores.

## 5. Casos de prueba de A*

### Caso 1: solución conocida disponible

- **Entrada:** grafo normal, sin estados bloqueados.
- **Resultado:** `ticket_clasificado -> consultar_base_conocimiento -> aplicar_solucion_conocida -> validar_servicio -> incidente_resuelto`.
- **Costo:** 6 unidades.
- **Estados explorados:** 5.
- **Resultado esperado:** utilizar primero una solución ya documentada.
- **Explicación:** es la ruta válida de menor costo; evita diagnóstico y escalamiento innecesarios.

### Caso 2: solución conocida costosa

- **Entrada:** el costo de aplicar la solución conocida aumenta de 2 a 8.
- **Resultado:** `ticket_clasificado -> verificar_cambio_reciente -> revertir_cambio -> validar_servicio -> incidente_resuelto`.
- **Costo:** 7 unidades.
- **Estados explorados:** 6.
- **Resultado esperado:** cambiar de ruta porque la alternativa conocida dejó de ser conveniente.
- **Explicación:** el cambio de costo modifica coherentemente la solución; revisar y revertir un cambio reciente es ahora más económico.

### Caso 3: incidente complejo con restricciones

- **Entrada:** se bloquean solución conocida, reversión, reinicio y ajuste de configuración.
- **Resultado:** `ticket_clasificado -> diagnostico_guiado -> escalar_especialista -> validar_servicio -> incidente_resuelto`.
- **Costo:** 12 unidades.
- **Estados explorados:** 7.
- **Resultado esperado:** escalar cuando las acciones locales no están disponibles.
- **Explicación:** la ruta es más costosa, pero es la única alternativa válida que permanece en el grafo.

Los tres resultados coinciden con los valores esperados y se comprueban mediante pruebas automatizadas.

## 6. Evidencia de ejecución

### A*

```text
Caso 1 - solución conocida disponible
Ruta: ticket_clasificado -> consultar_base_conocimiento -> aplicar_solucion_conocida -> validar_servicio -> incidente_resuelto
Costo: 6
Estados explorados: 5

Caso 2 - solución conocida costosa
Ruta: ticket_clasificado -> verificar_cambio_reciente -> revertir_cambio -> validar_servicio -> incidente_resuelto
Costo: 7
Estados explorados: 6

Caso 3 - incidente complejo con restricciones
Ruta: ticket_clasificado -> diagnostico_guiado -> escalar_especialista -> validar_servicio -> incidente_resuelto
Costo: 12
Estados explorados: 7
```

La evidencia demuestra más que una ejecución sin errores: al aumentar un costo cambia la ruta elegida, y al restringir acciones el algoritmo encuentra una alternativa coherente.

### Minimax

```text
Tablero de referencia: ['X', 'O', 'X', 'O', 'X', ' ', ' ', ' ', 'O']
Utilidad por posición: {5: 0, 6: 1, 7: 0}
Mejor posición para X: 6

Tablero modificado: ['X', 'X', ' ', 'O', 'O', ' ', ' ', ' ', ' ']
Utilidad por posición: {2: 1, 5: 0, 6: -1, 7: -1, 8: -1}
Mejor posición para X: 2
```

## 7. Problemas y demostraciones automatizadas

La formulación convierte una situación del dominio de soporte en una estructura que el computador puede explorar mediante estados, transiciones, restricciones, costos y una meta verificable.

Las pruebas unitarias establecen una configuración inicial, ejecutan el algoritmo y comparan automáticamente la ruta, el costo o la utilidad con el resultado esperado. También comprueban la consistencia de la heurística. Estas pruebas aportan evidencia reproducible del comportamiento del programa, pero no constituyen un demostrador automático de teoremas.

Las seis pruebas de la Semana 04 verifican:

1. La ruta de solución conocida.
2. El cambio de ruta cuando aumenta un costo.
3. El escalamiento cuando existen restricciones.
4. La consistencia de la heurística.
5. La decisión Minimax del tablero de referencia.
6. La decisión Minimax del tablero modificado.

## 8. Análisis de Minimax

Minimax **no se aplica directamente** a la resolución ordinaria de tickets. En A* el entorno puede presentar costos y restricciones, pero no existe otro agente racional que elija deliberadamente acciones para empeorar la atención. Confundir una falla técnica con un jugador MIN produciría una representación incorrecta.

Para cumplir la práctica de referencia se implementó el ejemplo de tres en línea de la presentación:

| Elemento | Representación |
|---|---|
| Estado | Configuración de las nueve casillas. |
| Acciones | Colocar una marca en una casilla vacía. |
| MAX | Jugador `X`, que maximiza la utilidad. |
| MIN | Jugador `O`, que minimiza la utilidad de `X`. |
| Terminal | Victoria de X, victoria de O o empate. |
| Utilidad | `1` si gana X, `-1` si gana O y `0` si empatan. |
| Decisión | Seleccionar la posición con mayor utilidad suponiendo que O responde racionalmente. |

Para el tablero de referencia, las posiciones disponibles obtienen `{5: 0, 6: 1, 7: 0}`. Minimax selecciona la posición 6 porque completa la diagonal 2-4-6 y garantiza una utilidad de 1.

### Tablero modificado

También se probó un segundo estado para verificar que la decisión cambia de forma coherente:

```text
X | X |
---------
O | O |
---------
  |   |
```

Su representación es `["X", "X", " ", "O", "O", " ", " ", " ", " "]`. Las posiciones disponibles obtienen `{2: 1, 5: 0, 6: -1, 7: -1, 8: -1}` y Minimax selecciona la posición 2. Esta jugada completa inmediatamente la primera fila de X y alcanza una utilidad de 1.

### Poda alfa-beta

La poda alfa-beta evita explorar una rama cuando sus resultados ya no pueden mejorar la decisión disponible para MAX o MIN. Si se implementa correctamente, devuelve la misma jugada que Minimax, pero puede evaluar menos estados. Su beneficio depende del orden de exploración de las acciones. En la implementación actual se utiliza Minimax sin poda alfa-beta.

## 9. Complejidad observada

### A*

El grafo contiene 11 estados y 16 transiciones. Con la cola de prioridad utilizada, el costo para este grafo explícito es aproximadamente `O((V + E) log V)` y la memoria es `O(V)`.

| Caso | Estados explorados | Estados disponibles |
|---|---:|---:|
| Solución conocida | 5 | 11 |
| Solución conocida costosa | 6 | 11 |
| Incidente restringido | 7 | 11 |

La heurística permite orientar la búsqueda sin revisar todos los estados del grafo en estos casos, aunque las restricciones obligan a explorar más alternativas.

### Minimax

Minimax tiene crecimiento aproximado `O(b^d)`, donde `b` es la cantidad de jugadas disponibles y `d` la profundidad restante. El tablero de referencia tiene tres posiciones vacías y el tablero modificado tiene cinco. Por ello, el segundo caso genera un árbol de búsqueda potencialmente mayor. La memoria recursiva es `O(d)`.

El programa actual no cuenta los estados evaluados por Minimax; por esta razón no se reporta una cifra de estados explorados para estos dos tableros.

## 10. Archivos relacionados con la Semana 04

| Archivo | Función |
|---|---|
| `src/semana04_astar.py` | A* adaptado a la planificación de soporte y tres configuraciones de ejecución. |
| `src/semana04_minimax.py` | Minimax con el tablero de referencia y un tablero modificado. |
| `tests/test_semana04_busqueda_juegos.py` | Comprueba los tres casos de A*, la heurística y las dos decisiones Minimax. |
| `reports/semana04.md` | Documenta la formulación, los resultados, la evidencia y el análisis. |
| `README.md` | Integra la Semana 04 al repositorio acumulativo. |

No se agregaron dependencias: ambos algoritmos usan la biblioteca estándar de Python.

## 11. Ventajas, limitaciones y mejoras

### Ventajas

- A* produce una secuencia explicable y conserva el costo total.
- Los costos y las restricciones permiten adaptar la decisión al contexto.
- La heurística consistente orienta la exploración sin perder optimalidad.
- El resultado puede auditarse mediante la ruta y los estados explorados.

### Limitaciones y supuestos

- El grafo y sus costos fueron definidos para una demostración académica.
- Se supone que cada acción termina en el estado indicado; no se modela probabilidad de fallo.
- Las unidades de esfuerzo son relativas y no equivalen todavía a minutos reales ni a un SLA.
- El planificador no consume directamente las predicciones de la Semana 02.
- El modelo no aprende nuevas transiciones a partir de tickets históricos.
- En grafos grandes, A* puede consumir memoria al conservar la frontera y los costos.
- Minimax tiene crecimiento exponencial aproximado `O(b^d)` sin poda ni límite de profundidad.

### Posibles mejoras

- Conectar la salida de la Semana 02 con el planificador de la Semana 04.
- Estimar costos a partir de tiempos históricos de resolución.
- Construir grafos diferentes según la categoría y la prioridad.
- Incorporar reintentos, probabilidades y resultados parciales.
- Comparar A* con Dijkstra para medir el efecto de la heurística.
- Implementar poda alfa-beta y contar los estados evitados.

## 12. Reproducción

```bash
python3 src/semana04_astar.py
python3 src/semana04_minimax.py
python3 -m unittest discover -s tests -v
```

## Referencias de la actividad

- *Semana 04 - Marco tecnológico de la inteligencia artificial - Clase*.
- *Guía explicativa - Semana 4 - Marco tecnológico de la inteligencia artificial*.
- Russell, S. y Norvig, P. *Artificial Intelligence: A Modern Approach*.
