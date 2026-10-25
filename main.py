import os

from clases import SerieDICOM, GestorDICOM


# OBJETOS PRINCIPALES

gestor = GestorDICOM()
estudio_activo = None
nombre_estudio_activo = None


# VALIDACIONES

def validar_entero(mensaje, minimo=None, maximo=None):
    while True:
        try:
            valor = int(input(mensaje))

            if minimo is not None and valor < minimo:
                print(f"El valor mínimo permitido es {minimo}.")
                continue

            if maximo is not None and valor > maximo:
                print(f"El valor máximo permitido es {maximo}.")
                continue

            return valor

        except ValueError:
            print("Debe ingresar un número entero.")


def validar_float(mensaje, minimo=None, maximo=None):
    while True:
        try:
            valor = float(input(mensaje))

            if minimo is not None and valor < minimo:
                print(f"El valor mínimo permitido es {minimo}.")
                continue

            if maximo is not None and valor > maximo:
                print(f"El valor máximo permitido es {maximo}.")
                continue

            return valor

        except ValueError:
            print("Debe ingresar un valor numérico.")


def validar_plano():
    planos_validos = [
        "transversal",
        "axial",
        "coronal",
        "sagital"
    ]

    while True:
        plano = input(
            "Plano (transversal/coronal/sagital): "
        ).strip().lower()

        if plano in planos_validos:
            return plano

        print("Plano inválido.")


def obtener_maximo_indice(estudio, plano):
    if plano in ["transversal", "axial"]:
        return estudio.volumen.shape[0] - 1

    if plano == "coronal":
        return estudio.volumen.shape[1] - 1

    if plano == "sagital":
        return estudio.volumen.shape[2] - 1


# BUSCAR CARPETAS DICOM

def buscar_carpetas_dicom(carpeta_base="datos"):
    carpetas_dicom = []

    for raiz, carpetas, archivos in os.walk(carpeta_base):
        contiene_dicom = any(
            archivo.lower().endswith(".dcm")
            for archivo in archivos
        )

        if contiene_dicom:
            carpetas_dicom.append(raiz)

    carpetas_dicom.sort()
    return carpetas_dicom


def seleccionar_carpeta():
    carpetas = buscar_carpetas_dicom()

    if len(carpetas) == 0:
        raise ValueError(
            "No se encontraron carpetas con archivos DICOM."
        )

    print("\nSeries DICOM disponibles:")

    for i, carpeta in enumerate(carpetas, start=1):
        print(f"{i}. {carpeta}")

    opcion = validar_entero(
        "Seleccione una serie: ",
        1,
        len(carpetas)
    )

    return carpetas[opcion - 1]


# MENÚ

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


# PROGRAMA PRINCIPAL

