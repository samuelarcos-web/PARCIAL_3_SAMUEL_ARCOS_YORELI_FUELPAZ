import os

import cv2
import numpy as np
import pydicom
import matplotlib.pyplot as plt


class SerieDICOM:

    def __init__(self, ruta_carpeta):

        self.ruta_carpeta = ruta_carpeta

        # =================================================
        # DATASETS DICOM
        # =================================================

        self.datasets = []

        # =================================================
        # METADATOS
        # =================================================

        self.filas = None
        self.columnas = None
        self.nombre_paciente = None
        self.modalidad = None

        self.pixel_spacing = None
        self.pixel_spacing_escalado = None

        self.slice_thickness = None
        self.tamano_voxel = None

        # =================================================
        # DATOS DE IMAGEN
        # =================================================

        self.matrices_pixeles = []

        self.cortes_escalados = []

        self.volumen = None

        # =================================================
        # RESULTADOS DE PROCESAMIENTO
        # =================================================

        self.imagen_corregida = None

        self.corte_normalizado = None
        self.corte_ecualizado = None

        self.corte_segmentado = None
        self.imagen_binaria = None
        self.imagen_apertura = None

        self.ultimo_aspect = None
        self.ultimo_umbral = None

        # =================================================
        # PROCESAMIENTO INICIAL AUTOMÁTICO
        # =================================================

        self._cargar_dicoms()

        self._extraer_metadatos()

        self._escalar_cortes()

        self._reconstruir_volumen()


    # =====================================================
    # BUSCAR ARCHIVOS DICOM
    # =====================================================

    def _buscar_archivos_dicom(self):

        archivos_dicom = []

        for raiz, carpetas, archivos in os.walk(
            self.ruta_carpeta
        ):

            for archivo in archivos:

                if archivo.lower().endswith(".dcm"):

                    ruta_completa = os.path.join(
                        raiz,
                        archivo
                    )

                    archivos_dicom.append(
                        ruta_completa
                    )

        return archivos_dicom


    # =====================================================
    # CARGAR DATASETS DICOM
    # =====================================================

    def _cargar_dicoms(self):

        archivos = self._buscar_archivos_dicom()

        if len(archivos) == 0:

            raise ValueError(
                "No se encontraron archivos DICOM "
                "en la carpeta seleccionada."
            )

        for ruta in archivos:

            try:

                dataset = pydicom.dcmread(
                    ruta
                )

                self.datasets.append(
                    dataset
                )

            except Exception as error:

                print(
                    f"No se pudo cargar {ruta}: {error}"
                )

        if len(self.datasets) == 0:

            raise ValueError(
                "No fue posible cargar ningún archivo DICOM."
            )

        # ---------------------------------------------
        # ORDEN INICIAL POR INSTANCENUMBER
        # ---------------------------------------------

        self.datasets.sort(
            key=lambda ds: int(
                getattr(
                    ds,
                    "InstanceNumber",
                    0
                )
            )
        )


    # =====================================================
    # EXTRAER METADATOS
    # =====================================================

    def _extraer_metadatos(self):

        primer_dataset = self.datasets[0]

        # ---------------------------------------------
        # FILAS
        # ---------------------------------------------

        self.filas = int(
            getattr(
                primer_dataset,
                "Rows",
                0
            )
        )

        # ---------------------------------------------
        # COLUMNAS
        # ---------------------------------------------

        self.columnas = int(
            getattr(
                primer_dataset,
                "Columns",
                0
            )
        )

        # ---------------------------------------------
        # NOMBRE DEL PACIENTE
        # ---------------------------------------------

        self.nombre_paciente = str(
            getattr(
                primer_dataset,
                "PatientName",
                "Desconocido"
            )
        )

        # ---------------------------------------------
        # MODALIDAD
        # ---------------------------------------------

        self.modalidad = str(
            getattr(
                primer_dataset,
                "Modality",
                "Desconocida"
            )
        )

        # ---------------------------------------------
        # PIXEL SPACING
        # ---------------------------------------------

        if hasattr(
            primer_dataset,
            "PixelSpacing"
        ):

            self.pixel_spacing = (
                float(
                    primer_dataset.PixelSpacing[0]
                ),
                float(
                    primer_dataset.PixelSpacing[1]
                )
            )

        else:

            self.pixel_spacing = (
                None,
                None
            )

        # ---------------------------------------------
        # SLICE THICKNESS
        # ---------------------------------------------

        if hasattr(
            primer_dataset,
            "SliceThickness"
        ):

            self.slice_thickness = float(
                primer_dataset.SliceThickness
            )

        else:

            self.slice_thickness = None

        # ---------------------------------------------
        # TAMAÑO DEL VOXEL
        # ---------------------------------------------

        self.tamano_voxel = (
            self.pixel_spacing[0],
            self.pixel_spacing[1],
            self.slice_thickness
        )

        # ---------------------------------------------
        # MATRICES DE PÍXELES
        # ---------------------------------------------

        self.matrices_pixeles = [
            dataset.pixel_array
            for dataset in self.datasets
        ]


    # =====================================================
    # ESCALAR CORTES AL DOBLE
    # =====================================================

    def _escalar_cortes(self):

        self.cortes_escalados = []

        for matriz in self.matrices_pixeles:

            corte_escalado = cv2.resize(
                matriz,
                None,
                fx=2,
                fy=2,
                interpolation=cv2.INTER_LINEAR
            )

            self.cortes_escalados.append(
                corte_escalado
            )

        # ---------------------------------------------
        # ACTUALIZAR PIXEL SPACING EN X E Y
        # ---------------------------------------------

        if (
            self.pixel_spacing[0] is not None
            and self.pixel_spacing[1] is not None
        ):

            self.pixel_spacing_escalado = (
                self.pixel_spacing[0] / 2,
                self.pixel_spacing[1] / 2
            )


    # =====================================================
    # RECONSTRUIR VOLUMEN 3D
    # =====================================================

    def _reconstruir_volumen(self):

        if len(self.cortes_escalados) == 0:

            raise ValueError(
                "No existen cortes escalados "
                "para construir el volumen."
            )

        self.volumen = np.stack(
            self.cortes_escalados,
            axis=0
        )


    # =====================================================
    # CORREGIR ÁNGULO
    # =====================================================

    def corregirAngulo(self, angulo):

        if not isinstance(
            angulo,
            (int, float)
        ):

            raise ValueError(
                "El ángulo debe ser un valor numérico."
            )

        if self.volumen is None:

            raise ValueError(
                "No existe un volumen para corregir."
            )

        volumen_rotado = []

        for corte in self.volumen:

            alto, ancho = corte.shape

            # -----------------------------------------
            # CENTRO DE LA IMAGEN
            # -----------------------------------------

            centro = (
                ancho // 2,
                alto // 2
            )

            # -----------------------------------------
            # MATRIZ DE ROTACIÓN
            # -----------------------------------------

            matriz_rotacion = (
                cv2.getRotationMatrix2D(
                    centro,
                    angulo,
                    1.0
                )
            )

            # -----------------------------------------
            # APLICAR TRANSFORMACIÓN GEOMÉTRICA
            # -----------------------------------------

            corte_rotado = cv2.warpAffine(
                corte,
                matriz_rotacion,
                (
                    ancho,
                    alto
                )
            )

            volumen_rotado.append(
                corte_rotado
            )

        # ---------------------------------------------
        # GUARDAR RESULTADO
        # ---------------------------------------------

        self.imagen_corregida = np.stack(
            volumen_rotado,
            axis=0
        )

        return self.imagen_corregida


    # =====================================================
    # ECUALIZAR CORTE
    # =====================================================

    def ecualizarCorte(self, indice_corte):

        # ---------------------------------------------
        # VALIDAR VOLUMEN
        # ---------------------------------------------

        if self.volumen is None:

            raise ValueError(
                "No existe un volumen para procesar."
            )

        # ---------------------------------------------
        # VALIDAR ÍNDICE
        # ---------------------------------------------

        if not isinstance(
            indice_corte,
            int
        ):

            raise ValueError(
                "El índice del corte debe ser "
                "un número entero."
            )

        if (
            indice_corte < 0
            or indice_corte
            >= self.volumen.shape[0]
        ):

            raise ValueError(
                f"El índice debe estar entre 0 y "
                f"{self.volumen.shape[0] - 1}."
            )

        # ---------------------------------------------
        # COPIA DEL VOLUMEN
        # ---------------------------------------------

        volumen_copia = self.volumen.copy()

        corte = volumen_copia[
            indice_corte
        ]

        # ---------------------------------------------
        # NORMALIZAR A UINT8
        # ---------------------------------------------

        corte_uint8 = cv2.normalize(
            corte,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(
            np.uint8
        )

        # ---------------------------------------------
        # ECUALIZAR HISTOGRAMA
        # ---------------------------------------------

        corte_ecualizado = cv2.equalizeHist(
            corte_uint8
        )

        # ---------------------------------------------
        # GUARDAR COMO ATRIBUTOS
        # ---------------------------------------------

        self.corte_normalizado = (
            corte_uint8
        )

        self.corte_ecualizado = (
            corte_ecualizado
        )

        # ---------------------------------------------
        # CREAR CARPETA
        # ---------------------------------------------

        carpeta_resultados = os.path.join(
            "resultados",
            "ecualizacion"
        )

        os.makedirs(
            carpeta_resultados,
            exist_ok=True
        )

        # ---------------------------------------------
        # HISTOGRAMA
        # ---------------------------------------------

        plt.figure(
            figsize=(8, 5)
        )

        plt.hist(
            corte_ecualizado.ravel(),
            bins=256,
            range=[
                0,
                256
            ]
        )

        plt.title(
            f"Histograma del corte "
            f"ecualizado {indice_corte}"
        )

        plt.xlabel(
            "Intensidad de gris"
        )

        plt.ylabel(
            "Frecuencia"
        )

        plt.tight_layout()

        ruta_histograma = os.path.join(
            carpeta_resultados,
            f"histograma_corte_"
            f"{indice_corte}.png"
        )

        plt.savefig(
            ruta_histograma,
            dpi=300
        )

        plt.show()

        plt.close()

        # ---------------------------------------------
        # GRÁFICO DE IMAGEN ECUALIZADA
        # ---------------------------------------------

        plt.figure(
            figsize=(7, 7)
        )

        plt.imshow(
            corte_ecualizado,
            cmap="gray"
        )

        plt.title(
            f"Corte ecualizado "
            f"{indice_corte}"
        )

        plt.axis(
            "off"
        )

        plt.tight_layout()

        ruta_grafico = os.path.join(
            carpeta_resultados,
            f"grafico_ecualizado_corte_"
            f"{indice_corte}.png"
        )

        plt.savefig(
            ruta_grafico,
            dpi=300,
            bbox_inches="tight"
        )

        plt.show()

        plt.close()

        # ---------------------------------------------
        # GUARDAR IMAGEN CON OPENCV
        # ---------------------------------------------

        ruta_imagen = os.path.join(
            carpeta_resultados,
            f"imagen_ecualizada_corte_"
            f"{indice_corte}.png"
        )

        cv2.imwrite(
            ruta_imagen,
            corte_ecualizado
        )

        return corte_ecualizado


    # =====================================================
    # OBTENER CORTE SEGÚN PLANO
    # =====================================================

    def obtenerCorte(
        self,
        plano,
        indice
    ):

        if self.volumen is None:

            raise ValueError(
                "No existe un volumen 3D."
            )

        if self.pixel_spacing_escalado is None:

            raise ValueError(
                "No se pudo determinar "
                "el PixelSpacing escalado."
            )

        if self.slice_thickness is None:

            raise ValueError(
                "No se pudo determinar "
                "el SliceThickness."
            )

        plano = plano.lower()

        # ---------------------------------------------
        # TRANSVERSAL / AXIAL
        # ---------------------------------------------

        if plano in [
            "transversal",
            "axial"
        ]:

            if (
                indice < 0
                or indice
                >= self.volumen.shape[0]
            ):

                raise ValueError(
                    f"El índice transversal "
                    f"debe estar entre 0 y "
                    f"{self.volumen.shape[0] - 1}."
                )

            corte = self.volumen[
                indice,
                :,
                :
            ]

            aspect = (
                self.pixel_spacing_escalado[0]
                /
                self.pixel_spacing_escalado[1]
            )

        # ---------------------------------------------
        # CORONAL
        # ---------------------------------------------

        elif plano == "coronal":

            if (
                indice < 0
                or indice
                >= self.volumen.shape[1]
            ):

                raise ValueError(
                    f"El índice coronal "
                    f"debe estar entre 0 y "
                    f"{self.volumen.shape[1] - 1}."
                )

            corte = self.volumen[
                :,
                indice,
                :
            ]

            aspect = (
                self.slice_thickness
                /
                self.pixel_spacing_escalado[1]
            )

        # ---------------------------------------------
        # SAGITAL
        # ---------------------------------------------

        elif plano == "sagital":

            if (
                indice < 0
                or indice
                >= self.volumen.shape[2]
            ):

                raise ValueError(
                    f"El índice sagital "
                    f"debe estar entre 0 y "
                    f"{self.volumen.shape[2] - 1}."
                )

            corte = self.volumen[
                :,
                :,
                indice
            ]

            aspect = (
                self.slice_thickness
                /
                self.pixel_spacing_escalado[0]
            )

        else:

            raise ValueError(
                "El plano debe ser transversal, "
                "coronal o sagital."
            )

        return (
            corte,
            aspect
        )


    # =====================================================
    # SEGMENTAR CORTE
    # =====================================================

    def segmentarCorte(
        self,
        plano,
        indice,
        tamano_kernel,
        iteraciones,
        umbral=None
    ):

        # ---------------------------------------------
        # VALIDAR KERNEL
        # ---------------------------------------------

        if not isinstance(
            tamano_kernel,
            int
        ):

            raise ValueError(
                "El tamaño del kernel "
                "debe ser entero."
            )

        if tamano_kernel <= 0:

            raise ValueError(
                "El tamaño del kernel "
                "debe ser mayor que cero."
            )

        # ---------------------------------------------
        # VALIDAR ITERACIONES
        # ---------------------------------------------

        if not isinstance(
            iteraciones,
            int
        ):

            raise ValueError(
                "Las iteraciones deben ser "
                "un número entero."
            )

        if iteraciones <= 0:

            raise ValueError(
                "Las iteraciones deben ser "
                "mayores que cero."
            )

        # ---------------------------------------------
        # OBTENER CORTE
        # ---------------------------------------------

        corte, aspect = self.obtenerCorte(
            plano,
            indice
        )

        corte_copia = corte.copy()

        # ---------------------------------------------
        # NORMALIZAR A UINT8
        # ---------------------------------------------

        corte_uint8 = cv2.normalize(
            corte_copia,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(
            np.uint8
        )

        # ---------------------------------------------
        # UMBRALIZACIÓN
        # ---------------------------------------------

        if umbral is None:

            valor_umbral, binaria = (
                cv2.threshold(
                    corte_uint8,
                    0,
                    255,
                    cv2.THRESH_BINARY_INV
                    + cv2.THRESH_OTSU
                )
            )

        else:

            if (
                umbral < 0
                or umbral > 255
            ):

                raise ValueError(
                    "El umbral debe estar "
                    "entre 0 y 255."
                )

            valor_umbral, binaria = (
                cv2.threshold(
                    corte_uint8,
                    umbral,
                    255,
                    cv2.THRESH_BINARY_INV
                )
            )

        # ---------------------------------------------
        # CREAR KERNEL
        # ---------------------------------------------

        kernel = np.ones(
            (
                tamano_kernel,
                tamano_kernel
            ),
            dtype=np.uint8
        )

        # ---------------------------------------------
        # APERTURA MORFOLÓGICA
        # ---------------------------------------------

        apertura = cv2.morphologyEx(
            binaria,
            cv2.MORPH_OPEN,
            kernel,
            iterations=iteraciones
        )

        # ---------------------------------------------
        # GUARDAR RESULTADOS
        # ---------------------------------------------

        self.corte_segmentado = (
            corte_uint8
        )

        self.imagen_binaria = (
            binaria
        )

        self.imagen_apertura = (
            apertura
        )

        self.ultimo_aspect = (
            aspect
        )

        self.ultimo_umbral = (
            valor_umbral
        )

        return (
            corte_uint8,
            binaria,
            apertura,
            aspect
        )


    # =====================================================
    # REPRESENTACIÓN DEL OBJETO
    # =====================================================

    def __str__(self):

        texto = (
            "\nINFORMACIÓN DE LA SERIE DICOM\n"
        )

        texto += (
            "-" * 45
            + "\n"
        )

        texto += (
            f"Paciente: "
            f"{self.nombre_paciente}\n"
        )

        texto += (
            f"Modalidad: "
            f"{self.modalidad}\n"
        )

        texto += (
            f"Filas: "
            f"{self.filas}\n"
        )

        texto += (
            f"Columnas: "
            f"{self.columnas}\n"
        )

        texto += (
            f"Número de cortes: "
            f"{len(self.datasets)}\n"
        )

        texto += (
            f"Pixel Spacing: "
            f"{self.pixel_spacing} mm\n"
        )

        texto += (
            f"Pixel Spacing escalado: "
            f"{self.pixel_spacing_escalado} mm\n"
        )

        texto += (
            f"Slice Thickness: "
            f"{self.slice_thickness} mm\n"
        )

        texto += (
            f"Tamaño del voxel original: "
            f"{self.tamano_voxel} mm\n"
        )

        if self.volumen is not None:

            texto += (
                f"Forma del volumen 3D: "
                f"{self.volumen.shape}\n"
            )

        if self.imagen_corregida is not None:

            texto += (
                f"Forma del volumen corregido: "
                f"{self.imagen_corregida.shape}\n"
            )

        return texto