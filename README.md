# PARCIAL 3 - INFORMÁTICA II

## Sistema de procesamiento de imágenes DICOM

**Integrantes:**

- Samuel Arcos
- Yoreli Fuelpaz

**Asignatura:** Informática II  
**Programa:** Bioingeniería  
**Universidad:** Universidad de Antioquia

---

## Descripción del proyecto

Este proyecto desarrolla un sistema en Python para el procesamiento de imágenes médicas en formato DICOM. El programa permite cargar diferentes series de imágenes, extraer información del dataset, realizar reconstrucciones tridimensionales, aplicar correcciones geométricas, normalización, ecualización y segmentación de regiones de interés.

El desarrollo utiliza programación orientada a objetos y las librerías PyDicom, OpenCV, NumPy y Matplotlib.

El programa se ejecuta desde un menú principal que permite acceder a las diferentes funcionalidades implementadas.

---

## Estructura del proyecto

```text
PARCIAL_3_SAMUEL_ARCOS_YORELI_FUELPAZ/
│
├── clases.py
├── main.py
├── README.md
├── .gitignore
│
├── resultados/
│   ├── T2/
│   │   ├── ecualizacion/
│   │   └── segmentacion/
│   │
│   ├── img2/
│   │   ├── ecualizacion/
│   │   └── segmentacion/
│   │
│   └── MPRAGE_GRAPPA/
│       ├── ecualizacion/
│       └── segmentacion/
│
└── datos/
```

La carpeta `datos` se utiliza localmente para almacenar las imágenes DICOM y no se incluye en el repositorio ni en el archivo comprimido de entrega debido al tamaño de los archivos.

---

## Archivos principales

### `clases.py`

Contiene las clases y los métodos necesarios para procesar las imágenes DICOM.

Las clases principales son:

### `SerieDICOM`

Se encarga de:

- buscar y cargar archivos DICOM;
- extraer metadatos del dataset;
- almacenar las matrices de píxeles;
- escalar los cortes;
- reconstruir el volumen tridimensional;
- corregir el ángulo de las imágenes;
- normalizar y ecualizar cortes;
- seleccionar cortes transversales, coronales y sagitales;
- realizar segmentación;
- aplicar operaciones morfológicas;
- detectar componentes conectados;
- calcular áreas aproximadas en milímetros cuadrados;
- dibujar regiones de interés;
- guardar los resultados generados.

### `GestorDICOM`

Permite almacenar varios objetos de tipo `SerieDICOM`, buscarlos, listarlos, activarlos y eliminarlos durante la ejecución del programa.

---

## `main.py`

Contiene la implementación principal del sistema.

Desde este archivo se presenta el menú de opciones y se coordinan las diferentes funciones de las clases.

El menú permite:

```text
1. Cargar estudio DICOM
2. Mostrar información del estudio
3. Corregir ángulo
4. Ecualizar corte
5. Segmentar región de interés
6. Listar estudios cargados
7. Activar estudio almacenado
8. Eliminar estudio del gestor
0. Salir
```

---

## Carga de imágenes DICOM

El programa busca de forma automática las carpetas que contienen archivos con extensión `.dcm`.

Esto permite trabajar con diferentes estructuras de carpetas sin tener que escribir manualmente la ruta de cada estudio.

Durante las pruebas se utilizaron imágenes pertenecientes a:

- PPMI
- Sarcoma
- T2

Los archivos DICOM se cargan utilizando:

```python
pydicom.dcmread()
```

---

## Información extraída del dataset

Para cada serie se almacenan como atributos:

- número de filas;
- número de columnas;
- nombre del paciente;
- modalidad;
- `PixelSpacing`;
- `SliceThickness`;
- tamaño del voxel;
- matrices de píxeles;
- volumen tridimensional.

---

## Escalado de imágenes

Cada corte DICOM se escala automáticamente al doble de su tamaño mediante OpenCV.

Se utiliza:

```python
cv2.resize()
```

con factores:

```python
fx=2
fy=2
```

Al duplicar el número de píxeles, el `PixelSpacing` utilizado para los cálculos físicos se ajusta dividiendo entre dos las dimensiones correspondientes a filas y columnas.

---

## Reconstrucción 3D

Después de escalar los cortes, estos se agrupan utilizando:

```python
np.stack()
```

El resultado se almacena en el atributo:

```python
self.volumen
```

La estructura general del volumen es:

```text
número de cortes × filas × columnas
```

Los cortes se ordenan utilizando el atributo DICOM `InstanceNumber`.

---

## Corrección de ángulo

El método:

```python
corregirAngulo()
```

recibe un valor numérico en grados.

Para cada corte se calcula el centro de la imagen y se genera una matriz de rotación mediante:

```python
cv2.getRotationMatrix2D()
```

Posteriormente se aplica la transformación mediante:

```python
cv2.warpAffine()
```

El volumen corregido se almacena como atributo del objeto sin reemplazar el volumen original.

---

## Normalización y ecualización

El método de ecualización:

1. crea una copia del volumen;
2. selecciona un corte;
3. normaliza la imagen al rango de 0 a 255;
4. convierte la imagen a `uint8`;
5. realiza la ecualización del histograma;
6. muestra el histograma;
7. muestra la imagen ecualizada;
8. guarda los resultados.

La normalización se realiza mediante:

```python
cv2.normalize()
```

y la ecualización mediante:

```python
cv2.equalizeHist()
```

Los resultados se guardan dentro de:

```text
resultados/NOMBRE_ESTUDIO/ecualizacion/
```

