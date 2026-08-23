"""
Redirige las cachés de descarga de modelos (Hugging Face, PyTorch) a la
unidad A: en vez del perfil de usuario en C:. Los pesos de SAM2 +
GroundingDINO + BERT ocupan varios GB, y C: puede tener muy poco espacio
libre.

Debe importarse ANTES que `torch`, `transformers`, `huggingface_hub` o
`samgeo`, porque esas librerías leen estas variables de entorno en el
momento de importarse.
"""

import os
from pathlib import Path

_CACHE_DIR = Path(__file__).parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)

os.environ.setdefault("HF_HOME", str(_CACHE_DIR / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(_CACHE_DIR / "huggingface" / "hub"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(_CACHE_DIR / "huggingface" / "hub"))
os.environ.setdefault("TORCH_HOME", str(_CACHE_DIR / "torch"))

# Backend de matplotlib sin interfaz gráfica: evita errores al generar
# imágenes desde un servidor (webapp.py) o desde hilos que no son el
# principal.
import matplotlib  # noqa: E402

matplotlib.use("Agg")
