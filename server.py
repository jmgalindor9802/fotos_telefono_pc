"""
The Elite Flower — Servidor Flask para recepción de imágenes.
Encapsula toda la lógica HTTP en la clase ImageServer.
"""

import logging
import os
import threading
import queue
import time
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

from config import APP_CONFIG

logger = logging.getLogger("server")


class ImageServer:
    """Servidor Flask que recibe imágenes vía POST y notifica al manager."""

    def __init__(self, photo_queue: queue.Queue):
        self._queue = photo_queue
        self._cfg = APP_CONFIG
        self._thread: Optional[threading.Thread] = None
        self._start_time: float = 0.0
        self._received_count: int = 0

        self._app = Flask(__name__)
        self._app.config["MAX_CONTENT_LENGTH"] = self._cfg["max_upload_mb"] * 1024 * 1024
        self._register_routes()
        self._register_error_handlers()

    # ───────── Rutas Flask ─────────
    def _register_routes(self):
        @self._app.route("/upload", methods=["POST"])
        def upload_image():
            if "image" not in request.files:
                logger.warning("Petición sin campo 'image'")
                return jsonify({"error": "No se encontró el campo 'image' en la petición."}), 400

            file = request.files["image"]
            if file.filename == "":
                return jsonify({"error": "No se seleccionó ningún archivo."}), 400

            if not self._allowed_file(file.filename):
                exts = ", ".join(sorted(self._cfg["allowed_extensions"]))
                logger.warning("Extensión rechazada: %s", file.filename)
                return jsonify({"error": f"Extensión no permitida. Usa: {exts}"}), 400

            upload_folder = self._cfg["upload_folder"]
            os.makedirs(upload_folder, exist_ok=True)

            extension = secure_filename(file.filename).rsplit(".", 1)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            unique_filename = f"foto_{timestamp}.{extension}"

            filepath = os.path.join(upload_folder, unique_filename)
            file.save(filepath)

            file_size_kb = round(os.path.getsize(filepath) / 1024, 1)
            self._received_count += 1

            logger.info("📸 Foto recibida: %s (%.1f KB)", unique_filename, file_size_kb)

            # Notificar al manager vía cola
            self._queue.put(filepath)

            return jsonify({
                "message": "Imagen subida exitosamente.",
                "filename": unique_filename,
                "file_size_kb": file_size_kb,
                "total_received": self._received_count,
            }), 200

        @self._app.route("/", methods=["GET"])
        def index():
            return jsonify({
                "status": "ok",
                "message": "Servidor de recepción de fotos activo. Envía imágenes a POST /upload.",
            }), 200

        @self._app.route("/health", methods=["GET"])
        def health():
            upload_folder = self._cfg["upload_folder"]
            photo_count = 0
            if os.path.isdir(upload_folder):
                photo_count = len([
                    f for f in os.listdir(upload_folder)
                    if os.path.isfile(os.path.join(upload_folder, f))
                ])
            uptime_secs = round(time.time() - self._start_time) if self._start_time else 0
            return jsonify({
                "status": "ok",
                "uptime_seconds": uptime_secs,
                "photos_in_folder": photo_count,
                "photos_received_session": self._received_count,
                "upload_folder": upload_folder,
                "max_upload_mb": self._cfg["max_upload_mb"],
                "port": self._cfg["port"],
            }), 200

    # ───────── Error handlers ─────────
    def _register_error_handlers(self):
        @self._app.errorhandler(413)
        def file_too_large(e):
            max_mb = self._cfg["max_upload_mb"]
            logger.warning("Archivo rechazado: excede el límite de %d MB", max_mb)
            return jsonify({
                "error": f"El archivo excede el límite de {max_mb} MB.",
            }), 413

    # ───────── Helpers ─────────
    def _allowed_file(self, filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in self._cfg["allowed_extensions"]

    # ───────── Ciclo de vida ─────────
    def start(self):
        """Inicia el servidor Flask en un hilo daemon."""
        self._start_time = time.time()

        self._thread = threading.Thread(
            target=self._app.run,
            kwargs={
                "host": self._cfg["host"],
                "port": self._cfg["port"],
                "debug": False,
                "use_reloader": False,
            },
            daemon=True,
        )
        self._thread.start()
        logger.info("Servidor Flask iniciado en puerto %d", self._cfg["port"])
