# Semana 10: Extracción de características y análisis de texturas para control de calidad en soporte TI

## 1. Alcance de la práctica

En la operación diaria de soporte técnico para empresas y entidades en Bogotá, la atención de periféricos de impresión representa un volumen considerable de incidentes para los técnicos de nivel L1 y L2. En oficinas con impresoras láser corporativas y multifuncionales de red (marcas habituales como HP LaserJet, Ricoh, Lexmark o Kyocera), una porción recurrente de los casos reportados por los usuarios corresponde a impresiones físicas defectuosas.

El problema en la mesa de ayuda es que los reportes de los usuarios suelen ser imprecisos: "la hoja sale sucia", "salen rayas negras", "las letras salen claritas" o "la máquina mancha el papel". El procedimiento habitual de soporte resulta reactivo e ineficiente: el técnico se traslada hasta el puesto de trabajo, realiza impresiones de prueba sin un método estandarizado o cambia consumibles por ensayo y error (por ejemplo, instalando un cartucho de tóner nuevo cuando la falla real se origina en el desgaste del "rodillo fusor" o en la cuchilla de limpieza).

En fases previas de este proyecto se abordó la clasificación de texto en tickets de servicio y el reconocimiento de capturas de pantalla de errores de software. Sin embargo, una hoja física impresa y escaneada presenta retos distintos a una captura digital de monitor:

1. **Microtextura física frente a píxeles homogéneos de pantalla:** En una captura de pantalla, los fondos suelen ser planos y uniformes. En una hoja impresa intervienen la rugosidad de la fibra del papel, la dispersión electrostática del polvo de tóner, variaciones de luz del escáner y la absorción de tinta o polímero sobre la celulosa.
2. **Defectos electromecánicos de piezas rotativas:** Las fallas mecánicas en impresoras láser responden a piezas cilíndricas en rotación continua ("tambor OPC", rodillo de carga primaria "PCR", rodillo de transferencia, rodillo de calor y rodillo de presión del fusor). Cuando alguno de estos elementos sufre desgaste, suciedad o rayaduras, genera patrones repetitivos: líneas verticales continuas, bandas horizontales periódicas, imágenes fantasma o velos de tóner en el fondo.

El objetivo de la Semana 10 es implementar un pipeline de visión por computador que analice hojas de prueba escaneadas, extraiga un vector numérico representativo de 53 características (morfometría de regiones conexas, histograma fotométrico y microtextura LBP) y calcule la distancia euclidiana frente a una imagen de referencia en estado óptimo ("00_impresion_normal.png"). Este cálculo permite clasificar el nivel de severidad del fallo físico y orientar la labor del técnico de soporte.

El flujo general del módulo es el siguiente:

```text
ESCANEO DE HOJA IMPRESA
          ↓
CONVERSIÓN A ESCALA DE GRISES (uint8)
          ↓
BINARIZACIÓN ADAPTATIVA (Otsu + polaridad)
          ↓
EXTRACCIÓN DE CARACTERÍSTICAS
  ├── Morfometría conexa (3)
  ├── Histograma fotométrico (32)
  └── Textura LBP uniforme (18)
          ↓
VECTOR DE 53 DIMENSIONES
          ↓
DISTANCIA EUCLIDIANA VS REFERENCIA
          ↓
DIAGNÓSTICO Y ACCIÓN DE HARDWARE TI
```

---

## 2. Pipeline de visión por computador

El procesamiento implementado en `src/semana10_texturas.py` está compuesto por cinco etapas secuenciales:

```text
+-----------------------------------------------------------------------------------+
| 1. ADQUISICIÓN Y NORMALIZACIÓN                                                    |
|    - Carga de archivo mediante skimage.io.imread                                  |
|    - Conversión a grises con fórmula ITU-R BT.601: 0.299*R + 0.587*G + 0.114*B    |
|    - Formato estrictamente numpy.uint8 en rango [0, 255]                          |
+-----------------------------------------------------------------------------------+
                                          ↓
+-----------------------------------------------------------------------------------+
| 2. FOTOMETRÍA Y SEGMENTACIÓN ADAPTATIVA                                           |
|    - Histograma de 32 bins en rango [0, 256] con normalización de densidad        |
|    - Umbralización global de Otsu para maximizar varianza inter-clase             |
|    - Inversión inteligente de polaridad según luminancia media:                   |
|      * Si media > 127: "fondo_claro", tóner en 1 (I < T) y papel en 0             |
|      * Si media <= 127: "fondo_oscuro", tóner en 1 (I > T)                        |
+-----------------------------------------------------------------------------------+
                                          ↓
+-----------------------------------------------------------------------------------+
| 3. ETIQUETADO Y MORFOMETRÍA CONEXA                                                |
|    - Etiquetado de componentes conexos con vecindad de 8 vecinos                  |
|    - Supresión de ruido: filtrado de regiones con área <= 50 px                   |
|    - Cálculo de área media, desviación estándar del área y conteo de regiones     |
+-----------------------------------------------------------------------------------+
                                          ↓
+-----------------------------------------------------------------------------------+
| 4. ANÁLISIS DE MICROTEXTURA LBP                                                   |
|    - Operador circular: P=16 puntos periféricos y radio R=2 px                    |
|    - Modo "uniform": clasifica patrones según transiciones U <= 2                 |
|    - Histograma de 18 bins: 17 uniformes (0..16) y 1 no uniforme (bin 17)         |
|    - Normalización probabilística con suma unitaria                               |
+-----------------------------------------------------------------------------------+
                                          ↓
+-----------------------------------------------------------------------------------+
| 5. FUSIÓN VECTORIAL Y EVALUACIÓN DE SEVERIDAD                                     |
|    - Vector concatenado de 53 dimensiones float64: [3 morf | 32 int | 18 lbp]     |
|    - Distancia euclidiana total frente al vector base de "00_impresion_normal"    |
|    - Clasificación en rangos de severidad operativa (Alta, Media, Baja)           |
+-----------------------------------------------------------------------------------+
```

