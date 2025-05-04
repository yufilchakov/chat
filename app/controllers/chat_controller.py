from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import ValidationError
from starlette.responses import HTMLResponse
from app.services.chat_service import ChatService
from app.models.message import Message
from fastapi.templating import Jinja2Templates
from fastapi import Request
import json
from app.services.chat_manager import ConnectionManager
from app.depends import get_connection_manager

router = APIRouter()
templates = Jinja2Templates(directory='templates')
connection_manager = ConnectionManager()


@router.get('/', response_class=HTMLResponse)
async def get(request: Request):
    """Обработчик GET-запроса для корневого маршрута."""
    return templates.TemplateResponse('index.html', {'request': request})


@router.websocket('/ws/{user_id}')
async def websocket_endpoint(
        user_id: str,
        websocket: WebSocket,
        chat_service: ChatService = Depends(ChatService),
        conn_manager: ConnectionManager = Depends(get_connection_manager)
):
    """Обработчик WebSocket-соединения для пользователей чата."""
    await conn_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message = Message(**message_data)
            
            if message.message_type == 'text':
                filtered_message = chat_service.filter_profanity(message.content)
                await conn_manager.broadcast(f'{user_id}: {filtered_message}')
            elif message.message_type == 'file':
                file_link = (f'<a href="data:application/octet-stream;base64,{message.file_content}" '
                             f'download="{message.filename}">Скачать {message.filename}</a>')
                await conn_manager.broadcast(file_link)
    except WebSocketDisconnect:
        conn_manager.disconnect(user_id)
    except ValidationError as e:
        await websocket.send_text(f'Ошибка: {e.json()}')
