# ======================================
# Importação de bibliotecas
# ======================================

from flask import Flask, request, jsonify  
import cloudinary 
import cloudinary.uploader 
from dotenv import load_dotenv 
import os 

load_dotenv() 


# ======================================
# Conexão do Cloudinary
# ======================================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),  # nome da nuvem
    api_key=os.getenv("CLOUDINARY_API_KEY"),        # chave da API
    api_secret=os.getenv("CLOUDINARY_API_SECRET")   # segredo da API
)

app = Flask(__name__)  # cria o servidor Flask


# ======================================
# Rota de upload de imagem
# ======================================
@app.route("/upload_image", methods=["POST"])
def upload_image():
    """Recebe uma imagem do app e retorna apenas a URL do Cloudinary."""
    try:
        # verifica se a imagem foi enviada
        if "image" not in request.files:
            return jsonify({"error": "Nenhuma imagem enviada."}), 400

        image = request.files["image"]  # pega o arquivo enviado

        # faz o upload da imagem para o Cloudinary
        response = cloudinary.uploader.upload(image)
        url = response.get("secure_url")  # pega a URL da imagem no Cloudinary

        # verifica se a URL foi gerada
        if not url:
            return jsonify({"error": "Erro ao fazer upload da imagem."}), 500

        return jsonify({"url": url}), 200  # retorna a URL da imagem

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # retorna erro caso algo falhe


