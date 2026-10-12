# Contador de árboles y zonas verdes (Catalunya / España)

App sencilla para contar árboles/zonas verdes en imágenes de satélite.
No tiene un sitio fijo: funciona en cualquier punto de Catalunya o de España
(o de cualquier otro sitio, en realidad) — buscas o navegas hasta la zona que
quieras y dibujas ahí el área a analizar.

Basada en [segment-geospatial](https://github.com/opengeos/segment-geospatial)
(MIT License, ver `LICENSE_NOTICE.md`).

## Qué hace

- Mapa satélite+etiquetas interactivo con vista inicial de toda España; usa
  la lupa de la barra de herramientas para buscar cualquier lugar (Catalunya
  incluida) o navega libremente.
- Detecta árboles / vegetación arbórea de forma genérica (sin distinguir
  especie ni tipo).
- Cuenta el número de árboles / manchas de vegetación detectadas y lo
  muestra en una leyenda sobre el mapa.
- Compara la imagen original con la detección mediante un desplazador
  (slider).
- Aspecto en tonos verdes (paleta YlGn).

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> Nota: `groundingdino-py` compila una extensión nativa; en Windows puede
> requerir las "Build Tools for Visual Studio" (C++). Si falla la
> instalación, instálalas desde
> https://visualstudio.microsoft.com/visual-cpp-build-tools/ y reintenta.

La primera ejecución descarga los pesos del modelo SAM2 (varios cientos de
MB), así que puede tardar unos minutos.

## Uso

Abre `contador_arboles_catalunya.py` en VS Code (con la extensión Jupyter) y
ejecuta las celdas (`# %%`) una a una:

1. Busca (lupa) o navega hasta la zona que quieras analizar — cualquier
   punto de Catalunya, España o el resto del mundo — y dibuja un
   rectángulo/polígono sobre ella con las herramientas de dibujo. Es
   obligatorio: si no dibujas nada, la siguiente celda avisa y no continúa.
2. Ejecuta el resto de celdas para descargar la imagen, detectar la
   vegetación, ver el conteo y comparar con el desplazador.

El conteo final se imprime como:

```
Árboles / zonas verdes detectados: N
```

---

<sub>Creado por [Bernabé Hinojosa](https://www.linkedin.com/in/bernabehinojosa/) — experto en Inteligencia Artificial, hidráulica y GIS.</sub>
