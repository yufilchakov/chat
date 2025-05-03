from pydantic import BaseModel, Field


class Message(BaseModel):
    """Модель данных для сообщения в чате."""
    user_id: str
    content: str
    message_type: str = Field(default='text', alias='type')
    filename: str | None = None
    file_content: str | None = None
