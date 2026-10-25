import os

from clases import (
    SerieDICOM,
    GestorDICOM
)


gestor = GestorDICOM()
estudio_activo = None


def mostrar_menu():

    print("\n" + "=" * 55)
    print("       SISTEMA DE PROCESAMIENTO DICOM")
    print("=" * 55)

    print("\n1. Cargar estudio DICOM")
    print("2. Mostrar información del estudio")
    print("3. Corregir ángulo")
    print("4. Ecualizar corte")
    print("5. Segmentar región de interés")
    print("6. Listar estudios cargados")
    print("7. Activar estudio almacenado")
    print("8. Eliminar estudio del gestor")
    print("0. Salir")


def buscar_carpetas_dicom(
    carpeta_base="datos"
):

    carpetas_dicom = []

    for raiz, carpetas, archivos in os.walk(
        carpeta_base
    ):

        contiene_dicom = any(
            archivo.lower().endswith(".dcm")
            for archivo in archivos
        )

        if contiene_dicom:

            carpetas_dicom.append(
                raiz
            )

    carpetas_dicom.sort()

    return carpetas_dicom


def seleccionar_carpeta():

    carpetas = buscar_carpetas_dicom()

    if len(carpetas) == 0:

        raise ValueError(
            "No se encontraron carpetas "
            "con archivos DICOM."
        )

    print(
        "\nSeries DICOM disponibles:"
    )

    for i, carpeta in enumerate(
        carpetas,
        start=1
    ):

        print(
            f"{i}. {carpeta}"
        )

    while True:

        try:

            opcion = int(
                input(
                    "Seleccione una serie: "
                )
            )

            if (
                1
                <= opcion
                <= len(carpetas)
            ):

                return carpetas[
                    opcion - 1
                ]

            print(
                "Opción fuera de rango."
            )

        except ValueError:

            print(
                "Debe ingresar un número entero."
            )


while True:

    mostrar_menu()

    try:

        opcion = int(
            input(
                "\nSeleccione una opción: "
            )
        )

    except ValueError:

        print(
            "\nDebe ingresar un número entero."
        )

        continue


    # =============================================
    # SALIR
    # =============================================

    if opcion == 0:

        print(
            "\nPrograma finalizado."
        )

        break


    # =============================================
    # CARGAR ESTUDIO
    # =============================================

    elif opcion == 1:

        try:

            ruta = seleccionar_carpeta()

            estudio = SerieDICOM(
                ruta
            )

            nombre = os.path.basename(
                os.path.normpath(
                    ruta
                )
            )

            gestor.agregar(
                nombre,
                estudio
            )

            estudio_activo = estudio

            print(
                "\nEstudio cargado correctamente."
            )

            print(
                "Estudio activo:",
                nombre
            )

        except Exception as error:

            print(
                "\nError al cargar el estudio:",
                error
            )


    # =============================================
    # INFORMACIÓN
    # =============================================

    elif opcion == 2:

        if estudio_activo is None:

            print(
                "\nPrimero debe cargar un estudio."
            )

        else:

            print(
                estudio_activo
            )


    # =============================================
    # CORREGIR ÁNGULO
    # =============================================

    elif opcion == 3:

        if estudio_activo is None:

            print(
                "\nPrimero debe cargar un estudio."
            )

        else:

            try:

                angulo = float(
                    input(
                        "Ingrese ángulo en grados: "
                    )
                )

                estudio_activo.corregirAngulo(
                    angulo
                )

                print(
                    "\nCorrección aplicada correctamente."
                )

            except Exception as error:

                print(
                    "\nError:",
                    error
                )


    # =============================================
    # ECUALIZAR CORTE
    # =============================================

    elif opcion == 4:

        if estudio_activo is None:

            print(
                "\nPrimero debe cargar un estudio."
            )

        else:

            try:

                indice = int(
                    input(
                        "Ingrese índice del corte: "
                    )
                )

                estudio_activo.ecualizarCorte(
                    indice
                )

            except Exception as error:

                print(
                    "\nError:",
                    error
                )


    # =============================================
    # SEGMENTAR REGIÓN
    # =============================================

    elif opcion == 5:

        if estudio_activo is None:

            print(
                "\nPrimero debe cargar un estudio."
            )

        else:

            try:

                plano = input(
                    "Plano "
                    "(transversal/coronal/sagital): "
                ).strip().lower()

                indice = int(
                    input(
                        "Índice del corte: "
                    )
                )

                kernel = int(
                    input(
                        "Tamaño del kernel: "
                    )
                )

                iteraciones = int(
                    input(
                        "Número de iteraciones: "
                    )
                )

                respuesta = input(
                    "¿Desea usar umbral automático? "
                    "(s/n): "
                ).strip().lower()

                if respuesta == "s":

                    umbral = None

                else:

                    umbral = float(
                        input(
                            "Ingrese umbral "
                            "(0-255): "
                        )
                    )

                estudio_activo.detectarRegionInteres(
                    plano=plano,
                    indice=indice,
                    tamano_kernel=kernel,
                    iteraciones=iteraciones,
                    umbral=umbral
                )

            except Exception as error:

                print(
                    "\nError:",
                    error
                )


    # =============================================
    # LISTAR ESTUDIOS
    # =============================================

    elif opcion == 6:

        print(
            gestor
        )


    # =============================================
    # ACTIVAR ESTUDIO
    # =============================================

    elif opcion == 7:

        nombres = gestor.listar()

        if len(nombres) == 0:

            print(
                "\nNo hay estudios almacenados."
            )

        else:

            print(
                "\nEstudios disponibles:"
            )

            for i, nombre in enumerate(
                nombres,
                start=1
            ):

                print(
                    f"{i}. {nombre}"
                )

            try:

                seleccion = int(
                    input(
                        "Seleccione estudio: "
                    )
                )

                if (
                    1 <= seleccion <= len(nombres)
                ):

                    nombre = nombres[
                        seleccion - 1
                    ]

                    estudio_activo = gestor.buscar(
                        nombre
                    )

                    print(
                        "\nEstudio activo:",
                        nombre
                    )

                else:

                    print(
                        "\nSelección inválida."
                    )

            except ValueError:

                print(
                    "\nDebe ingresar un número entero."
                )


    # =============================================
    # ELIMINAR ESTUDIO
    # =============================================

    elif opcion == 8:

        nombre = input(
            "Nombre del estudio a eliminar: "
        ).strip()

        if gestor.eliminar(
            nombre
        ):

            print(
                "\nEstudio eliminado."
            )

        else:

            print(
                "\nNo se encontró ese estudio."
            )


    # =============================================
    # OPCIÓN INVÁLIDA
    # =============================================

    else:

        print(
            "\nOpción inválida."
        )