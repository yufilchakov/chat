from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.responses import HTMLResponse
from app.services.chat_service import ChatService
from app.models.message import Message
from fastapi.templating import Jinja2Templates
from fastapi import Request
import json

router = APIRouter()
chat_service = ChatService()
templates = Jinja2Templates(directory='templates')

connected_users = {}


@router.get('/', response_class=HTMLResponse)
async def get(request: Request):
    """Обработчик GET-запроса для корневого маршрута."""
    return templates.TemplateResponse('index.html', {'request': request})


@router.websocket('/ws/{user_id}')
async def websocket_endpoint(user_id: str, websocket: WebSocket):
    """Обработчик WebSocket-соединения для пользователей чата."""
    await websocket.accept()
    connected_users[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message_data['user_id'] = user_id
            message_data['message_type'] = message_data.get('type', 'text')

            message = Message(**message_data)
            
            if message.message_type == 'text':
                filtered_message = chat_service.filter_profanity(message.content)
                await broadcast(f'{user_id}: {filtered_message}')
            elif message.message_type == 'file':
                file_link = (f'<a href="data:application/octet-stream;base64,{message.file_content}" '
                             f'download="{message.filename}">Скачать {message.filename}</a>')
                await broadcast(file_link)
    except WebSocketDisconnect:
        del connected_users[user_id]


async def broadcast(message: str):
    """Рассылает сообщение всем подключенным пользователям."""
    for connection in connected_users.values():
        await connection.send_text(message)
