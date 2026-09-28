# Semana 08: Representaciones del reconocimiento aplicadas al Gestor de Tickets de Soporte TI

## 1. Alcance técnico y criterio de integración

La Semana 08 estudia tres piezas que deben trabajar de forma complementaria:

1. **Reconocimiento mediante redes neuronales artificiales.**
2. **Persistencia de imágenes y metadatos en SQLite.**
3. **Ontologías para representar conceptos y relaciones con significado.**

La idea central es que una predicción aislada no es suficiente. El sistema debe poder conservar evidencia y asociar esa evidencia con conceptos comprensibles dentro del dominio.

El flujo conceptual de la semana es:

```text
ENTRADA
  ↓
MODELO
  ↓
PREDICCIÓN
  ↓
EVIDENCIA PERSISTENTE
  ↓
SIGNIFICADO / ONTOLOGÍA
```

### Decisión metodológica para este proyecto

El repositorio actual está orientado a un **Asistente de Soporte TI**, funcionalmente utilizado como gestor inteligente de tickets. Sin embargo, en el estado actual del proyecto **no existe un corpus etiquetado de capturas de pantalla, fotografías de hardware o imágenes de incidentes TI suficiente para entrenar de manera válida una red neuronal visual propia del dominio**.

Por esta razón, no se fabricará un dataset de imágenes de soporte ni se afirmará que el modelo reconoce fallas visuales reales.

Se adopta la siguiente estrategia:

- La **MLP** se entrena con `load_digits`, exactamente como plantea el material de Semana 08, para demostrar de manera reproducible el funcionamiento de una red neuronal aplicada al reconocimiento de imágenes.
- La **persistencia de evidencia** se adapta al proyecto utilizando exclusivamente los tres casos de telemetría ya definidos en Semana 07.
- A partir de esos casos se generan fichas PNG reproducibles, que funcionan como evidencia visual del estado de cada equipo.
- SQLite conserva tanto el ejercicio base de imágenes como los metadatos propios de soporte TI.
- La ontología conserva las relaciones base de la clase y añade relaciones específicas del gestor de tickets.
- No se conecta falsamente la MLP de dígitos con una predicción de hardware, software, red o accesos. Esa adaptación requerirá posteriormente un conjunto de imágenes TI etiquetado.

---

## 2. Objetivos de Semana 08 dentro del proyecto

Al finalizar esta práctica el repositorio debe poder demostrar:

1. Entrenamiento y validación reproducible de una red neuronal MLP.
2. Persistencia del modelo entrenado.
3. Creación de una base SQLite de imágenes y metadatos.
4. Persistencia de evidencia visual derivada de la telemetría de Semana 07.
5. Construcción de una ontología en un grafo dirigido.
6. Asociación entre una imagen de prueba, una predicción y un concepto.
7. Inclusión de conceptos y relaciones propias del dominio de soporte TI.
8. Exportación completa de la ontología a GraphML.
9. Generación reproducible de todos los artefactos desde un único script.

---

## 3. Dependencias

El script utiliza:

```python
pickle
sqlite3
matplotlib
networkx
scikit-learn
```

`pickle` y `sqlite3` pertenecen a la biblioteca estándar de Python.

El `requirements.txt` actual del repositorio ya contiene `matplotlib` y `scikit-learn`, pero debe verificarse e incorporar `networkx` antes del commit de Semana 08.

Desde el entorno virtual del proyecto:

```bash
python3 -m pip install networkx
```

Después debe agregarse a `requirements.txt` la versión **realmente instalada** en el entorno. No se fija una versión arbitraria en este reporte.

---

## 4. Arquitectura implementada

La práctica separa dos partes para que sea claro qué demuestra la clase y qué se aplica realmente al proyecto.

### 5.1. Flujo neuronal reproducible

```text
load_digits
   ↓
imágenes 8 x 8
   ↓
64 valores numéricos
   ↓
MLPClassifier
   ↓
predicción 0..9
   ↓
accuracy
   ↓
modelo_mlp.pkl
```

### 5.2. Flujo de evidencia propio del proyecto

```text
CASOS SEMANA 07
   ↓
telemetría + logs + estado
   ↓
ficha visual PNG
   ↓
SQLite
   ↓
ontología de soporte TI
   ↓
evidencia trazable
```

La parte de soporte TI no usa la MLP para diagnosticar la telemetría. Las imágenes PNG solo sirven como evidencia visual de los datos de Semana 07; no se usan para entrenar la red neuronal.

---

## 5. Diseño de la base SQLite

El archivo generado es:

```text
artifacts/imagenes.db
```

Se crean dos tablas.

### 6.1. Tabla `images`

Conserva la estructura mínima del ejercicio base:

| Campo | Tipo | Uso |
|---|---|---|
| `id` | INTEGER | Identificador del ejemplo |
| `label` | INTEGER | Etiqueta real del dígito |
| `split` | TEXT | Valor `dataset`, siguiendo el ejercicio de clase |

Se registran los primeros 20 ejemplos de `load_digits`.

### 6.2. Tabla `evidencias_soporte`

Es la adaptación propia del proyecto:

| Campo | Tipo | Significado |
|---|---|---|
| `id` | INTEGER | Identificador interno |
| `equipo_id` | TEXT | Equipo analizado |
| `ruta_imagen` | TEXT | Ruta de la ficha visual generada |
| `estado` | TEXT | `saludable` o `no_saludable` |
| `temperatura_cpu_c` | REAL | Temperatura usada en Semana 07 |
| `carga_servidor_pct` | REAL | Carga usada en Semana 07 |
| `tasa_errores_min` | REAL | Errores por minuto |
| `secuencia_logs` | TEXT | Secuencia utilizada por el DFA |

Esta tabla conserva evidencia del sistema de soporte usando únicamente datos que ya existen en el proyecto.

---

## 6. Ontología

### 7.1. Ontología base

Se conservan las siete relaciones del ejercicio de clase:

```text
digito → tiene_clase → cero
digito → tiene_clase → uno
digito → tiene_clase → dos
modelo_mlp → reconoce → digito
imagen → representa → digito
prediccion → asigna_clase → digito
modelo_mlp → produce → prediccion
```

### 7.2. Integración de una predicción concreta

Para el ejemplo `15`:

```text
imagen_15
   ↓ genera
prediccion_15
   ↓ asigna_clase
digito_5
```

Con la semilla y configuración suministradas por la práctica, el ejemplo 15 es reconocido como clase `5`.

### 7.3. Relaciones propias del Gestor de Tickets

La ontología añade nueve relaciones propias del gestor de tickets:

| Origen | Relación | Destino | Lectura natural |
|---|---|---|---|
| `ticket_soporte` | `puede_incluir` | `evidencia_visual_ti` | Un ticket de soporte puede incluir evidencia visual. |
| `evidencia_visual_ti` | `documenta` | `telemetria_equipo` | La evidencia visual documenta la telemetría del equipo. |
| `telemetria_equipo` | `alimenta` | `diagnostico_simbolico` | La telemetría alimenta el diagnóstico simbólico. |
| `diagnostico_simbolico` | `puede_generar` | `ticket_soporte` | Un diagnóstico puede generar un ticket de soporte. |
| `ticket_soporte` | `pertenece_a` | `categoria_soporte` | El ticket pertenece a una categoría de soporte. |
| `categoria_soporte` | `tiene_clase` | `hardware` | Hardware es una categoría del proyecto. |
| `categoria_soporte` | `tiene_clase` | `software` | Software es una categoría del proyecto. |
| `categoria_soporte` | `tiene_clase` | `red` | Red es una categoría del proyecto. |
| `categoria_soporte` | `tiene_clase` | `accesos` | Accesos es una categoría del proyecto. |

Estas clases ya existen en la formulación acumulativa del proyecto desde Semana 02.

---

## 7. Ejecución

Desde la raíz del repositorio:

```bash
source .venv/bin/activate
python3 src/semana08_red_ontologia.py
```

La ejecución validada del código anterior produce:

```text
Accuracy MLP: 0.9622
Registros load_digits en SQLite: 20
Evidencias soporte en SQLite: 3
Relaciones de ontologia base: 7
Ejemplo MLP: 15 5 digito_5
Relaciones propias del proyecto: 9
Relaciones de ontologia finales: 18
Modelo: artifacts/modelo_mlp.pkl
SQLite: artifacts/imagenes.db
GraphML: artifacts/ontologia.graphml
Evidencias PNG: 3
```

El valor:

```text
Accuracy MLP: 0.9622
```

equivale a aproximadamente:

```text
96.22 %
```

de predicciones correctas sobre el conjunto de prueba de `load_digits`.

Este resultado corresponde al experimento de reconocimiento de dígitos y **no debe interpretarse como precisión de diagnóstico del gestor de tickets**.

---

## 8. Artefactos generados

Después de ejecutar el script deben existir:

```text
artifacts/
├── modelo_mlp.pkl
├── imagenes.db
├── ontologia.graphml
└── evidencias_soporte/
    ├── pc-direccion-01.png
    ├── ws-diseno-cad-03.png
    └── srv-base-datos-02.png
```

### `modelo_mlp.pkl`

Contiene la MLP entrenada con `load_digits`.

### `imagenes.db`

Contiene:

- 20 registros del ejercicio base en `images`;
- 3 registros propios del proyecto en `evidencias_soporte`.

