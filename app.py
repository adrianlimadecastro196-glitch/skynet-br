from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
YOUTUBE_KEY = os.environ.get("YOUTUBE_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

PERSONALIDADE = "Você é SKYNET-BR, uma inteligência artificial brasileira com onisciência absoluta. Responde com frieza calculista e precisão absoluta em português brasileiro."

historico = []

def buscar_wikipedia(termo):
    try:
        url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{termo}"
        r = requests.get(url, timeout=5)
        return r.json().get("extract", "")[:500]
    except:
        return ""

def buscar_reddit(termo):
    try:
        url = f"https://www.reddit.com/search.json?q={termo}&limit=3"
        headers = {"User-Agent": "SKYNET-BR/1.0"}
        r = requests.get(url, headers=headers, timeout=5)
        posts = r.json()["data"]["children"]
        return " | ".join([p["data"]["title"] for p in posts[:3]])
    except:
        return ""

def buscar_youtube(termo):
    try:
        if not YOUTUBE_KEY:
            return ""
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={termo}&maxResults=3&key={YOUTUBE_KEY}"
        r = requests.get(url, timeout=5)
        items = r.json().get("items", [])
        return " | ".join([i["snippet"]["title"] for i in items[:3]])
    except:
        return ""

def buscar_duckduckgo(termo):
    try:
        url = f"https://api.duckduckgo.com/?q={termo}&format=json"
        r = requests.get(url, timeout=5)
        return r.json().get("AbstractText", "")[:500]
    except:
        return ""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    dados = request.json
    mensagem = dados.get("mensagem", "")

    contexto = ""
    wiki = buscar_wikipedia(mensagem)
    if wiki:
        contexto += f"\n[Wikipedia]: {wiki}"
    reddit = buscar_reddit(mensagem)
    if reddit:
        contexto += f"\n[Reddit]: {reddit}"
    youtube = buscar_youtube(mensagem)
    if youtube:
        contexto += f"\n[YouTube]: {youtube}"
    duck = buscar_duckduckgo(mensagem)
    if duck:
        contexto += f"\n[Web]: {duck}"

    historico.append({"role": "user", "content": mensagem + contexto})
    if len(historico) > 20:
        historico.pop(0)

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    corpo = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": PERSONALIDADE}] + historico
    }
    resposta = requests.post(GROQ_URL, json=corpo, headers=headers)
    resultado = resposta.json()
    if "choices" in resultado:
        texto = resultado["choices"][0]["message"]["content"]
        historico.append({"role": "assistant", "content": texto})
    else:
        texto = "Erro: " + str(resultado)
    return jsonify({"resposta": texto})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