while True:
    mostrar_menu()

    opcion = validar_entero(
        "\nSeleccione una opción: ",
        0,
        8
    )


    # SALIR

    if opcion == 0:
        print("\nPrograma finalizado.")
        break


    # CARGAR ESTUDIO

    elif opcion == 1:
        try:
            ruta = seleccionar_carpeta()
            estudio = SerieDICOM(ruta)

            nombre = os.path.relpath(
                ruta,
                "datos"
            ).replace(os.sep, " - ")

            gestor.agregar(nombre, estudio)

            estudio_activo = estudio
            nombre_estudio_activo = nombre

            print("\nEstudio cargado correctamente.")
            print("Estudio activo:", nombre)

        except Exception as error:
            print("\nError al cargar el estudio:", error)


    # MOSTRAR INFORMACIÓN

    elif opcion == 2:
        if estudio_activo is None:
            print("\nPrimero debe cargar un estudio.")
        else:
            print(estudio_activo)


    # CORREGIR ÁNGULO

    elif opcion == 3:
        if estudio_activo is None:
            print("\nPrimero debe cargar un estudio.")

        else:
            try:
                angulo = validar_float(
                    "Ingrese ángulo en grados: "
                )

                estudio_activo.corregirAngulo(angulo)

                print("\nCorrección aplicada correctamente.")
                print(
                    "Forma del volumen corregido:",
                    estudio_activo.imagen_corregida.shape
                )

            except Exception as error:
                print("\nError:", error)


    # ECUALIZAR CORTE

    elif opcion == 4:
        if estudio_activo is None:
            print("\nPrimero debe cargar un estudio.")

        else:
            try:
                maximo = estudio_activo.volumen.shape[0] - 1

                print(
                    f"\nCortes disponibles: 0 a {maximo}"
                )

                indice = validar_entero(
                    "Índice del corte: ",
                    0,
                    maximo
                )

                estudio_activo.ecualizarCorte(indice)

                print(
                    "\nEcualización realizada correctamente."
                )

            except Exception as error:
                print("\nError:", error)


    # SEGMENTAR REGIÓN

    elif opcion == 5:
        if estudio_activo is None:
            print("\nPrimero debe cargar un estudio.")

        else:
            try:
                plano = validar_plano()

                maximo_indice = obtener_maximo_indice(
                    estudio_activo,
                    plano
                )

                print(
                    f"\nÍndices disponibles para "
                    f"{plano}: 0 a {maximo_indice}"
                )

                indice = validar_entero(
                    "Índice del corte: ",
                    0,
                    maximo_indice
                )

                kernel = validar_entero(
                    "Tamaño del kernel: ",
                    1
                )

                iteraciones = validar_entero(
                    "Número de iteraciones: ",
                    1
                )

                respuesta = input(
                    "¿Desea usar umbral automático? "
                    "(s/n): "
                ).strip().lower()

                while respuesta not in ["s", "n"]:
                    print("Debe responder s o n.")

                    respuesta = input(
                        "¿Desea usar umbral automático? "
                        "(s/n): "
                    ).strip().lower()

                if respuesta == "s":
                    umbral = None
                else:
                    umbral = validar_float(
                        "Ingrese umbral (0-255): ",
                        0,
                        255
                    )

                estudio_activo.detectarRegionInteres(
                    plano=plano,
                    indice=indice,
                    tamano_kernel=kernel,
                    iteraciones=iteraciones,
                    umbral=umbral
                )

                print(
                    "\nSegmentación realizada correctamente."
                )

            except Exception as error:
                print("\nError:", error)


    # LISTAR ESTUDIOS

    elif opcion == 6:
        print(gestor)


    # ACTIVAR ESTUDIO

    elif opcion == 7:
        nombres = gestor.listar()

        if len(nombres) == 0:
            print("\nNo hay estudios almacenados.")

        else:
            print("\nEstudios disponibles:")

            for i, nombre in enumerate(
                nombres,
                start=1
            ):
                print(f"{i}. {nombre}")

            seleccion = validar_entero(
                "Seleccione estudio: ",
                1,
                len(nombres)
            )

            nombre = nombres[seleccion - 1]

            estudio_activo = gestor.buscar(nombre)
            nombre_estudio_activo = nombre

            print("\nEstudio activo:", nombre)


    # ELIMINAR ESTUDIO

    elif opcion == 8:
        nombres = gestor.listar()

        if len(nombres) == 0:
            print("\nNo hay estudios almacenados.")

        else:
            print("\nEstudios disponibles:")

            for i, nombre in enumerate(
                nombres,
                start=1
            ):
                print(f"{i}. {nombre}")

            seleccion = validar_entero(
                "Seleccione estudio a eliminar: ",
                1,
                len(nombres)
            )

            nombre = nombres[seleccion - 1]
            eliminado = gestor.eliminar(nombre)

            if eliminado:
                print("\nEstudio eliminado:", nombre)

                if nombre_estudio_activo == nombre:
                    estudio_activo = None
                    nombre_estudio_activo = None

            else:
                print(
                    "\nNo se pudo eliminar el estudio."
                )