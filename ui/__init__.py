"""
The Elite Flower — Ventana principal de la aplicación.
Compone Sidebar + ImageViewer + HistoryBar.
"""

import logging
import os
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk
from PIL import Image, ImageTk

from config import APP_CONFIG, THEME, get_local_ip, get_icon_path
from ui.sidebar import Sidebar
from ui.viewer import ImageViewer, HistoryBar

if TYPE_CHECKING:
    from manager import AppManager

logger = logging.getLogger("ui")


class AppInterface(ctk.CTk):
    """Ventana principal que ensambla todos los widgets."""

    def __init__(self, local_ip: str | None = None,
                 manager: "AppManager | None" = None):
        super().__init__()

        self._local_ip = local_ip or get_local_ip()
        self._manager = manager

        # ── Configuración de ventana ──
        self.title("🌿  The Elite Flower — Receptor de Fotos")
        self.geometry("1100x700")
        self.minsize(900, 550)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.configure(fg_color=THEME["bg_dark"])

        # ── Icono de ventana ──
        icon_path = get_icon_path()
        if icon_path:
            try:
                self.iconbitmap(icon_path)
                logger.info("Icono cargado: %s", icon_path)
            except Exception:
                logger.warning("No se pudo cargar el icono")

        # ── Confirmación al cerrar ──
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Grid principal: sidebar | main
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Componentes ──
        self._sidebar = Sidebar(
            self,
            local_ip=self._local_ip,
            on_select_folder=self._handle_folder_selected,
        )
        self._sidebar.grid(row=0, column=0, sticky="nswe")

        main = ctk.CTkFrame(self, fg_color=THEME["bg_dark"], corner_radius=0)
        main.grid(row=0, column=1, sticky="nswe", padx=(2, 0))
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self._viewer = ImageViewer(main, local_ip=self._local_ip)
        self._viewer.grid(row=0, column=0, sticky="nswe", padx=16, pady=(16, 8))

        self._history = HistoryBar(main, on_thumbnail_click=self._viewer.show_image)
        self._history.grid(row=1, column=0, sticky="we", padx=16, pady=(4, 16))

        # ── Cargar fotos existentes ──
        self._load_existing_photos()

    # ───────── API pública (llamada por AppManager) ─────────
    def display_image(self, filepath: str):
        """Muestra una nueva foto: visor + thumbnail + LED."""
        success = self._viewer.show_image(filepath)
        self._history.add_thumbnail(filepath)
        self._sidebar.flash_led()

        if success:
            self._sidebar.set_status(os.path.basename(filepath))
        else:
            self._sidebar.set_status("⚠ Foto corrupta", is_error=True)
            logger.warning("Imagen corrupta recibida: %s", filepath)

        self._sidebar.update_photo_count()

    def on_storage_path_changed(self, new_path: str):
        """Llamado por el manager cuando cambia la carpeta de destino."""
        self._sidebar.update_path_label(new_path)
        self._sidebar.update_photo_count()

    # ───────── Internos ─────────
    def _handle_folder_selected(self, new_path: str):
        """Callback del sidebar cuando el usuario elige una carpeta."""
        if self._manager is not None:
            self._manager.update_storage_path(new_path)

    def _on_close(self):
        """Confirmación antes de cerrar la aplicación."""
        if messagebox.askyesno(
            "Cerrar aplicación",
            "¿Estás seguro de que deseas cerrar el receptor de fotos?",
            icon="question",
        ):
            logger.info("Aplicación cerrada por el usuario")
            self.destroy()

    # ───────── Carga inicial ─────────
    def _load_existing_photos(self):
        """Carga fotos que ya existan en la carpeta al iniciar."""
        upload_folder = APP_CONFIG["upload_folder"]
        if not os.path.isdir(upload_folder):
            self._sidebar.update_photo_count()
            return

        allowed = APP_CONFIG["allowed_extensions"]
        files = sorted(
            [
                os.path.join(upload_folder, f)
                for f in os.listdir(upload_folder)
                if os.path.isfile(os.path.join(upload_folder, f))
                and "." in f
                and f.rsplit(".", 1)[1].lower() in allowed
            ],
            key=os.path.getmtime,
        )

        max_thumbs = APP_CONFIG["max_thumbnails"]
        for fp in files[-max_thumbs:]:
            self._history.add_thumbnail(fp)

        # Mostrar la última foto en el visor
        if files:
            self._viewer.show_image(files[-1])

        self._sidebar.update_photo_count()
        logger.info("Cargadas %d fotos existentes del historial", len(files))
