import os

import cv2
import numpy as np
import pydicom
import matplotlib.pyplot as plt


class SerieDICOM:

    def __init__(self, ruta_carpeta):

        self.ruta_carpeta = ruta_carpeta

        # Lista de datasets DICOM cargados
        self.datasets = []

        # Atributos solicitados por el parcial
        self.filas = None
        self.columnas = None
        self.nombre_paciente = None
        self.modalidad = None
        self.pixel_spacing = None
        self.slice_thickness = None
        self.tamano_voxel = None

        # Matrices originales
        self.matrices_pixeles = []

        # Cortes escalados al doble
        self.cortes_escalados = []

        # Volumen 3D
        self.volumen = None

        # Resultado de la corrección de ángulo
        self.imagen_corregida = None

        # Proceso de carga
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

        # Orden inicial por InstanceNumber
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

        self.filas = int(
            getattr(
                primer_dataset,
                "Rows",
                0
            )
        )

        self.columnas = int(
            getattr(
                primer_dataset,
                "Columns",
                0
            )
        )

        self.nombre_paciente = str(
            getattr(
                primer_dataset,
                "PatientName",
                "Desconocido"
            )
        )

        self.modalidad = str(
            getattr(
                primer_dataset,
                "Modality",
                "Desconocida"
            )
        )

        # PixelSpacing
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

        # SliceThickness
        if hasattr(
            primer_dataset,
            "SliceThickness"
        ):

            self.slice_thickness = float(
                primer_dataset.SliceThickness
            )

        else:

            self.slice_thickness = None

        # Tamaño del voxel
        self.tamano_voxel = (
            self.pixel_spacing[0],
            self.pixel_spacing[1],
            self.slice_thickness
        )

        # Matrices de píxeles originales
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

            # Centro de la imagen
            centro = (
                ancho // 2,
                alto // 2
            )

            # Matriz de rotación
            matriz_rotacion = (
                cv2.getRotationMatrix2D(
                    centro,
                    angulo,
                    1.0
                )
            )

            # Aplicar transformación geométrica
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

        # Guardar resultado como atributo
        self.imagen_corregida = np.stack(
            volumen_rotado,
            axis=0
        )

        return self.imagen_corregida

    def ecualizarCorte(self, indice_corte):

        # -------------------------------------------------
        # VALIDAR QUE EXISTA EL VOLUMEN
        # -------------------------------------------------

        if self.volumen is None:

            raise ValueError(
                "No existe un volumen para procesar."
            )

        # -------------------------------------------------
        # VALIDAR ÍNDICE DEL CORTE
        # -------------------------------------------------

        if not isinstance(indice_corte, int):

            raise ValueError(
                "El índice del corte debe ser un número entero."
            )

        if (
            indice_corte < 0
            or indice_corte >= self.volumen.shape[0]
        ):

            raise ValueError(
                f"El índice debe estar entre 0 y "
                f"{self.volumen.shape[0] - 1}."
            )

        # -------------------------------------------------
        # CREAR COPIA DEL VOLUMEN
        # -------------------------------------------------

        volumen_copia = self.volumen.copy()

        # Seleccionar corte
        corte = volumen_copia[indice_corte]

        # -------------------------------------------------
        # NORMALIZAR A UINT8
        # -------------------------------------------------

        corte_uint8 = cv2.normalize(
            corte,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(np.uint8)

        # -------------------------------------------------
        # ECUALIZACIÓN DEL HISTOGRAMA
        # -------------------------------------------------

        corte_ecualizado = cv2.equalizeHist(
            corte_uint8
        )

        # Guardar resultados como atributos
        self.corte_normalizado = corte_uint8
        self.corte_ecualizado = corte_ecualizado

        # -------------------------------------------------
        # CREAR CARPETA DE RESULTADOS
        # -------------------------------------------------

        carpeta_resultados = os.path.join(
            "resultados",
            "ecualizacion"
        )

        os.makedirs(
            carpeta_resultados,
            exist_ok=True
        )

        # -------------------------------------------------
        # HISTOGRAMA
        # -------------------------------------------------

        plt.figure(
            figsize=(8, 5)
        )

        plt.hist(
            corte_ecualizado.ravel(),
            bins=256,
            range=[0, 256]
        )

        plt.title(
            f"Histograma del corte ecualizado "
            f"{indice_corte}"
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
            f"histograma_corte_{indice_corte}.png"
        )

        plt.savefig(
            ruta_histograma,
            dpi=300
        )

        plt.show()

        plt.close()

        # -------------------------------------------------
        # MOSTRAR IMAGEN ECUALIZADA
        # -------------------------------------------------

        plt.figure(
            figsize=(7, 7)
        )

        plt.imshow(
            corte_ecualizado,
            cmap="gray"
        )

        plt.title(
            f"Corte ecualizado {indice_corte}"
        )

        plt.axis(
            "off"
        )

        plt.tight_layout()

        ruta_grafico = os.path.join(
            carpeta_resultados,
            f"grafico_ecualizado_corte_{indice_corte}.png"
        )

        plt.savefig(
            ruta_grafico,
            dpi=300,
            bbox_inches="tight"
        )

        plt.show()

        plt.close()

        # -------------------------------------------------
        # GUARDAR IMAGEN ECUALIZADA
        # -------------------------------------------------

        ruta_imagen = os.path.join(
            carpeta_resultados,
            f"imagen_ecualizada_corte_{indice_corte}.png"
        )

        cv2.imwrite(
            ruta_imagen,
            corte_ecualizado
        )

        return corte_ecualizado

    # =====================================================
    # REPRESENTACIÓN DEL OBJETO
    # =====================================================

    def __str__(self):

        texto = "\nINFORMACIÓN DE LA SERIE DICOM\n"
        texto += "-" * 45 + "\n"

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
            f"Slice Thickness: "
            f"{self.slice_thickness} mm\n"
        )

        texto += (
            f"Tamaño del voxel: "
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