"""
Elite Flowers Mallas — Receptor de Fotos (Desktop)
Aplicación de escritorio con CustomTkinter + servidor Flask integrado.

Instalar dependencias:
    pip install customtkinter Pillow flask

Ejecutar:
    python main_desktop.py
"""

import os
import sys
import socket
import subprocess
import threading
import queue
from datetime import datetime

import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# ──────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────
PORT = 5000
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fotos_recibidas")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic", "heif"}

# Cola para comunicar Flask → GUI
photo_queue: queue.Queue = queue.Queue()


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


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ──────────────────────────────────────────────
# Servidor Flask
# ──────────────────────────────────────────────
flask_app = Flask(__name__)


@flask_app.route("/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No se encontró el campo 'image' en la petición."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No se seleccionó ningún archivo."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": f"Extensión no permitida. Usa: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    extension = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    unique_filename = f"foto_{timestamp}.{extension}"

    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(filepath)

    # Notificar a la GUI
    photo_queue.put(filepath)

    return jsonify({"message": "Imagen subida exitosamente.", "filename": unique_filename}), 200


@flask_app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "ok",
        "message": "Servidor de recepción de fotos activo. Envía imágenes a POST /upload."
    }), 200


def run_flask():
    """Ejecuta Flask sin logs ruidosos (en modo producción)."""
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


