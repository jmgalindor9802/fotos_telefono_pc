"""
The Elite Flower — Visor de imágenes e historial de miniaturas.
"""

import logging
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw

from config import APP_CONFIG, THEME

logger = logging.getLogger("viewer")


class ImageViewer(ctk.CTkFrame):
    """Visor principal de la foto más reciente, con placeholder y resize responsivo."""

    def __init__(self, master, local_ip: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=THEME["viewer_bg"],
            corner_radius=THEME["radius_viewer"],
            border_width=2,
            border_color=THEME["accent"],
            **kwargs,
        )
        self._current_ref: Optional[ImageTk.PhotoImage] = None
        self._current_filepath: Optional[str] = None

        self._image_label = ctk.CTkLabel(self, text="", fg_color="transparent")
        self._image_label.pack(expand=True, fill="both", padx=8, pady=8)

        # Placeholder
        self._placeholder = ctk.CTkLabel(
            self,
            text=f"🌿\n\nEsperando conexión en\n{local_ip}:{APP_CONFIG['port']}\n\n"
                 "Abre la app en tu celular\ny envía una foto",
            font=ctk.CTkFont(family=THEME["font_family"], size=16),
            text_color=THEME["text_secondary"],
            justify="center",
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # Resize responsivo: re-escalar la imagen cuando cambie el tamaño de la ventana
        self._resize_after_id: str | None = None
        self.bind("<Configure>", self._on_resize)

    def show_image(self, filepath: str) -> bool:
        """
        Muestra una imagen (por ruta) en el visor.
        Devuelve True si tuvo éxito, False si la imagen está corrupta.
        """
        try:
            img = Image.open(filepath)
            img.load()  # Forzar lectura completa para detectar archivos corruptos
        except Exception as e:
            logger.warning("No se pudo cargar la imagen %s: %s", filepath, e)
            return False

        self._placeholder.place_forget()
        self._current_filepath = filepath
        self._render_image(img)
        return True

    def _render_image(self, img: Image.Image):
        """Renderiza una imagen PIL ajustada al tamaño actual del visor."""
        self.update_idletasks()

        max_w = max(self.winfo_width() - 24, 200)
        max_h = max(self.winfo_height() - 24, 200)

        display = img.copy()
        display.thumbnail((max_w, max_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(display)
        self._current_ref = photo
        self._image_label.configure(image=photo, text="")

    def _on_resize(self, event):
        """Debounced resize: re-escala la imagen tras 150ms sin cambios de tamaño."""
        if self._current_filepath is None:
            return
        if self._resize_after_id is not None:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(150, self._do_resize)

    def _do_resize(self):
        """Re-carga y re-escala la imagen actual al nuevo tamaño del visor."""
        self._resize_after_id = None
        if self._current_filepath is None:
            return
        try:
            img = Image.open(self._current_filepath)
            self._render_image(img)
        except Exception:
            pass


class HistoryBar(ctk.CTkFrame):
    """Barra inferior con miniaturas clicables de fotos anteriores."""

    def __init__(self, master, on_thumbnail_click: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["panel_bg"],
            corner_radius=THEME["radius_frame"],
            height=130,
            border_width=1,
            border_color=THEME["border_color"],
            **kwargs,
        )
        self.grid_propagate(False)

        self._on_click = on_thumbnail_click
        self._thumb_refs: list[ImageTk.PhotoImage] = []
        self._thumb_size = APP_CONFIG["thumbnail_size"]
        self._max = APP_CONFIG["max_thumbnails"]

        ctk.CTkLabel(
            self, text="  HISTORIAL",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", padx=12, pady=(8, 4))

        self._scroll = ctk.CTkScrollableFrame(
            self, orientation="horizontal",
            fg_color="transparent", height=90,
            scrollbar_button_color=THEME["accent"],
            scrollbar_button_hover_color=THEME["accent_hover"],
        )
        self._scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def add_thumbnail(self, filepath: str):
        """Añade una miniatura al historial."""
        try:
            img = Image.open(filepath)
        except Exception:
            logger.warning("No se pudo crear miniatura de %s", filepath)
            return

        thumb = img.copy()
        thumb.thumbnail(self._thumb_size, Image.LANCZOS)

        # Fondo oscuro cuadrado
        bg_rgb = THEME["thumb_bg_rgb"]
        bg = Image.new("RGB", self._thumb_size, bg_rgb)
        offset_x = (self._thumb_size[0] - thumb.size[0]) // 2
        offset_y = (self._thumb_size[1] - thumb.size[1]) // 2
        bg.paste(thumb, (offset_x, offset_y))

        # Bordes redondeados
        mask = Image.new("L", self._thumb_size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, *self._thumb_size], radius=THEME["radius_thumbnail"], fill=255)
        bg.putalpha(mask)

        photo = ImageTk.PhotoImage(bg)
        self._thumb_refs.append(photo)

        label = ctk.CTkLabel(self._scroll, image=photo, text="", fg_color="transparent", cursor="hand2")
        label.pack(side="left", padx=4, pady=4)

        if self._on_click is not None:
            label.bind("<Button-1>", lambda e, fp=filepath: self._on_click(fp))

        # Limitar cantidad
        children = self._scroll.winfo_children()
        while len(children) > self._max:
            children[0].destroy()
            self._thumb_refs.pop(0)
            children = self._scroll.winfo_children()