---

## Selección de planos

El programa permite trabajar con los siguientes planos:

### Transversal

```python
volumen[indice, :, :]
```

### Coronal

```python
volumen[:, indice, :]
```

### Sagital

```python
volumen[:, :, indice]
```

El programa también calcula el valor de `aspect` teniendo en cuenta las dimensiones físicas de los píxeles.

---

## Segmentación

Para la segmentación se permite al usuario seleccionar:

- plano;
- índice del corte;
- tamaño del kernel;
- número de iteraciones;
- umbral automático o manual.

El corte se normaliza a `uint8` y posteriormente se aplica una umbralización.

El usuario puede utilizar un valor manual entre 0 y 255 o utilizar el método automático de Otsu.

---

## Apertura morfológica

Después de la binarización se realiza una apertura morfológica mediante:

```python
cv2.morphologyEx()
```

utilizando:

```python
cv2.MORPH_OPEN
```

El tamaño del kernel y el número de iteraciones son definidos por el usuario.

---

## Componentes conectados

Después de la segmentación se utiliza:

```python
cv2.connectedComponentsWithStats()
```

para identificar las regiones independientes presentes en la imagen binaria.

Cada componente contiene información relacionada con:

- posición;
- ancho;
- alto;
- área en píxeles;
- centroide.

Se descartan componentes demasiado pequeños, demasiado grandes o que se encuentren unidos al borde de la imagen.

La región candidata de mayor área que cumple los criterios se selecciona como región de interés.

---

## Área en milímetros cuadrados

El área aproximada se calcula a partir del número de píxeles del componente seleccionado y las dimensiones físicas del píxel.

Para un corte transversal:

```text
Área de un píxel =
PixelSpacingFila × PixelSpacingColumna
```

Por tanto:

```text
Área de la región =
Área en píxeles × Área física de un píxel
```

Para los planos sagital y coronal se utiliza también el `SliceThickness` para representar correctamente las dimensiones físicas de los ejes.

---

## Región de interés

Después de identificar la región seleccionada:

1. se calcula un círculo envolvente;
2. se convierte el corte a espacio RGB;
3. se dibuja el círculo utilizando OpenCV;
4. se escribe el área aproximada;
5. se muestran las dimensiones aproximadas en milímetros;
6. se genera un recorte de la región;
7. se guarda el resultado.

El círculo se obtiene mediante:

```python
cv2.minEnclosingCircle()
```

y se dibuja mediante:

```python
cv2.circle()
```

El texto se agrega mediante:

```python
cv2.putText()
```

---

## Organización de resultados

Los resultados se almacenan separados por estudio para evitar sobrescribir archivos.

Ejemplo:

```text
resultados/
├── T2/
│   ├── ecualizacion/
│   └── segmentacion/
│
├── img2/
│   ├── ecualizacion/
│   └── segmentacion/
│
└── MPRAGE_GRAPPA/
    ├── ecualizacion/
    └── segmentacion/
```

Los resultados incluyen:

- histogramas;
- imágenes ecualizadas;
- gráficos de ecualización;
- imágenes con regiones de interés;
- gráficos con regiones recortadas y medidas físicas.

---

## Validaciones

El programa incluye validaciones para evitar errores durante la interacción con el usuario.

Se validan:

- opciones del menú;
- valores enteros;
- valores decimales;
- índices de cortes;
- plano seleccionado;
- tamaño del kernel;
- número de iteraciones;
- valores de umbral;
- existencia de estudios cargados.

Las validaciones permiten que una entrada incorrecta no cierre el programa.

---

## Librerías utilizadas

```python
os
pydicom
cv2
numpy
matplotlib
```

## Ejecución

Desde la carpeta principal del proyecto ejecutar:

```bash
python main.py
```

Si se está utilizando directamente el Python de Anaconda en Windows:

```powershell
& C:\ProgramData\anaconda3\python.exe main.py
```

---

## Datos DICOM

Las imágenes DICOM utilizadas durante las pruebas deben ubicarse dentro de:

```text
datos/
```

El programa detecta automáticamente las carpetas que contienen archivos `.dcm`.

Los archivos DICOM no están incluidos en el repositorio ni en el archivo comprimido de entrega debido a su tamaño.

---

## Resultados de prueba

Se realizaron pruebas utilizando estudios pertenecientes a:

- T2;
- Sarcoma;
- PPMI.

Las imágenes generadas durante estas pruebas se encuentran dentro de la carpeta:

```text
resultados/
```

---

## Repositorio

Repositorio del proyecto:

https://github.com/samuelarcos-web/PARCIAL_3_SAMUEL_ARCOS_YORELI_FUELPAZ

El repositorio contiene el historial de desarrollo y los commits realizados por los integrantes.

---

## Entrega

El archivo comprimido de entrega debe contener principalmente:

```text
P3_SamuelArcos_YoreliFuelpaz/
│
├── clases.py
├── main.py
├── README.md
└── resultados/
```

No se deben incluir:

```text
datos/
.vscode/
__pycache__/
.git/
```

debido a que son archivos de trabajo local o contienen las imágenes DICOM originales.

---

## Consideraciones

La segmentación depende de las características de intensidad de cada estudio. Por esta razón, el sistema permite utilizar un umbral automático mediante Otsu o seleccionar manualmente un valor entre 0 y 255.

Las regiones identificadas por el sistema corresponden a componentes obtenidos mediante procesamiento de imágenes. La selección realizada por el programa debe interpretarse como una región de interés computacional y no como un diagnóstico clínico.