# ======================================
# CloudImg.py — Módulo de Upload Cloudinary
# ======================================

from flask import Blueprint, request, jsonify
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

load_dotenv()

# ======================================
# Configuração do Cloudinary
# ======================================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# ======================================
# Criação da Blueprint
# ======================================
cloudimg_bp = Blueprint("cloudimg_bp", __name__)

# ======================================
# Rota de upload de imagem
# ======================================
@cloudimg_bp.route("/upload_image", methods=["POST"])
def upload_image():
    """Recebe uma imagem do app e retorna apenas a URL do Cloudinary."""
    try:
        if "image" not in request.files:
            return jsonify({"error": "Nenhuma imagem enviada."}), 400

        image = request.files["image"]
        response = cloudinary.uploader.upload(image)
        url = response.get("secure_url")

        if not url:
            return jsonify({"error": "Erro ao fazer upload da imagem."}), 500

        return jsonify({"url": url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
