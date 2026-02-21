"""
The Elite Flower — Manager (Controller).
Orquesta la comunicación entre el servidor Flask y la GUI.
Incluye sistema de plugins para procesamiento de imágenes.
"""

import logging
import os
import queue
from typing import Callable, List

from config import APP_CONFIG, get_local_ip, save_settings, find_available_port
from server import ImageServer

logger = logging.getLogger("manager")


class AppManager:
    """Controlador principal: conecta ImageServer ↔ AppInterface."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._server = ImageServer(self._queue)
        self._gui = None  # se asigna en run()
        self._processors: List[Callable[[str], str]] = []

    # ───────── Sistema de plugins ─────────
    def register_processor(self, fn: Callable[[str], str]):
        """
        Registra una función que procesa cada foto antes de mostrarla.

        La función recibe la ruta del archivo y debe devolver una ruta
        (puede ser la misma o una nueva si genera un archivo procesado).

        Ejemplo de uso:
            def watermark(filepath: str) -> str:
                # ... agregar marca de agua ...
                return filepath

            manager.register_processor(watermark)
        """
        self._processors.append(fn)
        logger.info("Procesador registrado: %s", fn.__name__)

    def _apply_processors(self, filepath: str) -> str:
        """Ejecuta todos los procesadores registrados en orden."""
        for fn in self._processors:
            try:
                filepath = fn(filepath)
            except Exception as e:
                logger.warning("Processor %s falló: %s", fn.__name__, e)
        return filepath

    # ───────── Cambio de carpeta ─────────
    def update_storage_path(self, new_path: str):
        """
        Actualiza la carpeta de guardado en tiempo real.
        Crea el directorio si no existe y persiste en settings.json.
        """
        os.makedirs(new_path, exist_ok=True)
        APP_CONFIG["upload_folder"] = new_path
        save_settings()
        logger.info("Carpeta actualizada: %s", new_path)

        if self._gui is not None:
            self._gui.on_storage_path_changed(new_path)

    # ───────── Polling de la cola ─────────
    def _poll_queue(self):
        """Revisa la cola y despacha fotos nuevas a la GUI."""
        try:
            while True:
                filepath = self._queue.get_nowait()
                filepath = self._apply_processors(filepath)
                if self._gui is not None:
                    self._gui.display_image(filepath)
        except queue.Empty:
            pass

        if self._gui is not None:
            self._gui.after(APP_CONFIG["poll_interval_ms"], self._poll_queue)

    # ───────── Ciclo de vida ─────────
    def run(self):
        """Inicia el servidor y la GUI (bloquea hasta cerrar ventana)."""
        # Import aquí para evitar dependencia circular
        from ui import AppInterface

        ip = get_local_ip()

        # Auto-seleccionar puerto libre
        preferred_port = APP_CONFIG["port"]
        actual_port = find_available_port(preferred_port)
        APP_CONFIG["port"] = actual_port

        if actual_port != preferred_port:
            logger.info("Puerto %d ocupado, usando %d", preferred_port, actual_port)

        logger.info("=" * 50)
        logger.info("THE ELITE FLOWER — Receptor de Fotos")
        logger.info("=" * 50)
        logger.info("IP local: %s", ip)
        logger.info("Puerto:   %d", actual_port)
        logger.info("Carpeta:  %s", APP_CONFIG["upload_folder"])
        logger.info("Upload máx: %d MB", APP_CONFIG["max_upload_mb"])
        logger.info("Procesadores: %d", len(self._processors))
        logger.info("=" * 50)

        # Iniciar servidor Flask
        self._server.start()

        # Crear GUI, pasando referencia al manager
        self._gui = AppInterface(local_ip=ip, manager=self)

        # Iniciar polling
        self._gui.after(APP_CONFIG["poll_interval_ms"], self._poll_queue)

        # Mainloop (bloquea)
        self._gui.mainloop()

