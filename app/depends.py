from app.services.chat_manager import ConnectionManager


connection_manager = ConnectionManager()


def get_connection_manager():
    """Функция для получения экземпляра ConnectionManager."""
    return connection_manager
