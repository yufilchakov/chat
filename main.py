from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import json
import base64
from better_profanity import Profanity

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

profanity = Profanity()
profanity.load_censor_words()

connected_users = {}

key = os.urandom(32)
iv = os.urandom(16)


def encrypt_message(message: str) -> str:
    """Шифрует сообщение с использованием AES-256."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_message(encrypted_message: str) -> str:
    """Дешифрует сообщение с использованием AES-256."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    encrypted_data = base64.b64decode(encrypted_message)
    decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
    return decrypted.decode('utf-8')


def filter_profanity(message: str) -> str:
    """Фильтрует нецензурную лексику в сообщении."""
    return profanity.censor(message)


@app.get('/', response_class=HTMLResponse)
async def get():
    """Возвращает HTML-страницу для чата."""
    return '''<!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <input id='userId' placeholder='Введите свой id' />
        <input id='message' placeholder='Введите сообщение' />
        <input type='file' id='fileInput' />
        <button onclick='sendMessage()'>Отправить</button>
        <div id='chat'></div>

        <script>
            const userId = document.getElementById('userId');
            const messageInput = document.getElementById('message');
            const fileInput = document.getElementById('fileInput');
            const chat = document.getElementById('chat');
            let websocket;

            function connect() {
                websocket = new WebSocket(`ws://localhost:8000/ws/${userId.value}`);
                websocket.onmessage = (event) => {
                    const message = document.createElement('div');
                    message.innerHTML = event.data;
                    chat.appendChild(message);
                };
            }

            function sendMessage() {
                if (websocket) {
                    const message = messageInput.value;
                    if (message) {
                        websocket.send(JSON.stringify({ type: 'text', content: message }));
                        messageInput.value = '';
                    }

                    const file = fileInput.files[0];
                    if (file) {
                        const reader = new FileReader();
                        reader.onload = function(event) {
                            const base64Data = event.target.result.split(',')[1];
                            websocket.send(JSON.stringify({ type: 'file', content: base64Data, filename: file.name }));
                            fileInput.value = '';
                        };
                        reader.readAsDataURL(file);
                    }
                }
            }

            userId.addEventListener('change', connect);
        </script>
    </body>
    </html>'''


@app.websocket('/ws/{user_id}')
async def websocket_endpoint(user_id: str, websocket: WebSocket):
    """Обрабатывает WebSocket соединения."""
    await websocket.accept()
    connected_users[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'text':
                await broadcast(f'{user_id}: {message['content']}')
            elif message['type'] == 'file':
                file_link = (f'<a href="data:application/octet-stream;base64,{message['content']}" '
                             f'download="{message['filename']}">Скачать {message['filename']}</a>')
                await broadcast(file_link)
    except WebSocketDisconnect:
        del connected_users[user_id]


async def broadcast(message: str):
    """Отправляет сообщение всем подключенным пользователям через WebSocket."""
    for connection in connected_users.values():
        await connection.send_text(message)


if __name__ == '__main__':
    import uvicorn
    
    uvicorn.run(app, host='0.0.0.0', port=8000)
