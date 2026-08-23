"""
Genera una página HTML autocontenida (sin servidor, sin internet) con un
comparador de imágenes con desplazador (slider): a un lado la imagen de
satélite original, al otro la detección de árboles/zonas verdes. Se puede
abrir haciendo doble clic o automáticamente con el navegador por defecto.
"""

import base64
from pathlib import Path


def _to_data_uri(png_path):
    data = Path(png_path).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_compare_html(original_png, overlay_png, out_html, titulo, n_arboles):
    original_uri = _to_data_uri(original_png)
    overlay_uri = _to_data_uri(overlay_png)

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{titulo}</title>
<style>
  body {{
    margin: 0;
    font-family: system-ui, sans-serif;
    background: #10241a;
    color: #eaf6ee;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 12px 48px;
  }}
  h1 {{ font-size: 1.3rem; margin: 0 0 4px; text-align: center; }}
  .conteo {{
    font-size: 1.1rem;
    margin-bottom: 18px;
    background: #1f6b3a;
    padding: 6px 16px;
    border-radius: 999px;
  }}
  .comparador {{
    position: relative;
    max-width: 900px;
    width: 100%;
    aspect-ratio: 1 / 1;
    overflow: hidden;
    border-radius: 10px;
    box-shadow: 0 8px 30px rgba(0,0,0,.4);
    touch-action: none;
  }}
  .comparador img {{
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    user-select: none;
    pointer-events: none;
  }}
  .capa-overlay {{
    clip-path: inset(0 50% 0 0);
  }}
  .etiqueta {{
    position: absolute;
    top: 10px;
    padding: 4px 10px;
    background: rgba(0,0,0,.55);
    border-radius: 6px;
    font-size: .8rem;
    pointer-events: none;
  }}
  .etiqueta.izq {{ left: 10px; }}
  .etiqueta.der {{ right: 10px; }}
  input[type=range] {{
    width: 100%;
    max-width: 900px;
    margin-top: 16px;
  }}
  .linea {{
    position: absolute;
    top: 0; bottom: 0;
    left: 50%;
    width: 3px;
    background: #fff;
    box-shadow: 0 0 6px rgba(0,0,0,.6);
    pointer-events: none;
  }}
</style>
</head>
<body>
  <h1>{titulo}</h1>
  <div class="conteo">🌳 {n_arboles} árboles / zonas verdes detectados</div>
  <div class="comparador" id="comparador">
    <img src="{original_uri}" alt="Imagen original">
    <img src="{overlay_uri}" alt="Detección" class="capa-overlay" id="capaOverlay">
    <div class="linea" id="linea"></div>
    <div class="etiqueta izq">Original</div>
    <div class="etiqueta der">Detección</div>
  </div>
  <input type="range" min="0" max="100" value="50" id="desplazador">

<script>
  const rango = document.getElementById('desplazador');
  const capa = document.getElementById('capaOverlay');
  const linea = document.getElementById('linea');
  rango.addEventListener('input', () => {{
    const v = rango.value;
    capa.style.clipPath = `inset(0 ${{100 - v}}% 0 0)`;
    linea.style.left = v + '%';
  }});
</script>
</body>
</html>
"""
    Path(out_html).write_text(html, encoding="utf-8")
