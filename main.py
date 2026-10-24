from clases import (
    SerieDICOM,
    GestorDICOM
)


gestor = GestorDICOM()


serie = SerieDICOM(
    r"datos/T2"
)


gestor.agregar(
    "T2",
    serie
)


print(gestor)

print(
    "\nEstudios almacenados:",
    gestor.listar()
)


estudio_encontrado = gestor.buscar(
    "T2"
)


if estudio_encontrado is not None:

    print(
        "\nPaciente encontrado:",
        estudio_encontrado.nombre_paciente
    )