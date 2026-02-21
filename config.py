"""
The Elite Flower — Configuración centralizada.
Tema visual, constantes de la app, logging y utilidades compartidas.
"""

import json
import logging
import os
import socket
import sys

# ──────────────────────────────────────────────
# Rutas base (compatible con PyInstaller)
# ──────────────────────────────────────────────
# Directorio donde vive el .exe real (o el script en dev)
if getattr(sys, "frozen", False):
    # PyInstaller --onefile extrae a _MEIPASS, pero el .exe está en sys.executable
    _EXE_DIR = os.path.dirname(sys.executable)
    _BUNDLE_DIR = getattr(sys, "_MEIPASS", _EXE_DIR)
else:
    _EXE_DIR = os.path.dirname(os.path.abspath(__file__))
    _BUNDLE_DIR = _EXE_DIR

# settings.json se guarda junto al .exe (persistente), no en el directorio temporal
SETTINGS_FILE = os.path.join(_EXE_DIR, "settings.json")

# ──────────────────────────────────────────────
# Logging centralizado
# ──────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s │ %(levelname)-7s │ %(name)-12s │ %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
)

# Silenciar logs excesivos de werkzeug
logging.getLogger("werkzeug").setLevel(logging.ERROR)

logger = logging.getLogger("config")

# ──────────────────────────────────────────────
# Configuración de la aplicación
# ──────────────────────────────────────────────
APP_CONFIG = {
    "port": 5000,
    "host": "0.0.0.0",
    "upload_folder": os.path.join(_EXE_DIR, "fotos_recibidas"),
    "allowed_extensions": {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic", "heif"},
    "max_upload_mb": 16,
    "thumbnail_size": (90, 90),
    "max_thumbnails": 30,
    "poll_interval_ms": 250,
    "led_duration_ms": 3000,
    "status_duration_ms": 4000,
}


# ──────────────────────────────────────────────
# Persistencia de configuración (settings.json)
# ──────────────────────────────────────────────
def load_settings():
    """Carga la configuración guardada desde settings.json."""
    if not os.path.isfile(SETTINGS_FILE):
        return
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "upload_folder" in data and os.path.isdir(data["upload_folder"]):
            APP_CONFIG["upload_folder"] = data["upload_folder"]
            logger.info("Carpeta restaurada: %s", data["upload_folder"])
    except Exception:
        logger.warning("settings.json corrupto — usando valores por defecto")


def save_settings():
    """Guarda la configuración actual en settings.json."""
    data = {
        "upload_folder": APP_CONFIG["upload_folder"],
    }
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning("No se pudo guardar settings.json: %s", e)


# Cargar settings al importar el módulo
load_settings()

# ──────────────────────────────────────────────
# Tema visual — Identidad "The Elite Flower"
# ──────────────────────────────────────────────
THEME = {
    # Fondos
    "bg_dark": "#0f172a",
    "panel_bg": "#1e293b",
    "viewer_bg": "#0c1524",
    "ip_frame_bg": "#2d3d2d",
    "thumb_bg_rgb": (15, 23, 42),

    # Acento y LED
    "accent": "#7da07d",
    "accent_hover": "#5c7a5c",
    "led_glow": "#3d5a3d",
    "led_off": "#3b4a3b",

    # Texto
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",

    # Bordes
    "border_color": "#334155",

    # Radios
    "radius_frame": 15,
    "radius_viewer": 20,
    "radius_button": 15,
    "radius_thumbnail": 10,

    # Tipografía
    "font_family": "Segoe UI",
}


# ──────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────
def get_local_ip() -> str:
    """Obtiene la IP local de la máquina en la red Wi-Fi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def is_port_available(port: int) -> bool:
    """Verifica si un puerto TCP está disponible."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", port))
        return True
    except OSError:
        return False


def find_available_port(start_port: int = 5000, max_tries: int = 10) -> int:
    """Busca un puerto libre empezando desde start_port.
    Si el puerto preferido está ocupado, prueba los siguientes."""
    for offset in range(max_tries):
        port = start_port + offset
        if is_port_available(port):
            return port
    return start_port  # fallback


def get_icon_path() -> str | None:
    """Devuelve la ruta al icono .ico si existe."""
    # Buscar en el directorio del bundle (PyInstaller) y en el directorio del exe
    for base in (_BUNDLE_DIR, _EXE_DIR):
        path = os.path.join(base, "elite_flower.ico")
        if os.path.isfile(path):
            return path
    return None