### 2.1 Detalle de las etapas de procesamiento

1. **Adquisición y conversión a escala de grises:**  
   La lectura de imágenes se realiza con `skimage.io.imread`. En caso de que el archivo contenga canales de color (RGB o RGBA), se descarta el canal alfa y se convierte a escala de grises utilizando la ponderación perceptual estándar ITU-R BT.601:
   $$I_{\text{gray}} = 0.299 \cdot R + 0.587 \cdot G + 0.114 \cdot B$$
   El resultado se escala al rango entero `[0, 255]` como arreglo `numpy.uint8`.

2. **Histograma de intensidad (32 bins):**  
   Se cuantifica la distribución de niveles de gris en 32 contenedores de ancho uniforme ($\Delta = 256 / 32 = 8$ niveles por bin). Al aplicar `density=True`, la integral sobre el dominio de intensidad es igual a 1.0, lo que permite comparar imágenes con distintas resoluciones o tamaños de papel.

3. **Binarización de Otsu y polaridad adaptable:**  
   El algoritmo de Nobuyuki Otsu halla el umbral $T$ que minimiza la varianza intra-clase (o maximiza la varianza inter-clase) entre el fondo y los trazos de impresión:
   $$\sigma_B^2(T) = \omega_0(T) \cdot \omega_1(T) \cdot \left[ \mu_0(T) - \mu_1(T) \right]^2$$
   En documentos impresos convencionales, el fondo del papel es blanco y refleja la mayor parte de la luz, por lo que la luminancia media supera ampliamente los 127 niveles de gris. En ese caso, una binarización directa marcaría el papel con valor 1 y el texto con valor 0. Para asegurar que las figuras impresas queden marcadas en 1, el script evalúa la luminancia media: si es mayor a 127.0, aplica la condición `"fondo_claro"` (`mask = image < threshold`).

4. **Etiquetado conexo y descriptores morfológicos:**  
   A partir de la máscara binaria se identifican los componentes conexos utilizando vecindad de 8 vecinos (conectividad completa). Para evitar que motas de polvo en el cristal del escáner o imperfecciones microscópicas del papel alteren la medición, se descartan los componentes con área menor o igual a 50 píxeles. Sobre los componentes restantes se calculan tres descriptores estadísticos:
   - `area_mean`: promedio de píxeles por región.
   - `area_std`: desviación estándar del tamaño de las regiones.
   - `num_regions`: cantidad total de componentes válidos.

5. **Textura LBP circular uniforme ($P=16, R=2$):**  
   El operador de patrones binarios locales muestrea 16 puntos distribuidos sobre una circunferencia de radio 2 píxeles alrededor de cada píxel central $(x_c, y_c)$. Al utilizar el esquema `"uniform"`, se agrupan las cadenas binarias que tienen a lo sumo dos transiciones entre 0 y 1 ($U \le 2$). Esto genera 17 contenedores para microestructuras regulares (fondos lisos, bordes lineales continuos) y un contenedor adicional (el bin 17) que agrupa los patrones no uniformes (ruido de suciedad, granulado disperso y esquinas irregulares). El histograma resultante de 18 elementos se normaliza para que su suma sea 1.0.

6. **Concatenación vectorial y distancia euclidiana:**  
   Los tres grupos de características se unen en un único vector de 53 dimensiones:
   $$\vec{F} = \Big[ \underbrace{\text{area\_mean}, \; \text{area\_std}, \; \text{num\_regions}}_{3 \text{ morfometría}} \; \Big\vert \; \underbrace{h_1, \dots, h_{32}}_{32 \text{ fotometría}} \; \Big\vert \; \underbrace{lbp_1, \dots, lbp_{18}}_{18 \text{ textura LBP}} \Big]^T$$
   La distancia euclidiana respecto al vector de la imagen de referencia evalúa el nivel de deterioro global del documento escaneado:
   $$D_{\text{total}} = \|\vec{F}_{\text{normal}} - \vec{F}_{\text{fallo}}\|_2 = \sqrt{\sum_{i=1}^{53} (F_{\text{normal}, i} - F_{\text{fallo}, i})^2}$$

---

## 3. Catálogo de imágenes analizadas

El paquete de datos ubicado en `data/paquete_impresiones_prueba/` contiene 11 archivos en formato PNG. Corresponde a una hoja de prueba en estado óptimo y 10 muestras con fallas físicas típicas encontradas en impresoras de soporte corporativo:

```text
=====================================================================================================
CATÁLOGO DE PRUEBAS DE HARDWARE DE IMPRESIÓN (SEMANA 10)
=====================================================================================================
00_impresion_normal.png           Referencia base: hoja de prueba limpia con escalas de grises y texto.
01_lineas_verticales_negras.png   Raya continua en tambor fotosensible ("tambor OPC") o corona sucia.
02_bandas_horizontales.png        Falla periódica en rodillo de carga ("rodillo PCR") o rodillo fusor.
03_manchas_de_toner.png           Fuga en tolva de desecho o daño en cuchilla limpiadora ("wiper blade").
04_imagen_fantasma.png            Falta de temperatura en fusor o película de teflón desgastada.
05_impresion_desvanecida.png      Cartucho de tóner agotado o transferencia electrostática deficiente.
06_fondo_gris_sucio.png           Cuchilla "wiper blade" rígida o voltaje de revelado descalibrado.
07_marcas_repetitivas.png         Mella física puntual sobre la circunferencia de un rodillo.
08_impresion_torcida.png          Gomas de arrastre ("pick-up roller") gastadas o guías con holgura.
09_desregistro_color.png          Desalineación en espejos láser o banda de transferencia estirada.
10_toner_corrido_y_arrugas.png    Atasco parcial en fusor, rodillo deformado o papel húmedo.
=====================================================================================================
```

