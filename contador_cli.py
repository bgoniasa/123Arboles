"""
Contador de árboles y zonas verdes — versión de terminal (sin VS Code, sin
mapas interactivos). Escribes el nombre de un sitio y listo.

Uso:
    .venv\\Scripts\\python.exe contador_cli.py
    .venv\\Scripts\\python.exe contador_cli.py "Girona"
    .venv\\Scripts\\python.exe contador_cli.py "Parc de Collserola, Barcelona" --radio 300
"""

import argparse
import os
import sys

import cache_setup  # noqa: F401  (debe ir antes que samgeo/transformers/torch)
from geopy.geocoders import Nominatim
from samgeo.common import geotiff_to_jpg
from samgeo.text_sam import LangSAM

from compare_html import build_compare_html
from tiles_no_gdal import tms_to_geotiff


def geocodificar(sitio):
    geolocator = Nominatim(user_agent="contador-arboles-catalunya")
    ubicacion = geolocator.geocode(sitio)
    if ubicacion is None:
        sys.exit(f"No he encontrado '{sitio}'. Prueba con un nombre más concreto (municipio, barrio, dirección...).")
    return ubicacion.latitude, ubicacion.longitude, ubicacion.address


def bbox_desde_centro(lat, lon, radio_m):
    # Aproximación simple: grados por metro (válida para radios pequeños)
    dlat = radio_m / 111_320
    dlon = radio_m / (111_320 * abs(__import__("math").cos(__import__("math").radians(lat))))
    return [lon - dlon, lat - dlat, lon + dlon, lat + dlat]


def main():
    parser = argparse.ArgumentParser(description="Cuenta árboles/zonas verdes en un sitio de Catalunya o España.")
    parser.add_argument("sitio", nargs="?", help="Nombre del lugar a analizar (p. ej. 'Girona', 'Montjuïc, Barcelona')")
    parser.add_argument("--radio", type=int, default=250, help="Radio en metros alrededor del sitio (por defecto 250 m)")
    args = parser.parse_args()

    sitio = args.sitio or input("¿Qué sitio quieres analizar? (p. ej. 'Girona' o 'Montjuïc, Barcelona'): ").strip()

    print(f"Buscando '{sitio}'...")
    lat, lon, direccion = geocodificar(sitio)
    print(f"Encontrado: {direccion} ({lat:.5f}, {lon:.5f})")

    bbox = bbox_desde_centro(lat, lon, args.radio)

    image = "imagen.tif"
    print("Descargando imagen de satélite...")
    tms_to_geotiff(output=image, bbox=bbox, zoom=19, source="SATELLITE")

    print("Cargando modelo SAM2 + GroundingDINO (la primera vez tarda más)...")
    sam = LangSAM(model_type="sam2-hiera-large")

    print("Detectando árboles / zonas verdes...")
    sam.predict(image, "tree", box_threshold=0.24, text_threshold=0.24)

    preview = "preview.png"
    sam.show_anns(
        cmap="YlGn",
        add_boxes=False,
        alpha=0.65,
        title=f"Árboles y zonas verdes — {sitio}",
        blend=True,
        output=preview,
    )
    print(f"Vista previa guardada: {preview}")

    # Nº de árboles = nº de detecciones individuales del modelo (una caja
    # por árbol), no manchas de la máscara ya fusionada: así los árboles que
    # se tocan entre sí (copas juntas) se siguen contando por separado.
    n_arboles = len(sam.boxes)
    print(f"\n{'=' * 40}")
    print(f"Árboles / zonas verdes detectados en {sitio}: {n_arboles}")
    print(f"{'=' * 40}")

    original_png = "imagen_original.png"
    geotiff_to_jpg(image, original_png)

    overlay_slider = "overlay_slider.png"
    sam.show_anns(
        cmap="YlGn",
        add_boxes=False,
        alpha=0.65,
        blend=True,
        output=overlay_slider,
    )

    visor = "visor.html"
    build_compare_html(
        original_png=original_png,
        overlay_png=overlay_slider,
        out_html=visor,
        titulo=f"Árboles y zonas verdes — {sitio}",
        n_arboles=n_arboles,
    )
    print(f"Visor con desplazador guardado: {visor}")
    os.startfile(os.path.abspath(visor))


if __name__ == "__main__":
    main()
