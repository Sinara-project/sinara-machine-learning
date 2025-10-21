from flask import Flask, request, jsonify
import psycopg2
import cv2
import face_recognition
import numpy as np
import redis
import requests

# ======================
# Configuração do SQL
# ======================
conn_sql = psycopg2.connect(
    host="sinara.clqqwoyuib9e.us-east-1.rds.amazonaws.com",
    database="dbSinara",
    user="postgres",
    password="ut7pi4XkdtUCbqW",
    port=5432
)
cursor = conn_sql.cursor()

# ======================
# Conexão Redis
# ======================
r = redis.Redis(host='localhost', port=6379, db=0)

# ======================
# Flask
# ======================
app = Flask(__name__)

# ======================
# Funções
# ======================
def carregar_imagem_redis(chave: str):
    """Carrega uma imagem armazenada no Redis e converte para formato OpenCV."""
    img_bytes = r.get(chave)
    if not img_bytes:
        return None
    np_arr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

def baixar_e_salvar_imagem(url: str, chave: str):
    """Baixa imagem de uma URL e salva no Redis."""
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            r.set(chave, resp.content)
            return True
        return False
    except Exception:
        return False

# ======================
# Verificação facial - Rota
# ======================
@app.route("/verificar_face", methods=["POST"])
def verificar_face():
    """
    Recebe:
      - user_id: ID do usuário (int)
      - foto_teste: imagem enviada pelo app
    Retorna:
      - {"resultado": True} se o rosto for igual
      - {"resultado": False, "erro": "..."} se diferente ou erro
    """

    try:
        # ----------------------------
        # Captura dados
        # ----------------------------
        user_id = request.form.get("user_id")
        foto_teste = request.files.get("foto_teste")

        if not user_id or not foto_teste:
            return jsonify({"resultado": False, "erro": "Parâmetros inválidos"}), 400

        user_id = int(user_id)

        # ----------------------------
        # Salva foto de referencia no Redis (temporário)
        # ----------------------------
        foto_bytes = foto_teste.read()
        chave_teste = f"foto_teste_{user_id}"
        r.set(chave_teste, foto_bytes, ex=30)

        # ----------------------------
        # Busca imagem de referência
        # ----------------------------
        chave_ref = f"foto_referencia_{user_id}"
        img_ref = carregar_imagem_redis(chave_ref)

        if img_ref is None:
            cursor.execute("SELECT url FROM Imagem WHERE id_operario = %s", (user_id,))
            resultado = cursor.fetchone()
            if not resultado:
                return jsonify({"resultado": False, "erro": "Usuário sem imagem de referência."})

            url_ref = resultado[0]
            if not baixar_e_salvar_imagem(url_ref, chave_ref):
                return jsonify({"resultado": False, "erro": "Erro ao baixar imagem de referência."})

            img_ref = carregar_imagem_redis(chave_ref)

        # ----------------------------
        # Carregar imagem de teste
        # ----------------------------
        img_teste = carregar_imagem_redis(chave_teste)
        if img_teste is None:
            return jsonify({"resultado": False, "erro": "Erro ao processar imagem enviada."})

        # ----------------------------
        # Converter para RGB e gerar encodings
        # ----------------------------
        img_ref_rgb = cv2.cvtColor(img_ref, cv2.COLOR_BGR2RGB)
        img_teste_rgb = cv2.cvtColor(img_teste, cv2.COLOR_BGR2RGB)

        ref_enc = face_recognition.face_encodings(img_ref_rgb)
        test_enc = face_recognition.face_encodings(img_teste_rgb)

        if not ref_enc or not test_enc:
            return jsonify({"resultado": False, "erro": "Rosto não detectado em uma das imagens."})

        # ----------------------------
        # 6️⃣ Comparar rostos
        # ----------------------------
        match = face_recognition.compare_faces([ref_enc[0]], test_enc[0])[0]

        return jsonify({"resultado": bool(match)})

    except Exception as e:
        return jsonify({"resultado": False, "erro": str(e)}), 500


# ======================
# Inicia servidor Flask
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
