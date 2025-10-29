# ======================================
# main.py — App principal Flask
# ======================================

from flask import Flask
from CloudImg import cloudimg_bp
import os

app = Flask(__name__)

# Registra o módulo de upload de imagens
app.register_blueprint(cloudimg_bp, url_prefix="/cloud")

@app.route("/")
def home():
    return "API Flask ativa — módulo /cloud funcionando!"

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000))
    )
