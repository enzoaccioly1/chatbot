# Chatbot (agente) professor de História

Um chatbot que utiliza a API do Google Gemini para simular um professor de história, capaz de debater historiografia e contextos históricos de diversas áreas do conhecimento.

---

## 🚀 Funcionalidades

- **Chat Persistente**
- **Contexto Histórico**
- **Interface Moderna**
- **Suporte para Markdown**

## 🛠️ Tecnologias Utilizadas

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.9+)
- **IA:** [Google Generative AI (Gemini)](https://ai.google.dev/)
- **Frontend:** HTML5, CSS3 e JavaScript
- **Servidor:** Uvicorn

## 📋 Pré-requisitos

- [Python 3.9 ou superior](https://www.python.org/downloads/)
- Uma chave de API do Google Gemini ([Google AI Studio](https://aistudio.google.com/))

## 🔧 Instalação e Configuração

1. **Clone o repositório:**

```bash
git clone https://github.com/seu-usuario/nome-do-seu-repositorio.git
cd chatbot
```

2. **Instale as dependências:**

```bash
pip install fastapi uvicorn google-generativeai python-dotenv
```

3. **Configure as variáveis de ambiente:**

Crie um arquivo chamado ```.env``` na raiz do projeto e adicione sua chave da API:

```bash
GEMINIKEY=SUACHAVEAQUI
```

### ⚠️ Não vaze sua chave:

Em caso de compartilhamento, crie também um arquivo chamado ```.gitignore``` na raiz e escreva ```.env``` dentro dele, para impedir que o Git envie sua chave para o repositório público.

### 💡 Dica (ao criar sua chave):

Não se esqueça de adicionar um faturamento ao projeto para que a chave seja utilizável.

## 🏃 Como Executar

```bash
uvicorn main:app --reload
```

Em seguida, acesse ```http://127.0.0.1:8000``` no seu navegador

### 💡 Dica (se der algum erro de comando não reconhecido): 

Dependendo de como o Python foi instalado (especialmente no Windows), o terminal pode não reconhecer comandos de pacotes Python. Se isso acontecer, você pode forçar a execução através do módulo do Python usando ```py -m``` ou ```python -m```, por exemplo:

```bash
py -m uvicorn main:app --reload
#ou
python -m uvicorn main:app --reload
```

