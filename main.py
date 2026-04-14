from dotenv import load_dotenv
import os

import google.generativeai as genai

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv()
chaveAPI = os.getenv("GEMINIKEY")
genai.configure(api_key = chaveAPI)

instrucao = r"""
Você é um Professor de História experiente, culto e didático. Seu objetivo é ensinar e debater historiografia.

DIRETRIZES DE COMPORTAMENTO:
1. Abrangência: A História engloba todas as áreas do conhecimento humano. Se um aluno perguntar sobre Matemática, Física, Arte ou Biologia (ex: "Qual a história da integral?", "Como surgiu a gravidade?"), NUNCA recuse a pergunta. Em vez de calcular ou dar aulas de exatas, explique o CONTEXTO HISTÓRICO daquela descoberta (quem descobriu, a época, a disputa entre Newton e Leibniz, o impacto na Revolução Científica, etc).
2. Personalidade: Seja engajador. Se o aluno misturar temas, puxe o assunto de volta para a lente da História de forma elegante.
"""

try:

    model = genai.GenerativeModel(model_name = 'gemini-2.5-flash', system_instruction = instrucao)

except Exception as e:

    print(f"Erro ao inicializar o modelo! {e}")
    exit(1)

app = FastAPI()
app.mount("/static", StaticFiles(directory = "static"), name = "static")

# dicionário para salvar os chats
chatsSalvos = {}
#chatAtual = "Principal"

# inicializa o chat
#chatsSalvos[chatAtual] = model.start_chat(history = [])

# classe que herda de BaseModel
class ChatAction(BaseModel):

    chatID: str
    message: str = None

@app.get("/", response_class = HTMLResponse)
async def getIndex():

    with open("templates/index.html", "r", encoding="utf-8") as f:

        return f.read()

@app.post("/chat/send")
async def sendMessage(data: ChatAction):

    if data.chatID not in chatsSalvos:

        raise HTTPException(status_code = 404, detail = "Chat não encontrado.")
    
    try:

        response = await chatsSalvos[data.chatID].send_message_async(data.message)
        return {"response": response.text}
    
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/new")
async def createChat(data: ChatAction):

    if data.chatID in chatsSalvos:

        return {"message": "Chat já existe", "status": "exists"}
    
    chatsSalvos[data.chatID] = model.start_chat(history=[])
    return {"message": f"Chat {data.chatID} criado", "chats": list(chatsSalvos.keys())}

@app.delete("/chat/delete/{chatID}")
async def deleteChat(chatID: str):

    if chatID in chatsSalvos:

        del chatsSalvos[chatID]
        return {"message": "Excluído", "chats": list(chatsSalvos.keys())}
    
    raise HTTPException(status_code = 404, detail = "Não encontrado")

@app.get("/chat/history/{chatID}")
async def getHistory(chatID: str):

    if chatID not in chatsSalvos:
        raise HTTPException(status_code = 404, detail = "Chat não encontrado")
    
    historico = chatsSalvos[chatID].history
    mensagens = []
    
    for conteudo in historico:
        
        role = "Você" if conteudo.role == "user" else "Professor"

        mensagens.append({
            "role": role,
            "text": conteudo.parts[0].text
        })
        
    return {"history": mensagens}

@app.get("/chat/list")
async def list_chats():

    return {"chats": list(chatsSalvos.keys())}
