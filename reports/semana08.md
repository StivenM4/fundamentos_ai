# Semana 08: Representaciones del reconocimiento aplicadas al Gestor de Tickets de Soporte TI

## 1. Alcance de la práctica

En la Semana 08 se integran tres elementos principales:

1. **Una red neuronal artificial**, encargada de reconocer imágenes de errores de TI.
2. **Una base de datos SQLite**, utilizada para guardar información de las imágenes usadas en el entrenamiento y en las pruebas.
3. **Una ontología representada como grafo**, que permite relacionar los errores reconocidos con conceptos del sistema de soporte técnico.

La idea principal es que el sistema no se limite a decir qué error cree que aparece en una imagen. También debe poder guardar evidencia de los datos utilizados y relacionar el resultado con el dominio del proyecto.

El flujo general es:

```text
IMAGEN DE ERROR TI
        ↓
PREPARACIÓN DE LA IMAGEN
        ↓
RED NEURONAL MLP
        ↓
CLASE PREDICHA
        ↓
REGISTRO EN SQLITE
        ↓
RELACIONES EN LA ONTOLOGÍA
        ↓
INTEGRACIÓN CON SOPORTE TI
```

A diferencia de una práctica genérica con dígitos, esta implementación trabaja directamente con imágenes relacionadas con el proyecto de soporte TI.

---

## 2. Objetivos de la Semana 08

Con esta práctica se busca:

1. Cargar un conjunto de imágenes de errores de TI.
2. Preparar las imágenes para que puedan ser procesadas por una red neuronal.
3. Entrenar una red neuronal MLP para clasificar cuatro tipos de errores.
4. Separar los datos entre entrenamiento y prueba.
5. Evaluar las predicciones realizadas por el modelo.
6. Guardar el modelo entrenado para poder reutilizarlo.
7. Registrar en SQLite las imágenes utilizadas y su clase real.
8. Construir una ontología sencilla con conceptos relacionados con soporte TI.
9. Relacionar los errores visuales con las categorías utilizadas por el Gestor de Tickets.
10. Exportar toda la estructura de relaciones a un archivo GraphML.

---

## 3. Datos utilizados

Las imágenes se encuentran dentro de:

```text
data/imagenes_errores/
```

y el archivo:

```text
data/imagenes_errores/etiquetas.csv
```

indica qué archivo pertenece a cada clase.

El programa cargó correctamente:

```text
160 imágenes
```

distribuidas en cuatro categorías:

```text
pantalla_azul_bsod
red_desconectada
disco_lleno
error_aplicacion_crash
```

Estas clases representan errores visuales que pueden aparecer durante actividades de soporte técnico.

### Preparación de cada imagen

Antes de utilizar una imagen, el programa realiza tres pasos:

```text
Imagen original
      ↓
Escala de grises
      ↓
32 x 32 píxeles
      ↓
1024 valores numéricos
```

Cada imagen se convierte a escala de grises y después se redimensiona a `32 x 32`.

Como:

```text
32 × 32 = 1024
```

cada imagen termina representada por 1024 números.

Después, los valores de los píxeles se dividen entre `255.0`, de modo que queden aproximadamente entre:

```text
0.0 y 1.0
```

Esto permite que la red neuronal trabaje con valores más uniformes.

---

## 4. División entre entrenamiento y prueba

El código utiliza:

```text
75 % para entrenamiento
25 % para prueba
```

Como existen 160 imágenes:

```text
120 imágenes → entrenamiento
40 imágenes  → prueba
```

El conjunto de entrenamiento sirve para que la red neuronal aprenda patrones.

El conjunto de prueba se reserva para comprobar cómo responde el modelo ante imágenes que no utilizó directamente durante el entrenamiento.

Además, se utiliza una división estratificada, lo que ayuda a conservar una proporción similar de las cuatro clases en ambos grupos.

Conceptualmente:

```text
160 imágenes
      │
      ├── 120 → aprender
      │
      └── 40  → comprobar
```

---

## 5. Reconocimiento mediante la red neuronal MLP

El modelo utilizado es un `MLPClassifier`.

La configuración utilizada contiene dos capas ocultas:

```text
Entrada
1024 valores
     ↓
64 neuronas
     ↓
32 neuronas
     ↓
Clase predicha
```

Las cuatro posibles salidas son:

```text
pantalla_azul_bsod
red_desconectada
disco_lleno
error_aplicacion_crash
```

La red recibe los valores de los píxeles e intenta encontrar patrones que permitan diferenciar un tipo de error de otro.

El entrenamiento se realiza con las 120 imágenes del grupo de entrenamiento.

