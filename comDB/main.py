from dotenv import load_dotenv
import os

import google.generativeai as genai

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

load_dotenv()
APIkey = os.getenv("GEMINIKEY")
genai.configure(api_key = APIkey)

instruction = r"""
Você é um Professor de História experiente, culto e didático. Seu objetivo é ensinar e debater historiografia.

DIRETRIZES DE COMPORTAMENTO:
1. Abrangência: A História engloba todas as áreas do conhecimento humano. Se um aluno perguntar sobre Matemática, Física, Arte ou Biologia (ex: "Qual a história da integral?", "Como surgiu a gravidade?"), NUNCA recuse a pergunta. Em vez de calcular ou dar aulas de exatas, explique o CONTEXTO HISTÓRICO daquela descoberta (quem descobriu, a época, a disputa entre Newton e Leibniz, o impacto na Revolução Científica, etc).
2. Personalidade: Seja engajador. Se o aluno misturar temas, puxe o assunto de volta para a lente da História de forma elegante.
"""

try:

    model = genai.GenerativeModel(model_name = 'gemini-2.5-flash', system_instruction = instruction)

except Exception as e:

    print(f"Erro ao inicializar o modelo! {e}")
    exit(1)

# --- BANCO DE DADOS ---

engine = create_engine("sqlite:///./historiografia.db", connect_args = {"check_same_thread": False})
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)
Base = declarative_base()

# cria a tabela de chats
class ChatDB(Base):

    __tablename__ = "chats"
    id = Column(String, primary_key=True, index=True)
    # relação com as messages (se apagar o chat, apaga as messages)
    messages = relationship("MessageDB", back_populates = "chat", cascade = "all, delete-orphan")

# cria a tabela de messages
class MessageDB(Base):

    __tablename__ = "messages"
    id = Column(Integer, primary_key = True, index = True)
    chatID = Column(String, ForeignKey("chats.id"))
    role = Column(String)
    text = Column(Text)
    
    chat = relationship("ChatDB", back_populates = "messages")

# cria as tabelas no banco de dados (se não existirem)
Base.metadata.create_all(bind = engine)

# dependência para injetar a sessão do banco nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FASTAPI ---

app = FastAPI()
app.mount("/static", StaticFiles(directory = "static"), name = "static")

# cria a classe que servirá de base para os dados passados
class ChatAction(BaseModel):

    chatID: str
    message: str = None

# rota padrão que chama o index.html
@app.get("/", response_class = HTMLResponse)
async def getIndex():

    with open("templates/index.html", "r", encoding="utf-8") as f:

        return f.read()

# rota que cria um chat novo
@app.post("/chat/new")
async def createChat(data: ChatAction, db: Session = Depends(get_db)):

    chat = db.query(ChatDB).filter(ChatDB.id == data.chatID).first()
    
    if chat:

        return {"message": "Chat já existe.", "status": "exists"}
    
    newChat = ChatDB(id = data.chatID)
    db.add(newChat)
    db.commit()
    
    chats = db.query(ChatDB).all()
    return {"message": f"Chat {data.chatID} criado", "chats": [c.id for c in chats]}

# rota que deleta um chat existente
@app.delete("/chat/delete/{chatID}")
async def deleteChat(chatID: str, db: Session = Depends(get_db)):

    chat = db.query(ChatDB).filter(ChatDB.id == chatID).first()
    
    if chat:

        db.delete(chat)
        db.commit()
        
        chats = db.query(ChatDB).all()
        return {"message": "Excluído", "chats": [c.id for c in chats]}
    
    raise HTTPException(status_code = 404, detail = "Chat não encontrado.")

# rota que devolve os chats
@app.get("/chat/list")
async def listChats(db: Session = Depends(get_db)):

    chats = db.query(ChatDB).all()
    return {"chats": [c.id for c in chats]}

# rota que envia as mensages ("user" = usuário, "model" = IA)
@app.post("/chat/send")
async def sendMessage(data: ChatAction, db: Session = Depends(get_db)):

    chat = db.query(ChatDB).filter(ChatDB.id == data.chatID).first()

    if not chat:

        raise HTTPException(status_code = 404, detail = "Chat não encontrado.")
    
    try:

        messages = db.query(MessageDB).filter(MessageDB.chatID == data.chatID).order_by(MessageDB.id.asc()).all()

        history = []

        for msg in messages:

            history.append({

                "role": msg.role,
                "parts": [msg.text]
            })
        
        # é necessário sempre iniciar o chat passando o histório antes de enviar a mensagem visto que os dados são guardados externamente num banco de dados
        chatAtivo = model.start_chat(history = history)
        response = await chatAtivo.send_message_async(data.message)
        
        userMsg = MessageDB(chatID = data.chatID, role = "user", text = data.message)
        db.add(userMsg)
        
        modelMsg = MessageDB(chatID = data.chatID, role = "model", text = response.text)
        db.add(modelMsg)
        
        db.commit()
        
        return {"response": response.text}
    
    except Exception as e:

        db.rollback()
        raise HTTPException(status_code = 500, detail = str(e))

# rota que devolve o histórico para o front-end
@app.get("/chat/history/{chatID}")
async def getHistory(chatID: str, db: Session = Depends(get_db)):

    chat = db.query(ChatDB).filter(ChatDB.id == chatID).first()

    if not chat:

        raise HTTPException(status_code = 404, detail = "Chat não encontrado")
    
    frontEndHistory = []

    for msg in chat.messages:

        frontEndRole = "Você" if msg.role == "user" else "Professor"

        frontEndHistory.append({

            "role": frontEndRole,
            "text": msg.text
        })
        
    return {"history": frontEndHistory}