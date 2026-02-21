"""
The Elite Flower — Panel lateral (Sidebar).
Muestra IP, puerto, LED de estado, contador y botón de carpeta.
"""

import os
import sys
import subprocess
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk

from config import APP_CONFIG, THEME


class Sidebar(ctk.CTkFrame):
    """Panel lateral izquierdo con información de conexión y controles."""

    def __init__(self, master, local_ip: str,
                 on_select_folder: Optional[Callable[[str], None]] = None,
                 **kwargs):
        super().__init__(
            master,
            width=270,
            corner_radius=0,
            fg_color=THEME["panel_bg"],
            border_width=1,
            border_color=THEME["border_color"],
            **kwargs,
        )
        self.grid_propagate(False)

        self._local_ip = local_ip
        self._on_select_folder = on_select_folder
        self._led_after_id: str | None = None
        self._font = THEME["font_family"]
        self._accent = THEME["accent"]

        self._build()

    def _build(self):
        port = APP_CONFIG["port"]

        # ── Título ──
        ctk.CTkLabel(
            self, text="🌿 The Elite Flower",
            font=ctk.CTkFont(family=self._font, size=21, weight="bold"),
            text_color=self._accent,
        ).pack(pady=(28, 4))

        ctk.CTkLabel(
            self, text="Receptor de Fotos",
            font=ctk.CTkFont(family=self._font, size=13),
            text_color=THEME["text_secondary"],
        ).pack(pady=(0, 24))

        # ── Separador ──
        ctk.CTkFrame(self, height=1, fg_color=THEME["border_color"]).pack(fill="x", padx=20, pady=4)

        # ── Sección conexión ──
        ctk.CTkLabel(
            self, text="CONEXIÓN",
            font=ctk.CTkFont(family=self._font, size=11, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(pady=(16, 8))

        ip_frame = ctk.CTkFrame(self, fg_color=THEME["ip_frame_bg"], corner_radius=THEME["radius_frame"])
        ip_frame.pack(padx=20, fill="x")

        for label_text, value_text in [("Dirección IP", self._local_ip), ("Puerto", str(port))]:
            ctk.CTkLabel(
                ip_frame, text=label_text,
                font=ctk.CTkFont(family=self._font, size=11),
                text_color=THEME["text_secondary"],
            ).pack(pady=(12, 0) if label_text == "Dirección IP" else (6, 0))

            ctk.CTkLabel(
                ip_frame, text=value_text,
                font=ctk.CTkFont(family=self._font, size=18, weight="bold"),
                text_color=self._accent,
            ).pack(pady=(0, 0) if label_text == "Dirección IP" else (0, 12))

        # URL completa
        ctk.CTkLabel(
            self,
            text=f"http://{self._local_ip}:{port}/upload",
            font=ctk.CTkFont(family=self._font, size=11),
            text_color=THEME["text_secondary"],
            wraplength=230,
        ).pack(pady=(8, 4))

        # ── Separador ──
        ctk.CTkFrame(self, height=1, fg_color=THEME["border_color"]).pack(fill="x", padx=20, pady=12)

        # ── Ruta de carpeta actual ──
        ctk.CTkLabel(
            self, text="CARPETA DESTINO",
            font=ctk.CTkFont(family=self._font, size=11, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(pady=(4, 4))

        self._path_label = ctk.CTkLabel(
            self,
            text=self._truncate_path(APP_CONFIG["upload_folder"]),
            font=ctk.CTkFont(family=self._font, size=9),
            text_color=THEME["text_secondary"],
            wraplength=230,
        )
        self._path_label.pack(pady=(0, 8))

        # ── Separador ──
        ctk.CTkFrame(self, height=1, fg_color=THEME["border_color"]).pack(fill="x", padx=20, pady=4)

        # ── LED de estado ──
        ctk.CTkLabel(
            self, text="ESTADO",
            font=ctk.CTkFont(family=self._font, size=11, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(pady=(4, 8))

        self._led_canvas = ctk.CTkCanvas(self, width=28, height=28,
                                          bg=THEME["panel_bg"], highlightthickness=0)
        self._led_canvas.pack()
        self._draw_led(THEME["led_off"])

        self._status_label = ctk.CTkLabel(
            self, text="Esperando fotos…",
            font=ctk.CTkFont(family=self._font, size=12),
            text_color=THEME["text_secondary"],
        )
        self._status_label.pack(pady=(6, 4))

        self._count_label = ctk.CTkLabel(
            self, text="0 fotos recibidas",
            font=ctk.CTkFont(family=self._font, size=11),
            text_color=THEME["text_secondary"],
        )
        self._count_label.pack(pady=(0, 16))

        # ── Botones inferiores (apilados desde abajo) ──
        ctk.CTkButton(
            self, text="📂  Abrir Carpeta",
            font=ctk.CTkFont(family=self._font, size=13, weight="bold"),
            command=self._open_folder,
            fg_color=self._accent,
            hover_color=THEME["accent_hover"],
            text_color=THEME["text_primary"],
            corner_radius=THEME["radius_button"],
            height=42,
        ).pack(padx=20, fill="x", pady=(8, 8), side="bottom")

        ctk.CTkButton(
            self, text="📁  Seleccionar Destino",
            font=ctk.CTkFont(family=self._font, size=12, weight="bold"),
            command=self._select_folder,
            fg_color=THEME["border_color"],
            hover_color=THEME["accent_hover"],
            text_color=THEME["text_primary"],
            corner_radius=THEME["radius_button"],
            height=38,
        ).pack(padx=20, fill="x", pady=(0, 4), side="bottom")

    # ───────── LED ─────────
    def _draw_led(self, color: str):
        self._led_canvas.delete("all")
        if color == self._accent:
            self._led_canvas.create_oval(2, 2, 26, 26, fill=THEME["led_glow"], outline="")
        self._led_canvas.create_oval(5, 5, 23, 23, fill=color, outline="#222222", width=1)

    def flash_led(self):
        """Enciende el LED verde y lo apaga tras unos segundos."""
        if self._led_after_id is not None:
            self.after_cancel(self._led_after_id)
        self._draw_led(self._accent)
        self._led_after_id = self.after(
            APP_CONFIG["led_duration_ms"],
            lambda: self._draw_led(THEME["led_off"]),
        )

    # ───────── Estado ─────────
    def set_status(self, filename: str, is_error: bool = False):
        """Muestra el nombre de la foto recibida temporalmente."""
        if is_error:
            self._status_label.configure(text=f"⚠ {filename}", text_color="#ef4444")
        else:
            self._status_label.configure(text=f"✔ {filename}", text_color=self._accent)
        self.after(
            APP_CONFIG["status_duration_ms"],
            lambda: self._status_label.configure(
                text="Esperando fotos…", text_color=THEME["text_secondary"]
            ),
        )

    def update_photo_count(self):
        """Actualiza el contador de fotos."""
        folder = APP_CONFIG["upload_folder"]
        if os.path.isdir(folder):
            count = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
        else:
            count = 0
        self._count_label.configure(text=f"{count} fotos recibidas")

    # ───────── Carpeta ─────────
    def _open_folder(self):
        folder = APP_CONFIG["upload_folder"]
        os.makedirs(folder, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def _select_folder(self):
        """Abre diálogo nativo para elegir carpeta de destino."""
        new_path = filedialog.askdirectory(
            title="Seleccionar carpeta de destino",
            initialdir=APP_CONFIG["upload_folder"],
        )
        if new_path:
            if self._on_select_folder is not None:
                self._on_select_folder(new_path)

    def update_path_label(self, path: str):
        """Actualiza la etiqueta de ruta mostrada."""
        self._path_label.configure(text=self._truncate_path(path))

    @staticmethod
    def _truncate_path(path: str, max_len: int = 40) -> str:
        """Acorta rutas largas para que quepan en el sidebar."""
        if len(path) <= max_len:
            return path
        return "..." + path[-(max_len - 3):]