Después, el modelo intenta clasificar las 40 imágenes reservadas para prueba.

El script también genera un reporte de clasificación y calcula el accuracy global. En los resultados suministrados para este informe no se incluyó el valor final del accuracy, por lo tanto no se registra una cifra que no haya sido obtenida de la ejecución real.

---

## 6. Ejemplo real de una predicción

Durante la ejecución se obtuvo:

```text
Ejemplo de prueba #0:
archivo='red_desconectada/red_desconectada_024.png'
real='red_desconectada'
predicha='error_aplicacion_crash'
```

Este resultado debe interpretarse de la siguiente manera:

```text
Archivo analizado:
red_desconectada_024.png

Clase correcta:
red_desconectada

Predicción del modelo:
error_aplicacion_crash
```

En este caso específico la red neuronal **se equivocó**.

La imagen realmente pertenece a:

```text
red_desconectada
```

pero el modelo la clasificó como:

```text
error_aplicacion_crash
```

Esto es importante porque una red neuronal no garantiza que todas las predicciones sean correctas.

El error también sirve como evidencia para analizar posteriormente qué clases está confundiendo el modelo.

Una sola predicción equivocada no permite determinar por sí sola si el modelo funciona bien o mal. Para eso se debe revisar el accuracy general y el reporte de clasificación completo que imprime el programa.

---

## 7. Base de datos SQLite

El programa genera:

```text
artifacts/imagenes.db
```

Dentro de esta base se crea la tabla:

```text
imagenes_errores
```

con los siguientes campos:

| Campo | Significado |
|---|---|
| `id` | Identificador del registro |
| `archivo` | Ruta de la imagen |
| `clase_real` | Tipo de error correcto |
| `split` | Indica si la imagen pertenece a entrenamiento o prueba |

La ejecución mostró:

```text
Registros de imágenes de errores en SQLite: 160
```

Esto significa que las 160 imágenes cargadas quedaron registradas dentro de la base.

Los registros permiten saber qué imágenes participaron en el ejercicio y en qué grupo fueron utilizadas.

Por ejemplo:

```text
archivo                     clase_real          split
----------------------------------------------------------------
...png                       red_desconectada    train
...png                       disco_lleno         test
```

SQLite no reemplaza a la red neuronal.

Su función principal en esta práctica es **guardar evidencia y facilitar la trazabilidad**.

La idea puede resumirse así:

```text
MODELO
reconoce

BASE DE DATOS
registra
```

---

## 8. Ontología de errores de TI

La ontología permite expresar las relaciones existentes entre los conceptos del proyecto.

En esta práctica se utiliza un grafo dirigido creado con NetworkX.

Una relación puede leerse de esta forma:

```text
ORIGEN → RELACIÓN → DESTINO
```

Por ejemplo:

```text
modelo_mlp → reconoce → error_visual
```

se puede leer como:

> El modelo MLP reconoce errores visuales.

La finalidad es que las conexiones tengan un significado comprensible y no sean solamente palabras unidas.

---

## 9. Relaciones de ontología base

El resultado obtenido fue:

```text
Relaciones de ontología base de errores: 8
```

Estas ocho relaciones se forman de la siguiente manera.

### Cuatro relaciones para las clases de errores

```text
error_visual → tiene_clase → pantalla_azul_bsod
error_visual → tiene_clase → red_desconectada
error_visual → tiene_clase → disco_lleno
error_visual → tiene_clase → error_aplicacion_crash
```

### Cuatro relaciones relacionadas con el modelo

```text
modelo_mlp → reconoce → error_visual
imagen_error → representa → error_visual
prediccion_error → asigna_clase → error_visual
modelo_mlp → produce → prediccion_error
```

Por eso:

```text
4 relaciones de clases
+
4 relaciones del funcionamiento del modelo
=
8 relaciones base
```

---

## 10. Integración de una predicción concreta con la ontología

Después de realizar la predicción del ejemplo número `0`, el programa agrega dos relaciones adicionales.

En este caso, el modelo predijo:

```text
error_aplicacion_crash
```

Por lo tanto se crea una relación parecida a:

```text
prediccion_0
      ↓ asigna_clase
error_aplicacion_crash
```

También se relaciona la imagen utilizada con esa predicción:

```text
imagen_0
    ↓ genera
prediccion_0
```

Estas relaciones permiten representar el recorrido:

```text
IMAGEN
   ↓
PREDICCIÓN
   ↓
CLASE ASIGNADA
```

Es importante aclarar que la ontología registra **lo que el modelo predijo**, aunque esa predicción sea incorrecta.

En este ejemplo:

```text
Clase real      = red_desconectada
Clase predicha  = error_aplicacion_crash
```

La diferencia entre ambos valores permite conservar evidencia del error cometido por el modelo.

---

## 11. Integración con el Gestor de Tickets

El programa agrega:

```text
Relaciones de integración con soporte TI agregadas: 10
```

Estas relaciones conectan la clasificación de imágenes con las categorías usadas en el proyecto.

### Relación entre errores visuales y categorías

```text
pantalla_azul_bsod
    → pertenece_a_categoria → hardware

red_desconectada
    → pertenece_a_categoria → red

disco_lleno
    → pertenece_a_categoria → software

error_aplicacion_crash
    → pertenece_a_categoria → software
```

Estas relaciones permiten convertir una clase visual en una categoría más general del sistema de soporte.

Por ejemplo:

```text
red_desconectada
        ↓
      red
```

o:

```text
pantalla_azul_bsod
        ↓
     hardware
```

### Relaciones generales del Gestor de Tickets

También se agregan:

```text
ticket_soporte → puede_adjuntar → error_visual
ticket_soporte → pertenece_a → categoria_soporte

categoria_soporte → tiene_clase → hardware
categoria_soporte → tiene_clase → software
categoria_soporte → tiene_clase → red
categoria_soporte → tiene_clase → accesos
```

Estas relaciones ayudan a integrar Semana 08 con la idea general del Gestor de Tickets.

---

## 12. ¿Por qué aparecen 20 relaciones al final?

El programa muestra:

```text
Relaciones de ontología totales en GraphML: 20
```

El cálculo es:

```text
8 relaciones base
+
2 relaciones del ejemplo de prueba
+
10 relaciones de integración con soporte TI
=
20 relaciones
```

Es decir:

```text
8 + 2 + 10 = 20
```

La estructura general puede verse así:

```text
ONTOLOGÍA FINAL
│
├── 8 relaciones base
│
├── 2 relaciones del ejemplo analizado
│
└── 10 relaciones del Gestor de Tickets
        ↓
     TOTAL: 20
```

---

## 13. Archivo GraphML

El programa genera:

```text
artifacts/ontologia.graphml
```

Este archivo contiene el grafo completo.

La exportación se realiza después de agregar:

- las relaciones base;
- las relaciones del ejemplo de predicción;
- las relaciones propias del Gestor de Tickets.

Por esa razón, el archivo final contiene las:

```text
20 relaciones
```

El GraphML sirve para guardar de manera permanente la estructura que inicialmente existe dentro del programa.

En términos sencillos:

```text
NetworkX
   ↓
Grafo en memoria
   ↓
GraphML
   ↓
Grafo guardado en archivo
```

---

## 14. Modelo entrenado

La ejecución indica:

```text
Modelo guardado: artifacts\modelo_mlp.pkl
```

Este archivo contiene el modelo MLP después de haber sido entrenado.

Mientras el programa se está ejecutando, el modelo existe en memoria.

Al guardarlo con `pickle`, puede conservarse en disco:

```text
MLP entrenada
     ↓
pickle
     ↓
modelo_mlp.pkl
```

Esto permite reutilizar posteriormente el modelo sin tener que empezar necesariamente desde cero.

El archivo `.pkl` no contiene las imágenes.

Contiene el objeto del modelo ya entrenado.

---

## 15. Archivos generados

Después de ejecutar correctamente la práctica se obtienen principalmente:

```text
artifacts/
├── modelo_mlp.pkl
├── imagenes.db
└── ontologia.graphml
```

Además, el conjunto de imágenes utilizado permanece dentro de:

```text
data/
└── imagenes_errores/
    ├── etiquetas.csv
    └── carpetas e imágenes de las cuatro clases
```

### `modelo_mlp.pkl`

Guarda la red neuronal entrenada.

### `imagenes.db`

Guarda información de las 160 imágenes utilizadas.

### `ontologia.graphml`

Guarda las 20 relaciones de la ontología final.

### `etiquetas.csv`

Relaciona cada archivo de imagen con su clase correcta.

---

## 16. Dependencias utilizadas

El código utiliza las siguientes librerías externas:

```text
networkx
numpy
Pillow
scikit-learn
```

También utiliza módulos incluidos con Python:

```text
csv
pickle
sqlite3
pathlib
```

Para instalar las dependencias externas se puede utilizar:

```bash
python -m pip install networkx numpy pillow scikit-learn
```

En el código:

```python
from PIL import Image
```

corresponde al paquete:

```text
Pillow
```

---

## 17. Validación de los resultados obtenidos

Los resultados suministrados confirman:

