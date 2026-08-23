"""
Visor web local: mapa interactivo (como el notebook original) donde puedes
navegar a cualquier sitio, dibujar un rectángulo y contar árboles / zonas
verdes ahí. Sin VS Code, sin Jupyter: se abre solo en el navegador.

Uso:
    .venv\\Scripts\\python.exe webapp.py
"""

import base64
import threading
import webbrowser
from pathlib import Path

import cache_setup  # noqa: F401  (debe ir antes que samgeo/transformers/torch)
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from samgeo.common import geotiff_to_jpg
from samgeo.text_sam import LangSAM

from tiles_no_gdal import tms_to_geotiff

app = FastAPI()
_sam = None


class BBox(BaseModel):
    west: float
    south: float
    east: float
    north: float


def _modelo():
    global _sam
    if _sam is None:
        print("Cargando modelo SAM2 + GroundingDINO (solo la primera vez tarda más)...")
        _sam = LangSAM(model_type="sam2-hiera-large")
    return _sam


def _b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


@app.get("/", response_class=HTMLResponse)
def index():
    return Path(__file__).parent.joinpath("static_index.html").read_text(encoding="utf-8")


@app.post("/analizar")
def analizar(bbox: BBox):
    ancho_m = abs(bbox.east - bbox.west) * 111_320
    if ancho_m > 3000:
        raise HTTPException(400, "El rectángulo es demasiado grande (máx. ~3 km de lado). Dibuja una zona más pequeña.")

    image = "imagen.tif"
    print(f"Descargando imagen para bbox {bbox}...")
    tms_to_geotiff(
        output=image,
        bbox=[bbox.west, bbox.south, bbox.east, bbox.north],
        zoom=19,
        source="SATELLITE",
        quiet=True,
    )

    sam = _modelo()
    print("Detectando árboles / zonas verdes...")
    sam.predict(image, "tree", box_threshold=0.24, text_threshold=0.24)
    n_arboles = len(sam.boxes)

    overlay_path = "overlay_slider.png"
    sam.show_anns(cmap="YlGn", add_boxes=False, alpha=0.65, blend=True, output=overlay_path)

    original_path = "imagen_original.png"
    geotiff_to_jpg(image, original_path)

    print(f"Detectados: {n_arboles}")
    return {
        "n_arboles": n_arboles,
        "original": _b64(original_path),
        "overlay": _b64(overlay_path),
    }


if __name__ == "__main__":
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
