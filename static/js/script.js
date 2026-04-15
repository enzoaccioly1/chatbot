let currentChat = null;
let isTyping = false;
const emptyState = `
    <div class="emptyChatContainer">
        <span class="emptyChatIcon" aria-hidden="true">📜</span>
        <h2>Comece uma nova pesquisa histórica.</h2>
        <p>Qual período ou evento você gostaria de explorar hoje?</p>
                    
        <div class="suggestionChips">
            <button onclick="fillInput('Quais foram as causas da Revolução Francesa?')">Revolução Francesa</button>
            <button onclick="fillInput('Como a Peste Negra mudou a sociedade europeia?')">Peste Negra</button>
            <button onclick="fillInput('Explique a corrida espacial durante a Guerra Fria.')">Guerra Fria</button>
        </div>
    </div>
`;

// inicia a aplicação
async function initApp(){

    const res = await fetch('/chat/list');
    const data = await res.json();

    const lastChat = localStorage.getItem('lastChat');
    
    if (data.chats && data.chats.length > 0){

        const chatToOpen = data.chats.includes(lastChat) ? lastChat : data.chats[0];
        apiSwitchChat(chatToOpen);
    }
    else{

        showWelcomeScreen(); 
    }
}

// welcome screen caso não haja chats criados
function showWelcomeScreen(){

    currentChat = null;
    
    const win = document.getElementById('chatWindow');
    document.getElementById('currentChatHeader').innerText = "Bem-vindo, Historiador";

    win.innerHTML = emptyState;
}

// reloga a sidebar de chats
async function apiLoadChats(){

    const res = await fetch('/chat/list');
    const data = await res.json();
    const listDiv = document.getElementById('chatList');
    listDiv.innerHTML = '';
    
    data.chats.forEach(name => {

        const item = document.createElement('div');

        item.className = `chatItem ${name === currentChat ? 'active' : ''}`;
        item.onclick = () => apiSwitchChat(name);

        item.innerHTML = `
            <span>${name}</span>
            <button class="btnDel" onclick="event.stopPropagation(); apiDeleteChat('${name}')">×</button>
        `;

        listDiv.appendChild(item);
    });
}

// cria um novo chat
async function apiCreateChat(){

    const name = document.getElementById('chatNameInput').value;

    if (!name) return;

    await fetch('/chat/new', {

        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ chatID: name })
    });

    document.getElementById('chatNameInput').value = '';

    if (!isTyping) {
        apiSwitchChat(name);
    }
}

// deleta o chat, se não houver mais chats mostra a welcome screen
async function apiDeleteChat(name){

    // caso a IA esteja pensando, bloqueia ações
    if (isTyping){

        alert("Aguarde o Professor concluir o raciocínio antes de excluir o chat.");
        return;
    }

    if (confirm(`Excluir chat "${name}"?`)){

        try{
            
            const res = await fetch(`/chat/delete/${name}`, { method: 'DELETE' });
            const data = await res.json();

            if (currentChat === name){

                currentChat = null;
            }

            if (data.chats && data.chats.length > 0){

                if (currentChat === null){

                    apiSwitchChat(data.chats[0]);
                }
                else{

                    apiLoadChats();
                }
            }
            else{

                showWelcomeScreen();
                apiLoadChats();
            }
        }
        catch(error){

            console.error("Erro ao deletar chat:", error);
        }
    }
}

// troca o chat, levando em consideração o histórico
async function apiSwitchChat(name){

    // caso a IA esteja pensando, bloqueia ações
    if (isTyping){

        alert("Aguarde o Professor concluir o raciocínio antes de trocar o chat.");
        return;
    }

    currentChat = name;
    localStorage.setItem('lastChat', name);

    document.getElementById('currentChatHeader').innerText = `${name}`;
    
    const win = document.getElementById('chatWindow');
    win.innerHTML = '';

    try{

        const res = await fetch(`/chat/history/${name}`);
        const data = await res.json();

        if(data.history && data.history.length > 0){


        }
        else{

            win.innerHTML = emptyState;
        }
            data.history.forEach(msg => {

                appendMsg(msg.role, msg.text);
            });
    }
    catch (e){

        console.error("Erro ao carregar histórico:", e);
    }

    apiLoadChats();
}

// enviar mensagem com 'enter'
document.getElementById('userInput').addEventListener('keydown', function(event){

    if (event.key === 'Enter'){

        event.preventDefault(); 
        apiSendMessage();
    }
});

// cria um chat novo se não existir e manda a mensagem
async function apiSendMessage(){

    // caso a IA esteja pensando, bloqueia ações
    if (isTyping) return;

    const input = document.getElementById('userInput');
    const msg = input.value;
    if (!msg) return;

    if (!currentChat || currentChat === "Bem-vindo, Historiador"){

        const autoName = msg.split(' ').slice(0, 2).join(' ') || "Novo Chat";
        const finalName = `${autoName} (${new Date().toLocaleTimeString()})`;
        
        await fetch('/chat/new', {

            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ chatID: finalName })
        });

        currentChat = finalName;
        document.getElementById('currentChatHeader').innerText = `${currentChat}`;
        document.getElementById('chatWindow').innerHTML = '';

        apiLoadChats();
    }

    isTyping = true;
    input.disabled = true;

    const emptyStateWindow = document.querySelector('.empty-chat-container');

    if (emptyStateWindow){

        emptyStateWindow.remove();
    }

    appendMsg('Você', msg);
    input.value = '';

    document.title = "Respondendo...";

    // loading cursor da IA
    const win = document.getElementById('chatWindow');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'messageBubble botMsg loadingCursor';
    loadingDiv.innerHTML = `<strong>Professor</strong><br>Pensando...`;
    win.appendChild(loadingDiv);
    win.scrollTop = win.scrollHeight;

    try{

        const res = await fetch('/chat/send', {

            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ chatID: currentChat, message: msg })
        });

        const data = await res.json();

        // remove o loading cursor
        win.removeChild(loadingDiv);
        
        if (data.response){

            appendMsg('Professor', data.response);
        }
        else{

            appendMsg('Professor', "Lamento, houve um erro na historiografia desta resposta.");
        }
    }
    catch(error){

        console.error("Erro ao enviar:", error);
        appendMsg('Professor', "Erro de conexão com o servidor.");
    }
    finally{

        isTyping = false;
        input.disabled = false;
        input.focus();
        document.title = "Chatbot de Historiografia";
    }
}

// faz as mensagens aparecerem em formato de bolha e também formata a resposta
function appendMsg(role, text){

    const win = document.getElementById('chatWindow');
    const msgDiv = document.createElement('div');
    
    msgDiv.className = `messageBubble ${role === 'Você' ? 'userMsg' : 'botMsg'}`;

    let htmlContent = marked.parse(text);

    msgDiv.innerHTML = `<strong>${role}</strong><br>${htmlContent}`;
    win.appendChild(msgDiv);
    win.scrollTop = win.scrollHeight;
}

// botões de sugestão preencherem o userInput
function fillInput(text){

    const input = document.getElementById('userInput');
    input.value = text;

    apiSendMessage();
}

initApp();