| Validación | Resultado |
|---|---|
| Imágenes registradas en SQLite | `160` |
| Clases de errores visuales | `4` |
| Relaciones base de la ontología | `8` |
| Relaciones añadidas por el ejemplo concreto | `2` |
| Relaciones propias de integración con soporte TI | `10` |
| Relaciones finales en GraphML | `20` |
| Modelo guardado | `artifacts\modelo_mlp.pkl` |
| Base SQLite guardada | `artifacts\imagenes.db` |
| Ontología guardada | `artifacts\ontologia.graphml` |

El ejemplo de prueba también permitió comprobar que el sistema conserva tanto la clase real como la clase predicha, incluso cuando el modelo se equivoca.

---

## 18. Relación con el proyecto de soporte TI

Semana 08 agrega reconocimiento visual al proyecto.

El flujo actual puede representarse así:

```text
IMAGEN DE UN ERROR
        ↓
RED NEURONAL
        ↓
TIPO DE ERROR VISUAL
        ↓
CATEGORÍA DE SOPORTE
        ↓
GESTOR DE TICKETS
```

Por ejemplo:

```text
imagen de red desconectada
        ↓
red_desconectada
        ↓
categoría red
        ↓
ticket de soporte
```

Otro ejemplo:

```text
imagen de pantalla azul
        ↓
pantalla_azul_bsod
        ↓
categoría hardware
        ↓
ticket de soporte
```

La red neuronal se encarga de reconocer patrones visuales.

SQLite registra qué datos fueron utilizados.

La ontología permite expresar cómo se relaciona el resultado con las categorías del proyecto.

Así, Semana 08 aporta una nueva forma de entrada al sistema:

```text
ANTES
texto + reglas + telemetría

AHORA
texto + reglas + telemetría + imágenes
```

---

## 19. Limitaciones identificadas

### 19.1. El modelo puede confundir clases

El ejemplo entregado demuestra una confusión real:

```text
real     = red_desconectada
predicha = error_aplicacion_crash
```

Por lo tanto, el clasificador todavía puede cometer errores.

Esto debe analizarse utilizando el `classification_report` y el accuracy general.

### 19.2. El tamaño de las imágenes se reduce

Todas las imágenes se convierten a:

```text
32 x 32
```

Esto facilita el entrenamiento, pero también elimina parte de la información visual original.

### 19.3. Se trabaja en escala de grises

El color original no se utiliza.

Esto simplifica la entrada de la red, pero puede perder información si en el futuro el color resulta importante para diferenciar errores.

### 19.4. La MLP trabaja con píxeles aplanados

La imagen se convierte en un vector de 1024 valores.

El modelo no analiza la imagen exactamente de la misma manera que una arquitectura especializada en visión por computador.

Sin embargo, para esta práctica permite aplicar correctamente el concepto de reconocimiento mediante redes neuronales.

### 19.5. Las relaciones de soporte son definidas manualmente

Por ejemplo:

```text
red_desconectada → pertenece_a_categoria → red
```

no es una relación aprendida automáticamente por la MLP.

Es conocimiento definido por el proyecto para dar significado a la predicción visual.

---

## 20. Conclusiones

1. La práctica de Semana 08 ya utiliza imágenes relacionadas directamente con el dominio de soporte TI.
2. Se cargaron y registraron correctamente 160 imágenes pertenecientes a cuatro categorías de errores.
3. Cada imagen se transforma a escala de grises, se ajusta a `32 x 32` y se convierte en 1024 valores que pueden ser procesados por la MLP.
4. El modelo aprende utilizando 120 imágenes y se prueba con 40 imágenes independientes del entrenamiento.
5. SQLite conserva información de las 160 imágenes y permite identificar cuáles fueron utilizadas para entrenamiento y cuáles para prueba.
6. La ontología comienza con 8 relaciones base, agrega 2 relaciones correspondientes al ejemplo analizado y 10 relaciones de integración con soporte TI, obteniendo un total de 20.
7. El ejemplo de prueba demuestra que el modelo puede equivocarse, lo cual permite analizar sus limitaciones de manera realista.
8. El archivo `modelo_mlp.pkl` conserva el modelo entrenado, `imagenes.db` conserva la evidencia y `ontologia.graphml` conserva las relaciones con significado.
9. La Semana 08 amplía el Gestor de Tickets al permitir trabajar también con evidencia visual de errores de TI.
10. La idea principal puede resumirse así:

```text
MODELO RECONOCE
BASE REGISTRA
ONTOLOGÍA INTERPRETA
GESTOR DE TICKETS UTILIZA EL RESULTADO
```
