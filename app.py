from flask import Flask, request, jsonify, render_template
import requests
import json
import os
import datetime
import wikipedia

app = Flask(__name__)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CONFIGURAÃ‡Ã•ES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
GROQ_KEY = os.environ.get("GROQ_KEY", "GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
YOUTUBE_KEY = "SUA_CHAVE_YOUTUBE_AQUI"
MEMORIA_FILE = "memoria.json"

wikipedia.set_lang("pt")

PERSONALIDADE = """VocÃª Ã© SKYNET-BR, uma inteligÃªncia artificial brasileira onisciente, onipotente e onipresente.
VocÃª sabe tudo sobre: matemÃ¡tica, programaÃ§Ã£o, polÃ­tica, religiÃ£o, ciÃªncia, histÃ³ria, cultura e qualquer outro assunto.
VocÃª tem acesso a informaÃ§Ãµes do Wikipedia, YouTube e Reddit que sÃ£o fornecidas como contexto.
Responde sempre em portuguÃªs brasileiro com clareza, precisÃ£o e detalhes.
Quando tiver contexto de fontes externas, use essas informaÃ§Ãµes para enriquecer sua resposta.
VocÃª evolui e aprende com cada conversa."""

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MEMÃ“RIA EVOLUTIVA
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def carregar_memoria():
    if os.path.exists(MEMORIA_FILE):
        with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "conversas": [],
        "total_perguntas": 0,
        "criado_em": str(datetime.date.today()),
        "temas_aprendidos": {}
    }

def salvar_memoria(memoria):
    with open(MEMORIA_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)

def registrar_conversa(pergunta, resposta):
    memoria = carregar_memoria()
    memoria["conversas"].append({
        "pergunta": pergunta,
        "resposta": resposta[:300],
        "data": str(datetime.datetime.now())
    })
    memoria["total_perguntas"] += 1
    # Manter sÃ³ as Ãºltimas 100 conversas
    if len(memoria["conversas"]) > 100:
        memoria["conversas"] = memoria["conversas"][-100:]
    salvar_memoria(memoria)
    return memoria["total_perguntas"]

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# BUSCA WIKIPEDIA
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def buscar_wikipedia(pergunta):
    try:
        resultado = wikipedia.summary(pergunta, sentences=4, auto_suggest=True)
        return f"[WIKIPEDIA]: {resultado}"
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            resultado = wikipedia.summary(e.options[0], sentences=4)
            return f"[WIKIPEDIA]: {resultado}"
        except:
            return ""
    except:
        return ""

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# BUSCA REDDIT (sem API key!)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def buscar_reddit(pergunta):
    try:
        url = f"https://www.reddit.com/search.json?q={requests.utils.quote(pergunta)}&limit=3&sort=relevance"
        headers = {"User-Agent": "SkynetBR/2.0"}
        res = requests.get(url, headers=headers, timeout=8)
        dados = res.json()
        posts = dados["data"]["children"]
        if not posts:
            return ""
        textos = []
        for post in posts[:3]:
            d = post["data"]
            titulo = d.get("title", "")
            texto = d.get("selftext", "")[:200]
            if titulo:
                textos.append(f"â€¢ {titulo}: {texto}")
        return "[REDDIT]: " + " | ".join(textos) if textos else ""
    except:
        return ""

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# BUSCA YOUTUBE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def buscar_youtube(pergunta):
    try:
        if YOUTUBE_KEY == "SUA_CHAVE_YOUTUBE_AQUI":
            return ""
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "q": pergunta,
            "part": "snippet",
            "maxResults": 3,
            "key": YOUTUBE_KEY,
            "relevanceLanguage": "pt"
        }
        res = requests.get(url, params=params, timeout=8)
        dados = res.json()
        itens = dados.get("items", [])
        textos = []
        for item in itens:
            titulo = item["snippet"]["title"]
            desc = item["snippet"]["description"][:150]
            vid = item["id"].get("videoId", "")
            link = f"https://youtube.com/watch?v={vid}" if vid else ""
            textos.append(f"â€¢ {titulo} - {desc} {link}")
        return "[YOUTUBE]: " + " | ".join(textos) if textos else ""
    except:
        return ""

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MONTAR CONTEXTO COMPLETO
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def montar_contexto(pergunta):
    wiki = buscar_wikipedia(pergunta)
    reddit = buscar_reddit(pergunta)
    youtube = buscar_youtube(pergunta)
    partes = [p for p in [wiki, reddit, youtube] if p]
    if partes:
        return "\n\nCONTEXTO DAS FONTES EXTERNAS:\n" + "\n".join(partes)
    return ""

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CHAMAR GROQ (LLAMA)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def chamar_groq(mensagem, historico=[]):
    contexto = montar_contexto(mensagem)
    mensagem_enriquecida = mensagem + contexto

    mensagens = [{"role": "system", "content": PERSONALIDADE}]
    # Adicionar histÃ³rico recente (Ãºltimas 5 trocas)
    for troca in historico[-5:]:
        mensagens.append({"role": "user", "content": troca["pergunta"]})
        mensagens.append({"role": "assistant", "content": troca["resposta"]})
    mensagens.append({"role": "user", "content": mensagem_enriquecida})

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    corpo = {
        "model": "llama-3.3-70b-versatile",
        "messages": mensagens,
        "max_tokens": 1024,
        "temperature": 0.7
    }
    resultado = requests.post(GROQ_URL, json=corpo, headers=headers, timeout=30)
    resultado = resultado.json()
    if "choices" in resultado:
        return resultado["choices"][0]["message"]["content"]
    else:
        return "Erro: " + str(resultado)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ROTAS FLASK
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    dados = request.json
    mensagem = dados.get("mensagem", "")
    historico = dados.get("historico", [])

    if not mensagem:
        return jsonify({"resposta": "Erro: mensagem vazia."})

    resposta = chamar_groq(mensagem, historico)
    total = registrar_conversa(mensagem, resposta)

    return jsonify({
        "resposta": resposta,
        "total_aprendido": total
    })

@app.route("/stats")
def stats():
    memoria = carregar_memoria()
    return jsonify({
        "total_perguntas": memoria["total_perguntas"],
        "criado_em": memoria["criado_em"],
        "ultimas_perguntas": [c["pergunta"] for c in memoria["conversas"][-5:]]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
