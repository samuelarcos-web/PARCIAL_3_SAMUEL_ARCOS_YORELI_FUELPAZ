from clases import SerieDICOM


serie = SerieDICOM(
    r"datos/T2"
)

print(serie)

print(
    "Forma del primer corte:",
    serie.matrices_pixeles[0].shape
)