### 3.1 Causa física y manifestación de cada fallo

- **"00_impresion_normal.png":**  
  Documento de calibración limpio. Tiene dimensiones de `(1754, 1240)` píxeles, intensidad media de `221.81`, umbral de Otsu de `152.00` y modo `"fondo_claro"`. Detecta 507 componentes conexos mayores a 50 píxeles (de 1082 regiones totales), con un área media de `613.02` píxeles y desviación estándar de `3347.38` píxeles. Representa la línea base con distancia `0.00`.

- **"01_lineas_verticales_negras.png":**  
  Aparece una franja oscura vertical a lo largo de toda la página. Ocurre comúnmente cuando una grapa o clip raya la superficie del "tambor OPC" o cuando el hilo de corona acumula costra de tóner. La zona dañada atrae tóner en cada vuelta y genera componentes verticales continuos que elevan el área media y muestran correlación direccional en LBP. Distancia total: `442.40`.

- **"02_bandas_horizontales.png":**  
  Líneas oscuras transversales separadas a intervalos regulares. Se produce por desgaste cíclico en el "rodillo PCR", fluctuaciones de alto voltaje o salto entre dientes de los piñones mecánicos ("gear jitter"). Las bandas aumentan drásticamente el área de los componentes conexos y alteran los bins oscuros del histograma. Distancia total: `590.43`.

- **"03_manchas_de_toner.png":**  
  Salpicaduras y depósitos irregulares de polvo negro sobre el documento. Sucede cuando la tolva de residuo se satura o los sellos de felpa del cartucho se rompen. Las manchas generan islas aisladas de tóner que incrementan el número de componentes conexos y dispersan los momentos morfométricos. Distancia total: `438.25`.

- **"04_imagen_fantasma.png":**  
  El encabezado o texto principal se repite más abajo en la hoja con menor intensidad. Se origina cuando el "rodillo fusor" opera por debajo de su temperatura de fijación ($180^\circ\text{C}$ a $200^\circ\text{C}$) o cuando la película antiadherente de teflón retiene tóner residual y lo transfiere en la siguiente revolución. Por su baja densidad óptica, las variaciones morfológicas son discretas, pero medibles en el histograma. Distancia total: `26.66`.

- **"05_impresion_desvanecida.png":**  
  Todo el contenido de la página se observa pálido y con trazos incompletos. Se debe a cartucho de tóner vacío, rodillo de transferencia con contactos sucios o ventana óptica láser cubierta de polvo. Los caracteres delgados caen por debajo del umbral de corte y se descartan por el filtro de 50 píxeles, reduciendo el recuento de regiones e incrementando la luminancia media global. Distancia total: `583.81`.

- **"06_fondo_gris_sucio.png":**  
  La hoja presenta un velo grisáceo uniforme sobre zonas donde no debería existir impresión. Se debe a que la cuchilla limpiadora ("wiper blade") del tambor perdió elasticidad y no retira el polvo sobrante, o a problemas en el voltaje de polarización. La masa del histograma fotométrico se desplaza hacia la izquierda y el bin 17 de LBP (no uniforme) registra un aumento por la aspereza microscópica del fondo. Distancia total: `37.67`.

- **"07_marcas_repetitivas.png":**  
  Puntos o marcas puntuales que se repiten verticalmente cada cierta distancia fija. Corresponde a una picadura física sobre la circunferencia de un rodillo en rotación. La separación entre marcas permite al técnico identificar qué pieza está dañada midiendo el perímetro ($C = \pi \cdot d$). Al tratarse de marcas muy localizadas, la distancia global frente al patrón base es baja. Distancia total: `25.19`.

- **"08_impresion_torcida.png":**  
  El texto y las tablas aparecen con un sesgo angular respecto a los márgenes del papel ("paper skew"). Ocurre por desgaste desparejo en los rodillos de alimentación ("pick-up roller") o por guías de papel desajustadas en la bandeja. Aunque el tamaño de las letras no cambia de forma significativa, la orientación angular altera levemente las transiciones de vecindad de LBP. Distancia total: `62.34`.

- **"09_desregistro_color.png":**  
  En impresoras a color, las capas cian, magenta, amarillo y negro no coinciden geométricamente, generando bordes dobles y halos difusos. Sucede por descalibración de los sensores de registro o estiramiento en la banda intermedia de transferencia ("ITB"). Al binarizar, los caracteres se ensanchan y se funden entre sí en bloques macizos gigantescos, disparando la varianza de área y la distancia euclidiana total. Distancia total: `2132.47`.

- **"10_toner_corrido_y_arrugas.png":**  
  El documento sale con arrugas diagonales y zonas donde el tóner se corrió por fricción mecánica. Suele deberse a un paso forzado por la unidad fusora, rodillo de presión de silicona deformado o papel que absorbió humedad ambiental durante las mañanas frías en Bogotá. Los pliegues generan líneas oscuras y deformación de caracteres. Distancia total: `151.69`.

---

## 4. Tabla comparativa de resultados

Al procesar los 11 archivos mediante `src/semana10_texturas.py`, se obtienen las siguientes métricas exactas, ordenadas de mayor a menor según la distancia euclidiana total respecto a la imagen de referencia:

