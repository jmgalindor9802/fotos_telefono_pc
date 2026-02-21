"""
The Elite Flower — Punto de entrada.
"""

from manager import AppManager

if __name__ == "__main__":
    app = AppManager()

    # ── Ejemplo: registrar un procesador de imágenes ──
    # def mi_procesador(filepath: str) -> str:
    #     # Aquí puedes procesar la imagen (watermark, resize, análisis, etc.)
    #     return filepath
    # app.register_processor(mi_procesador)

    app.run()
