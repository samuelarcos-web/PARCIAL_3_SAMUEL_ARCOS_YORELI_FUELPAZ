from clases import SerieDICOM


serie = SerieDICOM(
    r"datos/T2"
)

print(serie)

corte_ecualizado = serie.ecualizarCorte(
    10
)

print(
    "Tipo de dato del corte ecualizado:",
    corte_ecualizado.dtype
)

print(
    "Forma del corte ecualizado:",
    corte_ecualizado.shape
)

print(
    "Valor mínimo:",
    corte_ecualizado.min()
)

print(
    "Valor máximo:",
    corte_ecualizado.max()
)