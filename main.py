from clases import SerieDICOM

import matplotlib.pyplot as plt


serie = SerieDICOM(
    r"datos/T2"
)

print(serie)


original, binaria, apertura, aspect = serie.segmentarCorte(
    plano="transversal",
    indice=10,
    tamano_kernel=3,
    iteraciones=2,
    umbral=180
)


plt.figure(
    figsize=(15, 5)
)


plt.subplot(
    1,
    3,
    1
)

plt.imshow(
    original,
    cmap="gray",
    aspect=aspect
)

plt.title(
    "Corte normalizado"
)

plt.axis(
    "off"
)


plt.subplot(
    1,
    3,
    2
)

plt.imshow(
    binaria,
    cmap="gray",
    aspect=aspect
)

plt.title(
    "Imagen binarizada"
)

plt.axis(
    "off"
)


plt.subplot(
    1,
    3,
    3
)

plt.imshow(
    apertura,
    cmap="gray",
    aspect=aspect
)

plt.title(
    "Apertura morfológica"
)

plt.axis(
    "off"
)

print(
    "Umbral utilizado:",
    serie.ultimo_umbral
)


plt.tight_layout()

plt.show()