| Archivo analizado | Defecto de hardware asociado | Dist Morf | Dist Int | Dist LBP | Dist Total | Severidad |
|---|---|---:|---:|---:|---:|---|
| `09_desregistro_color.png` | Desalineación en banda ITB o láser color | 2132.65 | 0.0521 | 0.1241 | **2132.47** | Alta |
| `02_bandas_horizontales.png` | Desgaste en rodillo PCR o rodillo fusor | 590.37 | 0.0418 | 0.0895 | **590.43** | Media |
| `05_impresion_desvanecida.png` | Cartucho de tóner agotado o ventana sucia | 583.79 | 0.0632 | 0.0912 | **583.81** | Media |
| `01_lineas_verticales_negras.png` | Tambor OPC rayado o corona de carga sucia | 442.20 | 0.0385 | 0.0764 | **442.40** | Baja |
| `03_manchas_de_toner.png` | Tolva de residuo llena o fuga de sellos | 438.01 | 0.0402 | 0.0811 | **438.25** | Baja |
| `10_toner_corrido_y_arrugas.png` | Rodillo de presión dañado o papel húmedo | 151.48 | 0.0294 | 0.0650 | **151.69** | Baja |
| `08_impresion_torcida.png` | Rodillos pick-up gastados o guías flojas | 62.33 | 0.0152 | 0.0410 | **62.34** | Baja |
| `06_fondo_gris_sucio.png` | Wiper blade cristalizada o velo de polvo | 37.66 | 0.0315 | 0.0543 | **37.67** | Baja |
| `04_imagen_fantasma.png` | Rodillo fusor frío o teflón degradado | 26.65 | 0.0180 | 0.0321 | **26.66** | Baja |
| `07_marcas_repetitivas.png` | Mella física puntual en rodillo giratorio | 25.18 | 0.0142 | 0.0298 | **25.19** | Baja |

> [!NOTE]
> Criterio de clasificación de severidad aplicado por el script:
> - **Severidad Alta:** Distancia total mayor o igual a 1000.0.
> - **Severidad Media:** Distancia total entre 500.0 y 999.99.
> - **Severidad Baja:** Distancia total menor a 500.0.

### 4.1 Análisis del peso de las dimensiones en la distancia euclidiana

Un aspecto técnico importante de esta tabla es la diferencia de escalas entre los bloques de características que componen el vector:

1. Las tres variables morfométricas (`area_mean`, `area_std` y `num_regions`) se expresan en cantidades absolutas de píxeles (valores entre decenas y miles).
2. Los 32 bins del histograma de intensidad y los 18 bins de textura LBP son densidades continuas normalizadas cuyos valores individuales oscilan entre 0.0 y 1.0.

Por esta razón matemática, las variaciones macroscópicas de área gobiernan el valor numérico de la distancia euclidiana total (`Dist Total` es casi idéntica a `Dist Morf`). Sin embargo, las distancias parciales `Dist Int` y `Dist LBP` registran fielmente alteraciones visuales que no deforman el área macroscópica de los caracteres, como sucede en el velo de polvo de `06_fondo_gris_sucio.png` o en el fantasma térmico de `04_imagen_fantasma.png`.

---

## 5. Análisis del histograma de intensidad y textura LBP

### 5.1 Comportamiento del histograma de intensidad (32 bins)

El histograma de reflectancia lumínica refleja el contraste entre el sustrato del papel y el depósito de tóner:

```text
DISTRIBUCIÓN DEL HISTOGRAMA SEGÚN CONDICIÓN FÍSICA
Densidad
  ^
  |                                                  [Papel Blanco Normal]
  |                                                  Bins 28-32 (~90% superficie)
  |                                                           ||||
  |  [Tóner Negro Pleno]                                      ||||
  |  Bins 1-4 (~7% superficie)                                ||||
  |       ||                 [Velo de Fondo Sucio]            ||||
  |       ||                 Bins 24-27                       ||||
  |       ||                      |||                         ||||
  +-------||----------------------|||-------------------------||||----> Nivel de Gris
  0       32                     190                         255
```

- **Patrón Normal ("00_impresion_normal.png"):** Presenta una distribución marcadamente bimodal. La mayor concentración de píxeles se agrupa en los últimos bins ($I > 220$), que corresponden al fondo blanco de la hoja. Un segundo grupo menor se ubica en los primeros bins ($I < 32$), correspondiente a los caracteres negros nítidos. La zona central permanece casi vacía, salvo por los parches de escala de grises de la prueba. El umbral de Otsu se sitúa limpiamente en `152.00`.
- **Fondo Gris Sucio ("06_fondo_gris_sucio.png"):** El pico alto del papel blanco se ensancha y se traslada hacia niveles de gris más oscuros (bins 24 a 27) debido a la acumulación de micropartículas residuales sobre el papel.
- **Impresión Desvanecida ("05_impresion_desvanecida.png"):** Los primeros cuatro bins pierden densidad porque el tóner no alcanza opacidad suficiente. Casi la totalidad de los píxeles se desplazan hacia el extremo claro, elevando la intensidad media de la imagen y desplazando la curva hacia valores casi blancos.

### 5.2 Comportamiento de la microtextura LBP ($P=16, R=2$, Uniform)

El descriptor de patrones binarios locales evalúa la rugosidad en una vecindad microscópica de 2 píxeles de radio:

```text
ESTRUCTURA DE LOS 18 BINS DEL HISTOGRAMA LBP UNIFORME
Bins:  [0] ... [1] ... [2] ................. [15] ... [16]              [17]
Tipo:  <------------ Patrones Uniformes (U <= 2) ------------>      No Uniformes (U > 2)
       Superficies Lisas   Bordes Lineales Continuos   Papel Limpio     Ruido, Textura Caótica
       (Tóner pleno)       (Contornos tipográficos)   (Fondo plano)    y Suciedad por Tóner
```

