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

        self.imagen_componentes = None
        self.imagen_resultado = None
        self.region_recortada = None

        self.area_region_mm2 = None
        self.dimensiones_region_mm = None

        self.ultimo_aspect = None
        self.ultimo_umbral = None

        # =================================================
        # PROCESAMIENTO AUTOMÁTICO INICIAL
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

        if hasattr(
            primer_dataset,
            "SliceThickness"
        ):

            self.slice_thickness = float(
                primer_dataset.SliceThickness
            )

        else:

            self.slice_thickness = None

        self.tamano_voxel = (
            self.pixel_spacing[0],
            self.pixel_spacing[1],
            self.slice_thickness
        )

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

            centro = (
                ancho // 2,
                alto // 2
            )

            matriz_rotacion = (
                cv2.getRotationMatrix2D(
                    centro,
                    angulo,
                    1.0
                )
            )

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

        self.imagen_corregida = np.stack(
            volumen_rotado,
            axis=0
        )

        return self.imagen_corregida


    # =====================================================
    # NORMALIZAR Y ECUALIZAR CORTE
    # =====================================================

    def ecualizarCorte(self, indice_corte):

        if self.volumen is None:

            raise ValueError(
                "No existe un volumen para procesar."
            )

        if not isinstance(
            indice_corte,
            int
        ):

            raise ValueError(
                "El índice del corte debe ser entero."
            )

        if (
            indice_corte < 0
            or indice_corte >= self.volumen.shape[0]
        ):

            raise ValueError(
                f"El índice debe estar entre 0 y "
                f"{self.volumen.shape[0] - 1}."
            )

        volumen_copia = self.volumen.copy()

        corte = volumen_copia[
            indice_corte
        ]

        corte_uint8 = cv2.normalize(
            corte,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(
            np.uint8
        )

        corte_ecualizado = cv2.equalizeHist(
            corte_uint8
        )

        self.corte_normalizado = (
            corte_uint8
        )

        self.corte_ecualizado = (
            corte_ecualizado
        )

        carpeta_resultados = os.path.join(
            "resultados",
            "ecualizacion"
        )

        os.makedirs(
            carpeta_resultados,
            exist_ok=True
        )

        # Histograma
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

        # Imagen ecualizada
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
    # OBTENER CORTE SEGÚN EL PLANO
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

        # Transversal
        if plano in [
            "transversal",
            "axial"
        ]:

            if (
                indice < 0
                or indice >= self.volumen.shape[0]
            ):

                raise ValueError(
                    f"El índice transversal debe estar entre 0 y "
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

        # Coronal
        elif plano == "coronal":

            if (
                indice < 0
                or indice >= self.volumen.shape[1]
            ):

                raise ValueError(
                    f"El índice coronal debe estar entre 0 y "
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

        # Sagital
        elif plano == "sagital":

            if (
                indice < 0
                or indice >= self.volumen.shape[2]
            ):

                raise ValueError(
                    f"El índice sagital debe estar entre 0 y "
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

        if not isinstance(
            tamano_kernel,
            int
        ):

            raise ValueError(
                "El tamaño del kernel debe ser entero."
            )

        if tamano_kernel <= 0:

            raise ValueError(
                "El tamaño del kernel "
                "debe ser mayor que cero."
            )

        if not isinstance(
            iteraciones,
            int
        ):

            raise ValueError(
                "Las iteraciones deben ser enteras."
            )

        if iteraciones <= 0:

            raise ValueError(
                "Las iteraciones deben ser "
                "mayores que cero."
            )

        corte, aspect = self.obtenerCorte(
            plano,
            indice
        )

        corte_copia = corte.copy()

        corte_uint8 = cv2.normalize(
            corte_copia,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(
            np.uint8
        )

        if umbral is None:

            valor_umbral, binaria = (
                cv2.threshold(
                    corte_uint8,
                    0,
                    255,
                    cv2.THRESH_BINARY
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
                    cv2.THRESH_BINARY
                )
            )

        kernel = np.ones(
            (
                tamano_kernel,
                tamano_kernel
            ),
            dtype=np.uint8
        )

        apertura = cv2.morphologyEx(
            binaria,
            cv2.MORPH_OPEN,
            kernel,
            iterations=iteraciones
        )

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
    # TAMAÑO FÍSICO DEL PÍXEL SEGÚN PLANO
    # =====================================================

    def _tamanoPixelPlano(
        self,
        plano
    ):

        plano = plano.lower()

        if plano in [
            "transversal",
            "axial"
        ]:

            alto_pixel_mm = (
                self.pixel_spacing_escalado[0]
            )

            ancho_pixel_mm = (
                self.pixel_spacing_escalado[1]
            )

        elif plano == "coronal":

            alto_pixel_mm = (
                self.slice_thickness
            )

            ancho_pixel_mm = (
                self.pixel_spacing_escalado[1]
            )

        elif plano == "sagital":

            alto_pixel_mm = (
                self.slice_thickness
            )

            ancho_pixel_mm = (
                self.pixel_spacing_escalado[0]
            )

        else:

            raise ValueError(
                "El plano debe ser transversal, "
                "coronal o sagital."
            )

        return (
            alto_pixel_mm,
            ancho_pixel_mm
        )


    # =====================================================
    # DETECTAR REGIÓN DE INTERÉS
    # =====================================================

    def detectarRegionInteres(
        self,
        plano,
        indice,
        tamano_kernel,
        iteraciones,
        umbral=None,
        area_minima_pixeles=100,
        fraccion_maxima=0.15
    ):

        (
            corte_uint8,
            binaria,
            apertura,
            aspect
        ) = self.segmentarCorte(
            plano,
            indice,
            tamano_kernel,
            iteraciones,
            umbral
        )

        # =================================================
        # REGIONES PARA CONNECTED COMPONENTS
        # =================================================

        componentes = apertura.copy()

        self.imagen_componentes = (
            componentes
        )

        # =================================================
        # VISUALIZACIÓN DE DIAGNÓSTICO
        # =================================================

        plt.figure(
            figsize=(10, 5)
        )

        plt.subplot(
            1,
            2,
            1
        )

        plt.imshow(
            corte_uint8,
            cmap="gray"
        )

        plt.title(
            "Corte normalizado"
        )

        plt.axis(
            "off"
        )

        plt.subplot(
            1,
            2,
            2
        )

        plt.imshow(
            componentes,
            cmap="gray"
        )

        plt.title(
            "Regiones para Connected Components"
        )

        plt.axis(
            "off"
        )

        plt.tight_layout()
        plt.show()

        # =================================================
        # COMPONENTES CONECTADOS
        # =================================================

        (
            numero_componentes,
            etiquetas,
            estadisticas,
            centroides
        ) = cv2.connectedComponentsWithStats(
            componentes,
            connectivity=8
        )

        alto_imagen = (
            componentes.shape[0]
        )

        ancho_imagen = (
            componentes.shape[1]
        )

        area_total_imagen = (
            alto_imagen
            * ancho_imagen
        )

        area_maxima_pixeles = (
            area_total_imagen
            * fraccion_maxima
        )

        # =================================================
        # MOSTRAR COMPONENTES
        # =================================================

        print(
            "\nNúmero de componentes detectados:",
            numero_componentes - 1
        )

        for etiqueta in range(
            1,
            numero_componentes
        ):

            area = estadisticas[
                etiqueta,
                cv2.CC_STAT_AREA
            ]

            x = estadisticas[
                etiqueta,
                cv2.CC_STAT_LEFT
            ]

            y = estadisticas[
                etiqueta,
                cv2.CC_STAT_TOP
            ]

            ancho = estadisticas[
                etiqueta,
                cv2.CC_STAT_WIDTH
            ]

            alto = estadisticas[
                etiqueta,
                cv2.CC_STAT_HEIGHT
            ]

            print(
                f"Componente {etiqueta}: "
                f"area={area}, "
                f"x={x}, y={y}, "
                f"ancho={ancho}, alto={alto}"
            )

        # =================================================
        # FILTRAR CANDIDATOS
        # =================================================

        candidatos = []

        for etiqueta in range(
            1,
            numero_componentes
        ):

            x = estadisticas[
                etiqueta,
                cv2.CC_STAT_LEFT
            ]

            y = estadisticas[
                etiqueta,
                cv2.CC_STAT_TOP
            ]

            ancho = estadisticas[
                etiqueta,
                cv2.CC_STAT_WIDTH
            ]

            alto = estadisticas[
                etiqueta,
                cv2.CC_STAT_HEIGHT
            ]

            area = estadisticas[
                etiqueta,
                cv2.CC_STAT_AREA
            ]

            toca_borde = (
                x <= 0
                or y <= 0
                or x + ancho >= ancho_imagen - 1
                or y + alto >= alto_imagen - 1
            )

            if toca_borde:
                continue

            if area < area_minima_pixeles:
                continue

            if area > area_maxima_pixeles:
                continue

            candidatos.append(
                (
                    etiqueta,
                    area,
                    x,
                    y,
                    ancho,
                    alto
                )
            )

        if len(candidatos) == 0:

            raise ValueError(
                "No se encontraron regiones de interés "
                "con los criterios seleccionados."
            )

        candidatos.sort(
            key=lambda elemento: elemento[1],
            reverse=True
        )

        (
            etiqueta_seleccionada,
            area_pixeles,
            x,
            y,
            ancho,
            alto
        ) = candidatos[0]

        # =================================================
        # MÁSCARA DEL COMPONENTE SELECCIONADO
        # =================================================

        mascara_region = np.zeros_like(
            componentes
        )

        mascara_region[
            etiquetas == etiqueta_seleccionada
        ] = 255

        posiciones_y, posiciones_x = np.where(
            mascara_region == 255
        )

        puntos = np.column_stack(
            (
                posiciones_x,
                posiciones_y
            )
        ).astype(
            np.float32
        )

        # =================================================
        # CÍRCULO ENVOLVENTE
        # =================================================

        (
            centro,
            radio
        ) = cv2.minEnclosingCircle(
            puntos
        )

        centro = (
            int(centro[0]),
            int(centro[1])
        )

        radio = int(
            radio
        )

        # =================================================
        # ÁREA Y DIMENSIONES FÍSICAS
        # =================================================

        (
            alto_pixel_mm,
            ancho_pixel_mm
        ) = self._tamanoPixelPlano(
            plano
        )

        area_pixel_mm2 = (
            alto_pixel_mm
            * ancho_pixel_mm
        )

        area_mm2 = (
            area_pixeles
            * area_pixel_mm2
        )

        ancho_mm = (
            ancho
            * ancho_pixel_mm
        )

        alto_mm = (
            alto
            * alto_pixel_mm
        )

        self.area_region_mm2 = (
            area_mm2
        )

        self.dimensiones_region_mm = (
            ancho_mm,
            alto_mm
        )

        # =================================================
        # CONVERTIR A RGB
        # =================================================

        imagen_rgb = cv2.cvtColor(
            corte_uint8,
            cv2.COLOR_GRAY2RGB
        )

        # =================================================
        # DIBUJAR CÍRCULO
        # =================================================

        cv2.circle(
            imagen_rgb,
            centro,
            radio,
            (
                255,
                0,
                0
            ),
            3
        )

        # =================================================
        # TEXTO DEL ÁREA
        # =================================================

        texto_area = (
            f"Area: {area_mm2:.2f} mm2"
        )

        cv2.putText(
            imagen_rgb,
            texto_area,
            (
                max(
                    centro[0] - radio,
                    10
                ),
                max(
                    centro[1] - radio - 20,
                    30
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (
                255,
                0,
                0
            ),
            2,
            cv2.LINE_AA
        )

        # =================================================
        # TEXTO DE DIMENSIONES
        # =================================================

        texto_dimensiones = (
            f"{ancho_mm:.2f} x "
            f"{alto_mm:.2f} mm"
        )

        cv2.putText(
            imagen_rgb,
            texto_dimensiones,
            (
                max(
                    centro[0] - radio,
                    10
                ),
                min(
                    centro[1] + radio + 30,
                    alto_imagen - 10
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (
                255,
                0,
                0
            ),
            2,
            cv2.LINE_AA
        )

        self.imagen_resultado = (
            imagen_rgb
        )

        # =================================================
        # RECORTAR REGIÓN
        # =================================================

        margen = 30

        x_inicio = max(
            centro[0] - radio - margen,
            0
        )

        y_inicio = max(
            centro[1] - radio - margen,
            0
        )

        x_fin = min(
            centro[0] + radio + margen,
            ancho_imagen
        )

        y_fin = min(
            centro[1] + radio + margen,
            alto_imagen
        )

        region_recortada = imagen_rgb[
            y_inicio:y_fin,
            x_inicio:x_fin
        ]

        self.region_recortada = (
            region_recortada
        )

        # =================================================
        # GUARDAR RESULTADOS
        # =================================================

        carpeta_resultados = os.path.join(
            "resultados",
            "segmentacion"
        )

        os.makedirs(
            carpeta_resultados,
            exist_ok=True
        )

        ruta_imagen = os.path.join(
            carpeta_resultados,
            (
                f"{plano}_"
                f"corte_{indice}_"
                f"region.png"
            )
        )

        imagen_bgr = cv2.cvtColor(
            imagen_rgb,
            cv2.COLOR_RGB2BGR
        )

        cv2.imwrite(
            ruta_imagen,
            imagen_bgr
        )

        # =================================================
        # GRAFICAR RESULTADO FINAL
        # =================================================

        plt.figure(
            figsize=(13, 6)
        )

        plt.subplot(
            1,
            2,
            1
        )

        plt.imshow(
            imagen_rgb,
            aspect=aspect
        )

        plt.title(
            "Región de interés detectada"
        )

        plt.axis(
            "off"
        )

        plt.subplot(
            1,
            2,
            2
        )

        plt.imshow(
            region_recortada
        )

        plt.title(
            (
                f"Región recortada\n"
                f"Área: {area_mm2:.2f} mm²"
                f"{ancho_mm:.2f} x {alto_mm:.2f} mm"
            )
        )

        plt.axis(
            "off"
        )

        plt.tight_layout()

        ruta_grafico = os.path.join(
            carpeta_resultados,
            (
                f"{plano}_"
                f"corte_{indice}_"
                f"grafico.png"
            )
        )

        plt.savefig(
            ruta_grafico,
            dpi=300,
            bbox_inches="tight"
        )

        plt.show()
        plt.close()

        # =================================================
        # MOSTRAR INFORMACIÓN
        # =================================================

        print(
            "\nREGIÓN DE INTERÉS"
        )

        print(
            "Área en píxeles:",
            area_pixeles
        )

        print(
            "Área aproximada:",
            f"{area_mm2:.2f} mm²"
        )

        print(
            "Dimensiones aproximadas:",
            f"{ancho_mm:.2f} x "
            f"{alto_mm:.2f} mm"
        )

        print(
            "Centro:",
            centro
        )

        print(
            "Radio del círculo:",
            radio,
            "píxeles"
        )

        return (
            imagen_rgb,
            region_recortada,
            area_mm2
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


class GestorDICOM:

    def __init__(self):

        self.estudios = {}


    def agregar(
        self,
        nombre,
        estudio
    ):

        if not isinstance(
            estudio,
            SerieDICOM
        ):

            raise ValueError(
                "El objeto debe ser de tipo SerieDICOM."
            )

        self.estudios[
            nombre
        ] = estudio


    def buscar(
        self,
        nombre
    ):

        return self.estudios.get(
            nombre
        )


    def listar(self):

        return list(
            self.estudios.keys()
        )


    def eliminar(
        self,
        nombre
    ):

        if nombre in self.estudios:

            del self.estudios[
                nombre
            ]

            return True

        return False


    def __str__(self):

        if len(self.estudios) == 0:

            return (
                "No hay estudios DICOM almacenados."
            )

        texto = (
            "\nESTUDIOS DICOM ALMACENADOS\n"
        )

        texto += (
            "-" * 40
            + "\n"
        )

        for nombre, estudio in (
            self.estudios.items()
        ):

            texto += (
                f"{nombre} -> "
                f"{estudio.nombre_paciente} "
                f"({estudio.modalidad})\n"
            )

        return texto