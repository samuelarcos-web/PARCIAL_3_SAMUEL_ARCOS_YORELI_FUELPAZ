from clases import SerieDICOM


serie = SerieDICOM(
    r"datos/T2"
)

print(serie)

volumen_corregido = serie.corregirAngulo(
    15
)

print(
    "Forma del volumen corregido:",
    volumen_corregido.shape
)