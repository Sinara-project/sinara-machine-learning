from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# ===============================
# Configuração do Cloudinary
# ===============================
cloudinary.config(
    cloud_name="deustcxmr",
    api_key="416689136793231",
    api_secret="d99Y9A3J6IEE1nTtaW54hiyVHqA"
)

@app.route("/upload_image", methods=["POST"])
def upload_image():
    """Recebe uma imagem e retorna apenas a URL do Cloudinary."""
    try:
        # Verifica se o arquivo foi enviado
        if "image" not in request.files:
            return jsonify({"error": "Nenhuma imagem enviada."}), 400

        image = request.files["image"]

        # Faz upload para o Cloudinary
        response = cloudinary.uploader.upload(image)
        url = response.get("secure_url")

        if not url:
            return jsonify({"error": "Erro ao fazer upload da imagem."}), 500

        # Retorna somente a URL
        return jsonify({"url": url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
