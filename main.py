from clases import SerieDICOM


serie = SerieDICOM(
    r"datos/T2"
)

print(serie)

print(
    "Forma del primer corte original:",
    serie.matrices_pixeles[0].shape
)

print(
    "Forma del primer corte escalado:",
    serie.cortes_escalados[0].shape
)

print(
    "Forma del volumen:",
    serie.volumen.shape
)