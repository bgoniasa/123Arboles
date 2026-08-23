# %% [markdown]
# # Contador de árboles y zonas verdes (Catalunya / España)
#
# Adaptado a partir de [segment-geospatial](https://github.com/opengeos/segment-geospatial)
# (licencia MIT, ver `LICENSE_NOTICE.md`).
#
# Este script detecta y **cuenta** masas de vegetación (árboles / zonas verdes)
# en imágenes de satélite mediante SAM2 con un prompt de texto genérico.
# No clasifica especies ni tipos de árbol: solo detecta presencia de vegetación
# arbórea y la cuenta. Funciona en **cualquier punto de Catalunya o España**:
# el mapa arranca con una vista general y tú eliges la zona buscándola o
# navegando y dibujándola sobre el mapa, no hay ningún sitio fijo "de
# fábrica".
#
# Uso en VS Code: abre este archivo y ejecútalo celda a celda con la extensión
# Jupyter (cada bloque `# %%` es una celda).

# %%
import cache_setup  # noqa: F401  (debe ir antes que samgeo/transformers/torch)
import leafmap
from samgeo.text_sam import LangSAM
from tiles_no_gdal import tms_to_geotiff

# %% [markdown]
# ## Mapa interactivo — cualquier punto de Catalunya o España
#
# Vista inicial: toda España, para que puedas ir a cualquier sitio. Usa la
# lupa 🔍 de la barra de herramientas para buscar un municipio, barrio o
# dirección (p. ej. "Girona", "Collserola", "Ronda de Dalt"), o simplemente
# navega con el ratón. Cuando tengas la zona a analizar en pantalla, usa las
# herramientas de dibujo (⬛/▲) para marcar un rectángulo o polígono sobre
# ella antes de ejecutar la siguiente celda.

# %%
m = leafmap.Map(center=[40.0, -3.0], zoom=6, height="800px")
m.add_basemap("HYBRID")  # satélite + nombres de lugares, para orientarte
m

# %% [markdown]
# ## Descargar la imagen de satélite de la zona seleccionada
#
# Si no has dibujado ninguna zona sobre el mapa, esta celda avisa en vez de
# usar un sitio por defecto: así el cuaderno funciona igual en cualquier
# punto de Catalunya o España, no solo en un lugar fijo.

# %%
bbox = m.user_roi_bounds()
assert bbox is not None, (
    "No has dibujado ninguna zona en el mapa. Sube a la celda anterior, "
    "navega/busca el sitio que quieras (Catalunya, España o donde sea) y "
    "dibuja un rectángulo o polígono con las herramientas de dibujo antes "
    "de volver a ejecutar esta celda."
)

image = "imagen.tif"
tms_to_geotiff(output=image, bbox=bbox, zoom=19, source="SATELLITE")

# %%
m.layers[-1].visible = False
m.add_raster(image, layer_name="Imagen")
m

# %% [markdown]
# ## Detectar árboles / zonas verdes
#
# Se usa un único prompt de texto genérico ("tree"): no se distingue especie
# ni tipo, solo se detecta y delimita vegetación arbórea.

# %%
sam = LangSAM(model_type="sam2-hiera-large")

# %%
text_prompt = "tree"
sam.predict(image, text_prompt, box_threshold=0.24, text_threshold=0.24)

# %% [markdown]
# ## Visualizar el resultado (aspecto en tonos verdes)

# %%
sam.show_anns(
    cmap="YlGn",
    add_boxes=False,
    alpha=0.65,
    title="Árboles y zonas verdes detectados",
    blend=True,
)

# %% [markdown]
# ## Vectorizar y contar árboles / zonas verdes
#
# `region_groups` agrupa la máscara en regiones individuales. Cada región es
# un árbol o una mancha de vegetación contigua: `len(gdf)` es el conteo total.

# %%
out_mask = "arboles_mascara.tif"
sam.show_anns(cmap="Greys_r", add_boxes=False, alpha=1, blend=False, output=out_mask)

array, gdf = sam.region_groups(
    image=out_mask,
    min_size=30,
    out_csv="arboles.csv",
    out_image="arboles_regiones.tif",
    out_vector="arboles.gpkg",
)

n_arboles = len(gdf)
print(f"Árboles / zonas verdes detectados: {n_arboles}")

# %% [markdown]
# ## Comparar imagen original vs. detección con un desplazador (slider)

# %%
m2 = leafmap.Map()
m2.add_raster(image, layer_name="Imagen original")
m2.split_map(
    "arboles_regiones.tif",
    image,
    left_label="Árboles / zonas verdes",
    right_label="Imagen original",
    left_args={"palette": "YlGn", "nodata": 0, "opacity": 0.85},
)
m2

# %% [markdown]
# ## Mapa final con el conteo total

# %%
m3 = leafmap.Map()
m3.add_raster(image, layer_name="Imagen")
m3.add_raster(
    "arboles_regiones.tif",
    palette="YlGn",
    opacity=0.6,
    nodata=0,
    layer_name="Árboles / zonas verdes",
)
style = {"color": "#1b5e20", "weight": 1.5, "fillColor": "#66bb6a", "fillOpacity": 0.45}
m3.add_vector("arboles.gpkg", layer_name="Contorno", style=style)
m3.add_legend(
    title="Leyenda",
    legend_dict={f"Árbol / zona verde ({n_arboles} detectados)": "#66bb6a"},
)
m3.add_layer_manager()
print(f"Total detectado: {n_arboles} árboles / zonas verdes")
m3
