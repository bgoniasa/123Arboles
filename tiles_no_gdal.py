"""
Descarga teselas (tiles) de un mapa satélite para un bbox y las guarda como
GeoTIFF georreferenciado, sin depender de los bindings de Python de GDAL
(`osgeo`) — en Windows esos bindings no tienen wheel precompilado y exigen
compilar con Visual C++ Build Tools. En su lugar usamos `rasterio`, que ya
trae GDAL empaquetado dentro de su propio wheel.

Lógica de descarga/mosaico de teselas adaptada de `tms_to_geotiff()` en
segment-geospatial (https://github.com/opengeos/segment-geospatial),
licencia MIT — solo se ha sustituido el bloque final que escribía el
GeoTIFF con `osgeo.gdal` por uno equivalente con `rasterio`.
"""

import concurrent.futures
import io
import itertools
import math

import numpy as np
import rasterio
from PIL import Image
from rasterio.crs import CRS
from rasterio.transform import from_origin

try:
    import httpx

    _SESSION = httpx.Client()
except ImportError:
    import requests

    _SESSION = requests.Session()

_SESSION.headers.update(
    {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
    }
)

XYZ_TILES = {
    "OPENSTREETMAP": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "ROADMAP": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    "SATELLITE": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    "TERRAIN": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
    "HYBRID": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
}

_EARTH_RADIUS = 6378137.0


def _from4326_to3857(lat, lon):
    x = math.radians(lon) * _EARTH_RADIUS
    y = math.log(math.tan(math.radians(45 + lat / 2.0))) * _EARTH_RADIUS
    return x, y


def _deg2num(lat, lon, zoom):
    lat_r = math.radians(lat)
    n = 2**zoom
    xtile = (lon + 180) / 360 * n
    ytile = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * n
    return xtile, ytile


def _is_empty(im):
    extrema = im.getextrema()
    if len(extrema) >= 3:
        if len(extrema) > 3 and extrema[-1] == (0, 0):
            return True
        for ext in extrema[:3]:
            if ext != (0, 0):
                return False
        return True
    return extrema[0] == (0, 0)


def _paste_tile(bigim, base_size, tile, corner_xy, bbox):
    if tile is None:
        return bigim
    im = Image.open(io.BytesIO(tile))
    mode = "RGB" if im.mode == "RGB" else "RGBA"
    size = im.size
    if bigim is None:
        base_size[0], base_size[1] = size
        newim = Image.new(
            mode, (size[0] * (bbox[2] - bbox[0]), size[1] * (bbox[3] - bbox[1]))
        )
    else:
        newim = bigim
    dx = abs(corner_xy[0] - bbox[0])
    dy = abs(corner_xy[1] - bbox[1])
    xy0 = (size[0] * dx, size[1] * dy)
    if mode == "RGB":
        newim.paste(im, xy0)
    else:
        if im.mode != mode:
            im = im.convert(mode)
        if not _is_empty(im):
            newim.paste(im, xy0)
    im.close()
    return newim


def _finish_picture(bigim, base_size, bbox, x0, y0, x1, y1):
    xfrac = x0 - bbox[0]
    yfrac = y0 - bbox[1]
    x2 = round(base_size[0] * xfrac)
    y2 = round(base_size[1] * yfrac)
    imgw = round(base_size[0] * (x1 - x0))
    imgh = round(base_size[1] * (y1 - y0))
    retim = bigim.crop((x2, y2, x2 + imgw, y2 + imgh))
    if retim.mode == "RGBA" and retim.getextrema()[3] == (255, 255):
        retim = retim.convert("RGB")
    bigim.close()
    return retim


def _get_tile(url):
    retry = 3
    while True:
        try:
            r = _SESSION.get(url, timeout=60)
            break
        except Exception:
            retry -= 1
            if not retry:
                raise
    if r.status_code == 404 or not r.content:
        return None
    r.raise_for_status()
    return r.content


def tms_to_geotiff(output, bbox, zoom, source="SATELLITE", quiet=False):
    """Descarga teselas XYZ para `bbox` (EPSG:4326: [west, south, east, north])
    y las guarda como GeoTIFF en EPSG:3857, usando rasterio (sin GDAL/osgeo)."""
    if isinstance(source, str) and source.upper() in XYZ_TILES:
        source = XYZ_TILES[source.upper()]

    west, south, east, north = bbox
    x0, y0 = _deg2num(south, west, zoom)
    x1, y1 = _deg2num(north, east, zoom)
    x0, x1 = sorted([x0, x1])
    y0, y1 = sorted([y0, y1])
    corners = tuple(
        itertools.product(
            range(math.floor(x0), math.ceil(x1)),
            range(math.floor(y0), math.ceil(y1)),
        )
    )
    total = len(corners)
    bbox_tiles = (math.floor(x0), math.floor(y0), math.ceil(x1), math.ceil(y1))
    bigim = None
    base_size = [256, 256]
    with concurrent.futures.ThreadPoolExecutor(5) as executor:
        futures = [
            executor.submit(_get_tile, source.format(z=zoom, x=x, y=y))
            for x, y in corners
        ]
        for k, (fut, corner_xy) in enumerate(zip(futures, corners), 1):
            bigim = _paste_tile(bigim, base_size, fut.result(), corner_xy, bbox_tiles)
            if not quiet:
                print(f"Descargando tesela {k}/{total}")

    img = _finish_picture(bigim, base_size, bbox_tiles, x0, y0, x1, y1)
    arr = np.array(img)
    if arr.ndim == 2:
        arr = arr[:, :, None]
    arr = np.moveaxis(arr, -1, 0)  # (H, W, bands) -> (bands, H, W)

    xp0, yp0 = _from4326_to3857(south, west)
    xp1, yp1 = _from4326_to3857(north, east)
    transform = from_origin(
        min(xp0, xp1),
        max(yp0, yp1),
        abs(xp1 - xp0) / img.size[0],
        abs(yp1 - yp0) / img.size[1],
    )

    with rasterio.open(
        output,
        "w",
        driver="GTiff",
        height=arr.shape[1],
        width=arr.shape[2],
        count=arr.shape[0],
        dtype=arr.dtype,
        crs=CRS.from_epsg(3857),
        transform=transform,
        compress="deflate",
    ) as dst:
        dst.write(arr)

    if not quiet:
        print(f"Imagen guardada: {output}")
