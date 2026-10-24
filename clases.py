import os
import pydicom


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
        self.matrices_pixeles = []

        # Estos atributos se completarán más adelante
        self.cortes_escalados = []
        self.volumen = None
        self.imagen_corregida = None

        self._cargar_dicoms()
        self._extraer_metadatos()


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

        # Orden inicial usando InstanceNumber
        self.datasets.sort(
            key=lambda ds: int(
                getattr(
                    ds,
                    "InstanceNumber",
                    0
                )
            )
        )


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

        # Guardamos las matrices de píxeles de todos los cortes
        self.matrices_pixeles = [
            dataset.pixel_array
            for dataset in self.datasets
        ]


    def __str__(self):

        texto = "\nINFORMACIÓN DE LA SERIE DICOM\n"
        texto += "-" * 45 + "\n"

        texto += (
            f"Paciente: {self.nombre_paciente}\n"
        )

        texto += (
            f"Modalidad: {self.modalidad}\n"
        )

        texto += (
            f"Filas: {self.filas}\n"
        )

        texto += (
            f"Columnas: {self.columnas}\n"
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

        return texto