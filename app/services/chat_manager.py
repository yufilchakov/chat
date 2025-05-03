from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    """Менеджер для работы с WebSocket соединениями."""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Устанавливает новое WebSocket соединение для пользователя."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        """Закрывает WebSocket соединение для указанного пользователя."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        """Отправляет личное сообщение указанному пользователю."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except Exception:
                self.disconnect(user_id)

    async def broadcast(self, message: str):
        """Отправляет сообщение всем подключенным пользователям."""
        disconnected_users = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception:
                disconnected_users.append(user_id)
                
        for user_id in disconnected_users:
            self.disconnect(user_id)