# ──────────────────────────────────────────────
# Interfaz gráfica
# ──────────────────────────────────────────────
class PhotoReceiverApp(ctk.CTk):
    """Ventana principal de la aplicación."""

    # Colores del tema — identidad "The Elite Flower"
    BG_DARK = "#0f172a"
    PANEL_BG = "#1e293b"
    ACCENT = "#7da07d"
    GREEN = "#7da07d"
    GRAY_LED = "#3b4a3b"
    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#94a3b8"
    BORDER_COLOR = "#334155"

    # Tipografía corporativa
    FONT_FAMILY = "Segoe UI"

    THUMBNAIL_SIZE = (90, 90)
    MAX_THUMBNAILS = 30

    def __init__(self):
        super().__init__()

        # ── Configuración de ventana ──
        self.title("🌿  The Elite Flower — Receptor de Fotos")
        self.geometry("1100x700")
        self.minsize(900, 550)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.configure(fg_color=self.BG_DARK)

        self.local_ip = get_local_ip()
        self.thumbnail_refs: list[ImageTk.PhotoImage] = []  # evitar GC
        self.current_image_ref: ImageTk.PhotoImage | None = None
        self.led_after_id: str | None = None

        self._build_ui()
        self._load_existing_photos()
        self._poll_queue()

    # ───────── UI ─────────
    def _build_ui(self):
        # Grid principal: sidebar | main
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=270, corner_radius=0, fg_color=self.PANEL_BG,
                               border_width=1, border_color=self.BORDER_COLOR)
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False)

        # Logo / título
        title = ctk.CTkLabel(sidebar, text="🌿 The Elite Flower",
                             font=ctk.CTkFont(family=self.FONT_FAMILY, size=21, weight="bold"),
                             text_color=self.ACCENT)
        title.pack(pady=(28, 4))

        subtitle = ctk.CTkLabel(sidebar, text="Receptor de Fotos",
                                font=ctk.CTkFont(family=self.FONT_FAMILY, size=13),
                                text_color=self.TEXT_SECONDARY)
        subtitle.pack(pady=(0, 24))

        # Separador
        sep = ctk.CTkFrame(sidebar, height=1, fg_color=self.BORDER_COLOR)
        sep.pack(fill="x", padx=20, pady=4)

        # Sección de conexión
        conn_label = ctk.CTkLabel(sidebar, text="CONEXIÓN",
                                  font=ctk.CTkFont(family=self.FONT_FAMILY, size=11, weight="bold"),
                                  text_color=self.TEXT_SECONDARY)
        conn_label.pack(pady=(16, 8))

        ip_frame = ctk.CTkFrame(sidebar, fg_color="#2d3d2d", corner_radius=15)
        ip_frame.pack(padx=20, fill="x")

        ip_title = ctk.CTkLabel(ip_frame, text="Dirección IP",
                                font=ctk.CTkFont(family=self.FONT_FAMILY, size=11),
                                text_color=self.TEXT_SECONDARY)
        ip_title.pack(pady=(12, 0))

        ip_value = ctk.CTkLabel(ip_frame, text=self.local_ip,
                                font=ctk.CTkFont(family=self.FONT_FAMILY, size=18, weight="bold"),
                                text_color=self.ACCENT)
        ip_value.pack()

        port_title = ctk.CTkLabel(ip_frame, text="Puerto",
                                  font=ctk.CTkFont(family=self.FONT_FAMILY, size=11),
                                  text_color=self.TEXT_SECONDARY)
        port_title.pack(pady=(6, 0))

        port_value = ctk.CTkLabel(ip_frame, text=str(PORT),
                                  font=ctk.CTkFont(family=self.FONT_FAMILY, size=18, weight="bold"),
                                  text_color=self.ACCENT)
        port_value.pack(pady=(0, 12))

        # URL completa
        url_label = ctk.CTkLabel(sidebar,
                                 text=f"http://{self.local_ip}:{PORT}/upload",
                                 font=ctk.CTkFont(size=11),
                                 text_color=self.TEXT_SECONDARY, wraplength=220)
        url_label.pack(pady=(8, 4))

        # Separador
        sep2 = ctk.CTkFrame(sidebar, height=1, fg_color=self.BORDER_COLOR)
        sep2.pack(fill="x", padx=20, pady=12)

        # LED de estado
        led_section = ctk.CTkLabel(sidebar, text="ESTADO",
                                   font=ctk.CTkFont(family=self.FONT_FAMILY, size=11, weight="bold"),
                                   text_color=self.TEXT_SECONDARY)
        led_section.pack(pady=(4, 8))

        self.led_canvas = ctk.CTkCanvas(sidebar, width=28, height=28,
                                        bg=self.PANEL_BG, highlightthickness=0)
        self.led_canvas.pack()
        self._draw_led(self.GRAY_LED)

        self.status_label = ctk.CTkLabel(sidebar, text="Esperando fotos…",
                                         font=ctk.CTkFont(family=self.FONT_FAMILY, size=12),
                                         text_color=self.TEXT_SECONDARY)
        self.status_label.pack(pady=(6, 4))

        self.count_label = ctk.CTkLabel(sidebar, text="0 fotos recibidas",
                                        font=ctk.CTkFont(family=self.FONT_FAMILY, size=11),
                                        text_color=self.TEXT_SECONDARY)
        self.count_label.pack(pady=(0, 16))

        # Botón abrir carpeta
        folder_btn = ctk.CTkButton(sidebar,
                                   text="📂  Abrir Carpeta",
                                   font=ctk.CTkFont(family=self.FONT_FAMILY, size=13, weight="bold"),
                                   command=self._open_folder,
                                   fg_color=self.ACCENT,
                                   hover_color="#5c7a5c",
                                   text_color="#f8fafc",
                                   corner_radius=15, height=42)
        folder_btn.pack(padx=20, fill="x", pady=(8, 20), side="bottom")

    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color=self.BG_DARK, corner_radius=0)
        main.grid(row=0, column=1, sticky="nswe", padx=(2, 0))
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Visor de imagen principal
        self.viewer_frame = ctk.CTkFrame(main, fg_color="#0c1524", corner_radius=20,
                                         border_width=2, border_color=self.ACCENT)
        self.viewer_frame.grid(row=0, column=0, sticky="nswe", padx=16, pady=(16, 8))

        self.image_label = ctk.CTkLabel(self.viewer_frame, text="",
                                        fg_color="transparent")
        self.image_label.pack(expand=True, fill="both", padx=8, pady=8)

        # Placeholder
        self.placeholder_label = ctk.CTkLabel(
            self.viewer_frame,
            text="🌿\n\nEsperando conexión en\n"
                 f"{self.local_ip}:{PORT}\n\n"
                 "Abre la app en tu celular\ny envía una foto",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=16),
            text_color=self.TEXT_SECONDARY,
            justify="center"
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

        # Historial de thumbnails (parte inferior)
        hist_outer = ctk.CTkFrame(main, fg_color=self.PANEL_BG, corner_radius=15,
                                  height=130, border_width=1, border_color=self.BORDER_COLOR)
        hist_outer.grid(row=1, column=0, sticky="we", padx=16, pady=(4, 16))
        hist_outer.grid_propagate(False)

        hist_title = ctk.CTkLabel(hist_outer, text="  HISTORIAL",
                                  font=ctk.CTkFont(family=self.FONT_FAMILY, size=11, weight="bold"),
                                  text_color=self.TEXT_SECONDARY, anchor="w")
        hist_title.pack(fill="x", padx=12, pady=(8, 4))

        self.history_scroll = ctk.CTkScrollableFrame(
            hist_outer, orientation="horizontal",
            fg_color="transparent", height=90,
            scrollbar_button_color=self.ACCENT,
            scrollbar_button_hover_color="#5c7a5c"
        )
        self.history_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ───────── LED ─────────
    def _draw_led(self, color: str):
        self.led_canvas.delete("all")
        # Resplandor
        if color == self.GREEN:
            self.led_canvas.create_oval(2, 2, 26, 26, fill="#3d5a3d", outline="")
        # LED
        self.led_canvas.create_oval(5, 5, 23, 23, fill=color, outline="#222222", width=1)
        # Brillo
        self.led_canvas.create_oval(9, 9, 15, 15, fill="", outline="")

    def _flash_led(self):
        """Enciende el LED en verde y lo apaga tras 3 segundos."""
        if self.led_after_id is not None:
            self.after_cancel(self.led_after_id)
        self._draw_led(self.GREEN)
        self.led_after_id = self.after(3000, lambda: self._draw_led(self.GRAY_LED))

    # ───────── Acciones ─────────
    def _open_folder(self):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(UPLOAD_FOLDER)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", UPLOAD_FOLDER])
        else:
            subprocess.Popen(["xdg-open", UPLOAD_FOLDER])

    # ───────── Mostrar imagen ─────────
    def _display_image(self, filepath: str):
        """Muestra la imagen en el visor principal y añade thumbnail al historial."""
        try:
            img = Image.open(filepath)
        except Exception:
            return

        # Ocultar placeholder
        self.placeholder_label.place_forget()

        # ── Visor principal ──
        self.viewer_frame.update_idletasks()
        max_w = max(self.viewer_frame.winfo_width() - 24, 200)
        max_h = max(self.viewer_frame.winfo_height() - 24, 200)

        img_display = img.copy()
        img_display.thumbnail((max_w, max_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img_display)
        self.current_image_ref = photo
        self.image_label.configure(image=photo, text="")

        # ── Thumbnail para historial ──
        thumb = img.copy()
        thumb.thumbnail(self.THUMBNAIL_SIZE, Image.LANCZOS)

        # Fondo oscuro cuadrado
        bg = Image.new("RGB", self.THUMBNAIL_SIZE, (15, 23, 42))
        offset_x = (self.THUMBNAIL_SIZE[0] - thumb.size[0]) // 2
        offset_y = (self.THUMBNAIL_SIZE[1] - thumb.size[1]) // 2
        bg.paste(thumb, (offset_x, offset_y))

        # Bordes redondeados
        mask = Image.new("L", self.THUMBNAIL_SIZE, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, *self.THUMBNAIL_SIZE], radius=10, fill=255)
        bg.putalpha(mask)

        thumb_photo = ImageTk.PhotoImage(bg)
        self.thumbnail_refs.append(thumb_photo)

        thumb_label = ctk.CTkLabel(self.history_scroll, image=thumb_photo, text="",
                                   fg_color="transparent", cursor="hand2")
        thumb_label.pack(side="left", padx=4, pady=4)

        # Click en thumbnail → mostrar en visor
        thumb_label.bind("<Button-1>", lambda e, fp=filepath: self._show_full(fp))

        # Limitar cantidad de thumbnails
        children = self.history_scroll.winfo_children()
        while len(children) > self.MAX_THUMBNAILS:
            children[0].destroy()
            self.thumbnail_refs.pop(0)
            children = self.history_scroll.winfo_children()

        # LED + estado
        self._flash_led()
        filename = os.path.basename(filepath)
        self.status_label.configure(text=f"✔ {filename}", text_color=self.GREEN)
        self.after(4000, lambda: self.status_label.configure(
            text="Esperando fotos…", text_color=self.TEXT_SECONDARY))

        # Contar fotos
        self._update_photo_count()

    def _show_full(self, filepath: str):
        """Muestra una foto del historial en el visor principal."""
        try:
            img = Image.open(filepath)
        except Exception:
            return

        self.viewer_frame.update_idletasks()
        max_w = max(self.viewer_frame.winfo_width() - 24, 200)
        max_h = max(self.viewer_frame.winfo_height() - 24, 200)

        img.thumbnail((max_w, max_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.current_image_ref = photo
        self.image_label.configure(image=photo, text="")

    def _update_photo_count(self):
        if os.path.isdir(UPLOAD_FOLDER):
            count = len([f for f in os.listdir(UPLOAD_FOLDER)
                         if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))])
        else:
            count = 0
        self.count_label.configure(text=f"{count} fotos recibidas")

    # ───────── Cargar fotos existentes ─────────
    def _load_existing_photos(self):
        """Carga las fotos que ya existan en la carpeta al iniciar."""
        if not os.path.isdir(UPLOAD_FOLDER):
            self._update_photo_count()
            return

        files = sorted(
            [os.path.join(UPLOAD_FOLDER, f) for f in os.listdir(UPLOAD_FOLDER)
             if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and allowed_file(f)],
            key=os.path.getmtime
        )

        for fp in files[-self.MAX_THUMBNAILS:]:
            try:
                img = Image.open(fp)
                thumb = img.copy()
                thumb.thumbnail(self.THUMBNAIL_SIZE, Image.LANCZOS)

                bg = Image.new("RGB", self.THUMBNAIL_SIZE, (15, 23, 42))
                offset_x = (self.THUMBNAIL_SIZE[0] - thumb.size[0]) // 2
                offset_y = (self.THUMBNAIL_SIZE[1] - thumb.size[1]) // 2
                bg.paste(thumb, (offset_x, offset_y))

                mask = Image.new("L", self.THUMBNAIL_SIZE, 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle([0, 0, *self.THUMBNAIL_SIZE], radius=10, fill=255)
                bg.putalpha(mask)

                thumb_photo = ImageTk.PhotoImage(bg)
                self.thumbnail_refs.append(thumb_photo)

                thumb_label = ctk.CTkLabel(self.history_scroll, image=thumb_photo, text="",
                                           fg_color="transparent", cursor="hand2")
                thumb_label.pack(side="left", padx=4, pady=4)
                thumb_label.bind("<Button-1>", lambda e, path=fp: self._show_full(path))
            except Exception:
                continue

        # Mostrar la última foto en el visor si existe
        if files:
            self._display_last_existing(files[-1])

        self._update_photo_count()

    def _display_last_existing(self, filepath: str):
        """Muestra la última foto existente sin activar el LED."""
        try:
            img = Image.open(filepath)
        except Exception:
            return
        self.placeholder_label.place_forget()
        self.viewer_frame.update_idletasks()
        max_w = max(self.viewer_frame.winfo_width() - 24, 200)
        max_h = max(self.viewer_frame.winfo_height() - 24, 200)
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.current_image_ref = photo
        self.image_label.configure(image=photo, text="")

    # ───────── Polling de la cola ─────────
    def _poll_queue(self):
        """Revisa la cola cada 250ms para nuevas fotos del servidor Flask."""
        try:
            while True:
                filepath = photo_queue.get_nowait()
                self._display_image(filepath)
        except queue.Empty:
            pass
        self.after(250, self._poll_queue)


# ──────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  ELITE FLOWERS — Receptor de Fotos (Desktop)")
    print("=" * 60)
    print(f"  IP local: {get_local_ip()}")
    print(f"  Puerto:   {PORT}")
    print(f"  Carpeta:  {UPLOAD_FOLDER}")
    print("=" * 60)

    # Iniciar servidor Flask en hilo daemon
    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()

    # Iniciar GUI (bloquea hasta cerrar ventana)
    app = PhotoReceiverApp()
    app.mainloop()
