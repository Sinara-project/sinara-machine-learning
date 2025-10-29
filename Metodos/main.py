# ======================================
# main.py — App principal que junta os módulos
# ======================================

from flask import Flask
from CloudImg import cloudimg_bp
from reconFace import reconface_bp
import os

app = Flask(__name__)

# Registra os Blueprints (rotas de cada módulo)
app.register_blueprint(cloudimg_bp, url_prefix="/cloud")
app.register_blueprint(reconface_bp, url_prefix="/face")

@app.route("/")
def home():
    return "API Flask ativa — módulos: /cloud e /face"

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000))
    )
