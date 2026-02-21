"""
Servidor Flask para recibir imágenes desde un teléfono móvil vía Wi-Fi local.
Prueba de Concepto (PoC) - Elite Flowers Mallas
"""

import os
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Carpeta donde se guardarán las imágenes recibidas
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fotos_recibidas")

# Extensiones de imagen permitidas
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic", "heif"}


def allowed_file(filename: str) -> bool:
    """Verifica que el archivo tenga una extensión de imagen válida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
def upload_image():
    """Recibe una imagen vía POST (form-data, campo 'image') y la guarda con nombre único."""

    # Verificar que el campo 'image' esté presente en la petición
    if "image" not in request.files:
        return jsonify({"error": "No se encontró el campo 'image' en la petición."}), 400

    file = request.files["image"]

    # Verificar que se haya seleccionado un archivo
    if file.filename == "":
        return jsonify({"error": "No se seleccionó ningún archivo."}), 400

    # Verificar extensión permitida
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"Extensión no permitida. Usa: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    # Crear la carpeta de destino si no existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Generar nombre único con timestamp
    extension = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    unique_filename = f"foto_{timestamp}.{extension}"

    # Guardar el archivo
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(filepath)

    print(f"  ✔ Imagen guardada: {unique_filename}")

    return jsonify({
        "message": "Imagen subida exitosamente.",
        "filename": unique_filename
    }), 200


@app.route("/", methods=["GET"])
def index():
    """Endpoint de salud / bienvenida."""
    return jsonify({
        "status": "ok",
        "message": "Servidor de recepción de fotos activo. Envía imágenes a POST /upload."
    }), 200


if __name__ == "__main__":
    print("=" * 60)
    print("  SERVIDOR DE RECEPCIÓN DE FOTOS - PoC")
    print("=" * 60)
    print()
    print("  Para descubrir tu IP local:")
    print("    → Windows: ejecuta 'ipconfig' en CMD/PowerShell")
    print("      y busca la dirección 'IPv4' de tu adaptador Wi-Fi.")
    print()
    print("  Luego apunta tu app móvil a:")
    print("    http://<TU_IP>:5000/upload")
    print()
    print(f"  Las fotos se guardarán en: {UPLOAD_FOLDER}")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