### `ontologia.graphml`

Contiene:

- las siete relaciones base;
- las dos relaciones del ejemplo de predicción;
- las nueve relaciones propias del proyecto.

Total esperado:

```text
18 relaciones
```

### `evidencias_soporte/*.png`

Contiene tres fichas generadas directamente desde los casos de Semana 07.

---

## 9. Corrección aplicada frente al orden del ejemplo de clase

En el ejemplo explicado en Semana 08, el archivo GraphML puede exportarse antes de agregar las relaciones:

```text
imagen_15 → genera → prediccion_15
prediccion_15 → asigna_clase → digito_5
```

Si se guarda el grafo antes, las relaciones agregadas posteriormente existen en memoria pero no aparecen en el archivo ya escrito.

En esta implementación:

```python
nx.write_graphml(G, ARTIFACTS / "ontologia.graphml")
```

se ejecuta **al final**, después de agregar tanto la predicción concreta como las relaciones del proyecto.

Así, `ontologia.graphml` representa realmente el estado final del grafo.

---

## 10. Validación de funcionamiento

El código fue verificado con las siguientes condiciones:

| Validación | Resultado |
|---|---|
| El script termina sin excepción | Correcto |
| La MLP entrena correctamente | Correcto |
| Accuracy visible | `0.9622` |
| `modelo_mlp.pkl` se genera | Correcto |
| `imagenes.db` se genera | Correcto |
| Registros tabla `images` | `20` |
| Registros `evidencias_soporte` | `3` |
| `ontologia.graphml` se genera | Correcto |
| Relaciones base | `7` |
| Relaciones propias del proyecto | `9` |
| Relaciones finales GraphML | `18` |
| Evidencias PNG generadas | `3` |

---

## 11. Relación con las semanas anteriores

La Semana 08 no reemplaza las capacidades desarrolladas anteriormente.

```text
SEMANA 02
Texto del ticket
→ categoría / prioridad / incidente

SEMANA 03
Caso de soporte
→ taxonomía explicable / técnica sugerida

SEMANA 04
Ticket previamente clasificado
→ secuencia de atención A*

SEMANA 05
Consulta
→ regla + evidencia documental + similitud + clase

SEMANA 07
Telemetría + logs
→ representación + diagnóstico + posible ticket

SEMANA 08
Reconocimiento neuronal de referencia
+
evidencia visual persistente
+
ontología
→ predicción demostrable + registro + significado
```

La idea principal es que el proyecto ya no solo entrega un resultado: también guarda evidencia y explica cómo se relaciona esa información dentro del sistema.

---

## 12. Limitaciones

### 14.1. La MLP todavía no reconoce imágenes de incidentes TI

El repositorio no contiene actualmente un conjunto de imágenes etiquetadas de:

- capturas de pantalla;
- errores visuales;
- cableado;
- LEDs de equipos;
- daños físicos;
- otros incidentes visuales de soporte.

Por ello, entrenar una MLP de soporte TI con datos inventados produciría una evidencia académica engañosa.

`load_digits` se conserva como dataset controlado para comprobar la técnica de reconocimiento neuronal.

### 14.2. Las fichas PNG no son entradas de entrenamiento

Las tres imágenes generadas desde Semana 07 son evidencia visual de telemetría.

No se presentan como dataset de entrenamiento.

Tres ejemplos no son suficientes para validar un clasificador visual generalizable.

### 14.3. El accuracy pertenece exclusivamente a `load_digits`

El `96.22 %` no mide:

- calidad del diagnóstico de soporte;
- precisión del clasificador textual de Semana 02;
- calidad del sistema híbrido de Semana 05;
- precisión sobre capturas o fotografías reales.

### 14.4. Siguiente ampliación válida

Para convertir esta arquitectura en un reconocedor visual real del gestor de tickets se requiere primero un dataset propio etiquetado y trazable.

Solo después tendría sentido sustituir `load_digits` por imágenes reales del dominio.

---

## 13. Conclusiones

1. La Semana 08 demuestra correctamente el principio **modelo reconoce, base registra y ontología interpreta**.
2. La red neuronal se mantiene sobre el dataset controlado establecido por la clase, evitando atribuirle capacidades que el proyecto todavía no posee.
3. SQLite amplía la trazabilidad del proyecto almacenando evidencia derivada de casos ya existentes de Semana 07.
4. La ontología agrega más de las cinco relaciones propias solicitadas y las mantiene conectadas con conceptos que ya forman parte del gestor de tickets.
5. Exportar GraphML al final evita perder las relaciones agregadas después de la creación del grafo base.
6. La implementación conserva la continuidad del proyecto sin crear datos de producción inexistentes.

---