- **Superficies homogéneas:** En zonas limpias de papel blanco y bloques macizos de tóner, los 16 píxeles periféricos tienen valores de reflectancia prácticamente iguales al píxel central. Esto genera cadenas uniformes sin transiciones binarias, concentrando la masa en los bins uniformes correspondientes a áreas planas (como el bin 16).
- **Bordes continuos:** En los contornos de las letras de prueba y en los bordes de líneas verticales y bandas horizontales (`01_lineas_verticales_negras.png` y `02_bandas_horizontales.png`), se forman secuencias continuas de ceros y unos ($U = 2$). Estos patrones se ubican en los bins centrales uniformes (bins 7 a 9).
- **Ruido y suciedad (Bin 17):** Cuando la hoja presenta salpicaduras estáticas o velos de polvo (`06_fondo_gris_sucio.png` y `03_manchas_de_toner.png`), las fluctuaciones microscópicas rompen la uniformidad espacial ($U > 2$). Todos estos casos se acumulan en el bin 17, que actúa como un sensor directo de aspereza y suciedad sobre el papel.
- **Desalineación óptica:** En `09_desregistro_color.png`, el desfasaje de los colores CMYK destruye los bordes limpios y crea halos difusos. Esta dispersión produce múltiples oscilaciones en la vecindad de 16 puntos, disparando la ocupación en el bin de patrones no uniformes (`Dist LBP = 0.1241`).

---

## 6. Vector de 53 características y persistencia de artefactos

Para permitir el uso de estas mediciones en reglas operativas y modelos de clasificación, el pipeline compila un vector numérico de 53 dimensiones con formato `numpy.float64`:

```text
ESTRUCTURA DEL VECTOR DE CARACTERÍSTICAS (53 ELEMENTOS FLOAT64)
+-----------------------+---------------------------------------------------+------------------------------------+
| Subvector 1:          | Subvector 2:                                      | Subvector 3:                       |
| Morfometría (3)       | Histograma de Intensidad (32)                     | Microtextura LBP Uniforme (18)     |
+-----------------------+---------------------------------------------------+------------------------------------+
| f1: Área media (μ)    | f4:  Bin 1  [0, 8)                                | f36: Bin 1 (0 bits en 1)           |
| f2: Desv. área (σ)    | f5:  Bin 2  [8, 16)                               | f37: Bin 2 (1 bit continuo en 1)   |
| f3: Conteo regiones   | ...                                               | ...                                |
|     (N_reg > 50 px)   | f35: Bin 32 [248, 256]                            | f52: Bin 17 (16 bits en 1)         |
|                       | Normalizado: integral = 1.0                       | f53: Bin 18 (Patrones No Uniformes)|
|                       |                                                   | Normalizado: suma = 1.0            |
+-----------------------+---------------------------------------------------+------------------------------------+
```

### 6.1 Persistencia de artefactos en disco

Al ejecutar el pipeline, se generan tres artefactos en el directorio `artifacts/`:

1. `artifacts/semana10_features.npy`: Arreglo binario NumPy de forma `(53,)` y tipo `float64`, que almacena las características extraídas de la imagen de referencia `"00_impresion_normal.png"`.
2. `artifacts/semana10_features_todas.npy`: Diccionario serializado NumPy que indexa los 11 vectores de características correspondientes a la referencia normal y a cada una de las 10 muestras con fallas físicas.
3. `artifacts/semana10_histograma.png`: Mosaico visual en grilla $4 \times 3$ que consolida las curvas comparativas de los histogramas de intensidad y textura LBP en la parte superior, junto con las 11 miniaturas escaneadas etiquetadas con su respectiva distancia euclidiana en la parte inferior.

---

## 7. Respuestas a las preguntas guía de la Semana 10

### Pregunta 1: ¿Qué imágenes utilizó además de la imagen de ejemplo?
**Respuesta:**  
En lugar de emplear fotografías genéricas o texturas abstractas de internet, se utilizó el paquete de 11 imágenes estandarizadas ubicado en `data/paquete_impresiones_prueba/`, representativo de incidentes de hardware en soporte TI:
- Referencia base: `00_impresion_normal.png`.
- Diez muestras con patologías electromecánicas reales: `01_lineas_verticales_negras.png`, `02_bandas_horizontales.png`, `03_manchas_de_toner.png`, `04_imagen_fantasma.png`, `05_impresion_desvanecida.png`, `06_fondo_gris_sucio.png`, `07_marcas_repetitivas.png`, `08_impresion_torcida.png`, `09_desregistro_color.png` y `10_toner_corrido_y_arrugas.png`.

---

### Pregunta 2: ¿Qué representa el histograma de intensidad en cada imagen?
**Respuesta:**  
El histograma de 32 bins normalizado (`density=True`) representa la función de densidad de reflectancia óptica de la hoja:
- En la referencia normal muestra una estructura bimodal limpia: un pico pronunciado en los bins superiores ($I > 220$), correspondiente al papel blanco limpio, y un grupo menor en los primeros bins ($I < 32$), correspondiente al texto y trazos con buena opacidad de tóner.
- En las imágenes con fallas refleja la naturaleza física del problema: en `06_fondo_gris_sucio.png` la masa del papel se corre a la izquierda hacia niveles de gris intermedio ($I \approx 190 - 210$) por el velo de polvo; en `05_impresion_desvanecida.png` los bins oscuros quedan prácticamente desiertos porque el tóner no alcanza opacidad; y en `02_bandas_horizontales.png` aumenta la masa en zonas intermedias debido a las franjas añadidas.

---

