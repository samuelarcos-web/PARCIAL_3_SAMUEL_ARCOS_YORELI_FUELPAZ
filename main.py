from clases import SerieDICOM


serie = SerieDICOM(
    r"datos/T2"
)

print(serie)


imagen, recorte, area = (
    serie.detectarRegionInteres(
        plano="transversal",
        indice=10,
        tamano_kernel=3,
        iteraciones=2,
        umbral=180,
        area_minima_pixeles=100,
        fraccion_maxima=0.15
    )
)


print(
    "\nÁrea detectada:",
    area,
    "mm²"
)