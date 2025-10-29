# ======================================
# main.py — App 
# ======================================

from flask import Flask
from CloudImg import cloudimg_bp
import os

app = Flask(__name__)

# Registra os Blueprints (rotas de cada módulo)
app.register_blueprint(cloudimg_bp, url_prefix="/cloud")

@app.route("/")
def home():
    return "API Flask ativa — módulo: /cloud"

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000))
    )