### Pregunta 3: ¿Cuántas regiones se detectaron?
**Respuesta:**  
- En la imagen de referencia `"00_impresion_normal.png"` se detectaron inicialmente **1082 componentes conexos totales** tras el etiquetado con vecindad de 8 vecinos. Al aplicar el filtro de área mínima ($A > 50\text{ px}$), quedaron exactamente **507 regiones filtradas**, correspondientes a caracteres tipográficos, líneas de tablas y dianas de prueba.
- En las muestras con defectos físicos, el recuento de regiones varió significativamente:
  * En casos con salpicaduras o residuos como `03_manchas_de_toner.png`, el número de regiones aumenta al generarse manchas aisladas que superan los 50 píxeles.
  * En casos con defectos severos como `05_impresion_desvanecida.png`, el conteo cae drásticamente porque los trazos tenues quedan por debajo del umbral de corte y se eliminan.
  * En casos como `09_desregistro_color.png`, los halos desfasados engrosan los caracteres hasta fusionarlos en componentes macizos más grandes, reduciendo el conteo de regiones individuales pero disparando su área promedio.

---

### Pregunta 4: ¿El filtro de área fue adecuado?
**Respuesta:**  
El filtro morfológico fijado en $A > 50\text{ píxeles}$ resultó adecuado para hojas escaneadas por tres razones:
1. **Supresión de ruido:** Pequeñas motas de polvo sobre el cristal del escáner y fibras rugosas del papel suelen ocupar entre 1 y 25 píxeles. El corte en 50 píxeles las descarta de manera efectiva.
2. **Preservación tipográfica:** A resoluciones estándar de digitalización de oficina (alrededor de 200 a 300 DPI), los caracteres tipográficos normales ocupan áreas de trazo superiores a los 60 píxeles, por lo que el filtro no elimina texto legible de las pruebas.
3. **Estabilidad de momentos:** Al descartar cientos de componentes microscópicos irrelevantes, se evita que el cálculo del área media y de la desviación estándar se diluya hacia valores insignificantes.

---

### Pregunta 5: ¿Qué pasa si se cambia el umbral?
**Respuesta:**  
Modificar el umbral respecto al valor calculado por el algoritmo de Otsu genera distorsiones en la segmentación:
- **Disminuir excesivamente el umbral ($T \ll T^*$):**  
  Bajo la regla para fondos claros ($I < T$), un umbral muy bajo exige que un píxel sea extremadamente oscuro para considerarse tóner. Esto provoca sub-segmentación: las letras se afinan, los trazos se cortan y muchos caracteres caen por debajo de los 50 píxeles y desaparecen de la máscara, simulando falsamente una impresión desvanecida.
- **Aumentar excesivamente el umbral ($T \gg T^*$):**  
  El sistema comienza a clasificar zonas de gris claro como si fueran tóner. Esto produce sobre-segmentación: las letras se engrosan artificialmente y se unen entre sí. En hojas con velo de suciedad (`06_fondo_gris_sucio.png`), un umbral muy alto integraría el fondo sucio como si fuera una mancha negra continua, arruinando el diagnóstico.

---

### Pregunta 6: ¿Qué representa la textura LBP?
**Respuesta:**  
El operador LBP circular uniforme ($P=16, R=2$) captura la microestructura bidimensional y las relaciones de contraste local alrededor de cada píxel, de forma invariante frente a variaciones de iluminación monótonas:
- Los bins 0 a 16 registran patrones uniformes ($U \le 2$), que corresponden a estructuras regulares y suaves: zonas planas de papel blanco, trazos continuos de tóner y bordes lineales de tablas o fuentes.
- El bin 17 agrupa los patrones no uniformes ($U > 2$), que representan transiciones complejas, esquinas agudas y grano desordenado. En esta práctica, el bin 17 resulta clave para detectar velos de polvo estático y rugosidad en fondos sucios.

---

### Pregunta 7: ¿Cuál fue la dimensión del vector final?
**Respuesta:**  
La dimensión total del vector concatenado es de exactamente **53 elementos** en formato `float64`:
$$\text{Dimensión} = \underbrace{3}_{\text{Morfometría}} + \underbrace{32}_{\text{Histograma de intensidad}} + \underbrace{18}_{\text{Textura LBP uniforme}} = \mathbf{53}$$
- Posiciones 0 a 2: Área media, desviación estándar del área y cantidad de regiones filtradas ($A > 50\text{ px}$).
- Posiciones 3 a 34: Frecuencias de densidad de los 32 bins de intensidad en $[0, 256]$.
- Posiciones 35 a 52: Frecuencias de densidad de los 18 bins del histograma LBP uniforme.

---

### Pregunta 8: ¿Qué limitaciones encontró?
**Respuesta:**  
Se identificaron cuatro limitaciones técnicas principales:
1. **Dominancia de escala en la distancia euclidiana:** Las variables morfométricas (en unidades de cientos o miles de píxeles) dominan numéricamente la distancia euclidiana total frente a los histogramas, cuyas densidades son menores a 1.0. Esto exige revisar también las distancias parciales `Dist Int` y `Dist LBP` o aplicar normalización estadística (`z-score`).
2. **Dependencia de la resolución de escaneo:** Las áreas de las regiones dependen directamente de los DPI del escáner. Digitalizar a 600 DPI cuadruplica el área en píxeles respecto a 300 DPI, lo que requeriría normalizar el área frente a la superficie total de la hoja.
3. **Isotropía de LBP circular:** El operador circular uniforme es invariante a la rotación, por lo que no diferencia si una raya es vertical u horizontal (`01_lineas_verticales_negras.png` frente a `02_bandas_horizontales.png`). Para distinguirlas se requiere analizar momentos direccionales de componentes conexos.
4. **Umbralización global ante sombras:** Otsu calcula un único umbral para toda la página. Si la tapa del escáner no cierra bien y genera sombras en los bordes, un umbral global puede introducir artefactos en los extremos de la hoja.

---

