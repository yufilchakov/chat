from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    """Модель данных для сообщения в чате."""
    user_id: str
    content: str
    message_type: str
    filename: Optional[str] = None
    file_content: Optional[str] = None
