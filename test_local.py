"""
Prueba local no interactiva: descarga una imagen de una zona fija de
Catalunya, detecta árboles/vegetación con SAM2 + prompt de texto, cuenta
las regiones detectadas y guarda una imagen de comprobación.

Uso: .venv\\Scripts\\python.exe test_local.py
"""

import cache_setup  # noqa: F401  (debe ir antes que samgeo/transformers/torch)
from samgeo.text_sam import LangSAM
from tiles_no_gdal import tms_to_geotiff

# Zona de prueba: Parc de la Ciutadella, Barcelona (parque con mucho arbolado)
bbox = [2.1855, 41.3860, 2.1920, 41.3910]

image = "imagen.tif"
print("Descargando imagen de satélite...")
tms_to_geotiff(output=image, bbox=bbox, zoom=19, source="SATELLITE")

print("Cargando modelo SAM2 + GroundingDINO (puede tardar, descarga pesos la primera vez)...")
sam = LangSAM(model_type="sam2-hiera-large")

print("Detectando árboles...")
sam.predict(image, "tree", box_threshold=0.24, text_threshold=0.24)

sam.show_anns(
    cmap="YlGn",
    add_boxes=False,
    alpha=0.65,
    title="Árboles y zonas verdes detectados",
    blend=True,
    output="preview.png",
)
print("Vista previa guardada: preview.png")

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
print(f"\nÁrboles / zonas verdes detectados: {n_arboles}")