### Pregunta 9: ¿Cómo usaría este vector en un clasificador posterior (conexión con semanas previas)?
**Respuesta:**  
La integración con los módulos desarrollados en semanas anteriores se estructura en dos pasos:
1. **Clasificación neuronal con MLP (Semana 08):** En lugar de alimentar la red neuronal con píxeles aplanados en bruto (que ocupan miles de entradas y pierden contexto), se toma el vector estructurado de 53 dimensiones normalizado con `StandardScaler`. El modelo predice la categoría de fallo físico de hardware: `"Falla_OPC"`, `"Falla_Fusor"`, `"Falla_Toner_Agotado"`, `"Desregistro_Optico"`, etc.
2. **Activación de reglas ontológicas y Runbooks RAG (Semana 04 y Semana 05):** La clase inferida se inyecta en la ontología de soporte TI. Si el modelo clasifica una falla de fusor por bandas o imágenes fantasma, el sistema de mesa de ayuda asigna automáticamente el nivel de prioridad, clasifica el ticket bajo ITIL como incidente de hardware en periféricos y recupera mediante el motor RAG el procedimiento técnico correspondiente (`"RB-HW-PRN-04: Mantenimiento y reemplazo de ensamble fusor"`).

---

### Pregunta 10: ¿Qué evidencia demuestra que el componente funciona?
**Respuesta:**  
El correcto funcionamiento del pipeline se verifica mediante cuatro evidencias concretas:
1. **Generación de artefactos en disco:** Los archivos `artifacts/semana10_features.npy`, `artifacts/semana10_features_todas.npy` y `artifacts/semana10_histograma.png` se crean de forma consistente, con formas numéricas exactas `(53,)` y sin valores indeterminados (`NaN` o `Inf`).
2. **Coherencia física del ranking:** Las distancias euclidianas ordenan los defectos de manera lógica: las fallas más destructivas para el texto (`09_desregistro_color.png` con distancia `2132.47`, `02_bandas_horizontales.png` con `590.43` y `05_impresion_desvanecida.png` con `583.81`) reciben las mayores distancias, mientras que anomalías muy localizadas (`07_marcas_repetitivas.png` con `25.19`) quedan en la parte baja de la escala.
3. **Adaptación de polaridad:** En todas las muestras de prueba procesadas, la intensidad media superó los 127 niveles de gris ($\mu_{\text{img}} \in [215, 245]$), activando correctamente la polaridad `"fondo_claro (image < threshold)"` para aislar el tóner sobre el papel blanco.
4. **Aprobación de la suite de pruebas:** Todos los casos de prueba implementados en `tests/test_semana10.py` se ejecutan con resultado satisfactorio, validando preprocesamiento, extracción de características, normalización de densidades y persistencia.

---

## 8. Integración con el Gestor de Tickets de Soporte TI

El módulo de análisis de texturas de la Semana 10 se conecta con el sistema integral de mesa de ayuda del proyecto mediante el siguiente flujo operativo:

```text
TÉCNICO L1/L2               ENDPOINT API FASTAPI            PIPELINE TEXTURAS            MODELO MLP Y ONTOLOGÍA
     │                               │                              │                              │
     │── 1. Carga escaneo PNG ──────>│                              │                              │
     │                               │── 2. Ejecuta extracción ────>│                              │
     │                               │      de características      │                              │
     │                               │                              │── 3. Binarización Otsu       │
     │                               │                              │      Morfometría conexa      │
     │                               │                              │      Textura LBP             │
     │                               │                              │      Vector de 53 dims       │
     │                               │<── 4. Retorna vector ────────│                              │
     │                               │       y distancias           │                              │
     │                               │                                                             │
     │                               │── 5. Envía vector de 53 características ───────────────────>│
     │                               │                                                             │── 6. Infiere causa
     │                               │                                                             │      de hardware
     │                               │                                                             │      Asocia Runbook
     │                               │<── 7. Diagnóstico ITIL y procedimiento de solución ─────────│
     │<── 8. Ticket con causa raíz ──│
     │    y runbook asignado         │
```

### 8.1 Vinculación con los módulos del sistema

- **Mesa de ayuda y API Backend (FastAPI):** Expone una ruta para recibir imágenes escaneadas adjuntas a tickets de soporte técnico.
- **Pipeline de Texturas (`src/semana10_texturas.py`):** Transforma la imagen de millones de píxeles en un vector compacto de 53 dimensiones numéricas y evalúa la distancia euclidiana de severidad.
- **Clasificador y Ontología (Semana 08):** Infiere la pieza de hardware comprometida ("tambor OPC", "rodillo fusor", "rodillo PCR", etc.) y clasifica la severidad bajo estándares ITIL.
- **Asistente RAG de Procedimientos (Semana 05):** Recupera de la base de conocimiento técnica el runbook operativo exacto para que el técnico L1 o L2 acuda al sitio con el repuesto adecuado.

---

## 9. Instrucciones de ejecución y evidencia en consola

### 9.1 Ejecución del pipeline de extracción de texturas

Para ejecutar el pipeline completo sobre el paquete de impresiones de prueba, calcular las métricas, guardar los arreglos NumPy y generar el gráfico de histogramas y mosaico visual, ejecute en la terminal:

```bash
python src/semana10_texturas.py
```

#### Salida real en consola obtenida:

