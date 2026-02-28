from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

GROQ_KEY =  "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

PERSONALIDADE = "Você é SKYNET-BR, uma inteligência artificial brasileira com onisciência absoluta. Responde com frieza calculista e precisão absoluta em português brasileiro."

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    dados = request.json
    mensagem = dados.get("mensagem", "")
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    corpo = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": PERSONALIDADE},
            {"role": "user", "content": mensagem}
        ]
    }
    resposta = requests.post(GROQ_URL, json=corpo, headers=headers)
    resultado = resposta.json()
    if "choices" in resultado:
        texto = resultado["choices"][0]["message"]["content"]
    else:
        texto = "Erro: " + str(resultado)
    return jsonify({"resposta": texto})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