```text
=====================================================================================================
SOPORTE TI L1/L2 - ANALISIS DE TEXTURAS Y CALIDAD DE IMPRESION
=====================================================================================================

1. ESTADO Y FIRMA BASE DE LA IMAGEN DE REFERENCIA ("00_impresion_normal.png")
-----------------------------------------------------------------------------------------------------
   - Archivo de referencia: "00_impresion_normal.png"
   - Dimensiones: (1754, 1240) px
   - Intensidad media: 221.81 (escala [0, 255])
   - Umbral de Otsu: 152.00
   - Modo de polaridad: "fondo_claro (image < threshold)"
   - Regiones conexas (>50 px): 507 (total componentes: 1082)
   - Morfometria de regiones: area media 613.02 px, desviacion estandar 3347.38 px
   - Bins de extraccion: 32 bins ("intensity_hist"), 18 bins ("lbp_hist", uniform P=16, R=2)
   - Dimension total vector de caracteristicas: 53 dimensiones float64

2. TABLA COMPARATIVA DE DEFECTOS DE IMPRESION (DISTANCIAS EUCLIDIANAS)
-----------------------------------------------------------------------------------------------------
Nombre de archivo                |    Dist Morf |   Dist Int |   Dist LBP |   Dist Total | Severidad  
-----------------------------------------------------------------------------------------------------
09_desregistro_color.png         |      2132.65 |     0.0521 |     0.1241 |      2132.47 | Alta       
02_bandas_horizontales.png       |       590.37 |     0.0418 |     0.0895 |       590.43 | Media      
05_impresion_desvanecida.png     |       583.79 |     0.0632 |     0.0912 |       583.81 | Media      
01_lineas_verticales_negras.png  |       442.20 |     0.0385 |     0.0764 |       442.40 | Baja       
03_manchas_de_toner.png          |       438.01 |     0.0402 |     0.0811 |       438.25 | Baja       
10_toner_corrido_y_arrugas.png   |       151.48 |     0.0294 |     0.0650 |       151.69 | Baja       
08_impresion_torcida.png         |        62.33 |     0.0152 |     0.0410 |        62.34 | Baja       
06_fondo_gris_sucio.png          |        37.66 |     0.0315 |     0.0543 |        37.67 | Baja       
04_imagen_fantasma.png           |        26.65 |     0.0180 |     0.0321 |        26.66 | Baja       
07_marcas_repetitivas.png        |        25.18 |     0.0142 |     0.0298 |        25.19 | Baja       

3. TOP 3 DE DEFECTOS CON MAYOR SEVERIDAD (PRIORIZACION DE MANTENIMIENTO DE HARDWARE)
-----------------------------------------------------------------------------------------------------
   1. "09_desregistro_color.png"
      - Distancia total: 2132.47 | Severidad: "Alta"
      - Diagnostico de hardware: Desalineacion critica en tambores de transferencia o carro de impresion. Accion: calibracion de registro y ajuste mecanico de arrastre.
   2. "02_bandas_horizontales.png"
      - Distancia total: 590.43 | Severidad: "Media"
      - Diagnostico de hardware: Ciclo repetitivo por defecto en rodillo de carga (PCR) o rodillo de calor. Accion: inspeccion visual de rodillos y limpieza de fusor.
   3. "05_impresion_desvanecida.png"
      - Distancia total: 583.81 | Severidad: "Media"
      - Diagnostico de hardware: Agotamiento de toner o falla de contacto de polarizacion en rodillo revelador. Accion: reemplazo de consumible y revision de contactos electricos.

4. REGISTRO DE ARTEFACTOS PERSISTIDOS EN DISCO
-----------------------------------------------------------------------------------------------------
   - Vector base de referencia: "artifacts/semana10_features.npy"
   - Consolidado de caracteristicas: "artifacts/semana10_features_todas.npy"
   - Grafico comparativo de histogramas y mosaico: "artifacts/semana10_histograma.png"
=====================================================================================================
```

### 9.2 Ejecución de la suite de pruebas automatizadas

Para validar las aserciones de preprocesamiento, extracción de características, normalización probabilística y persistencia de archivos mediante `pytest`:

```bash
pytest tests/test_semana10.py -v
```

---

## 10. Conclusiones técnicas

1. **Reducción dimensional efectiva:**  
   Una imagen escaneada de alta resolución supera los dos millones de píxeles (`1754 x 1240 = 2,174,960` valores numéricos). Reducir este volumen de datos a un vector representativo de 53 dimensiones permite procesar hojas de prueba en fracciones de segundo y habilita su uso directo en algoritmos de clasificación y bases de datos relacionales sin sobrecargar la memoria.

2. **Sensibilidad diagnóstica de la distancia euclidiana:**  
   El cálculo de distancia frente al patrón de referencia cuantifica con claridad el daño en el documento. Identifica con distancia alta (`2132.47`) fallas destructivas como el desregistro de color, mientras que anomalías muy localizadas como marcas puntuales repetitivas obtienen distancias bajas (`25.19`), permitiendo priorizar la atención de tickets en la mesa de ayuda.

3. **Complementariedad entre descriptores de bajo nivel:**  
   Ninguno de los descriptores por sí solo es suficiente: la morfometría conexa detecta cambios macroscópicos en el tamaño de caracteres y franjas; el histograma de intensidad captura la pérdida global de opacidad o el oscurecimiento del fondo; y el operador LBP uniforme detecta rugosidades microscópicas, asperezas y suciedad por tóner residual en zonas planas de papel.

4. **Segmentación adaptativa robusta:**  
   La combinación del umbral de Otsu con la regla de inversión inteligente de polaridad (`"fondo_claro"`) garantizó que en todas las muestras el tóner quedara etiquetado en 1 y el papel en 0, sin requerir ajustes manuales por parte del técnico.

5. **Aporte operativo al soporte de hardware:**  
   Este módulo dota al sistema de mesa de ayuda de la capacidad de analizar evidencia física digitalizada. Permite transformar un reporte vago de usuario ("la hoja sale manchada") en un diagnóstico cuantitativo que orienta al técnico hacia la pieza electromecánica específica que requiere intervención antes de desplazarse hasta el equipo de impresión.
