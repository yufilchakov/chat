from better_profanity import Profanity


class ChatService:
    """Сервис для обработки чата, включая фильтрацию нецензурной лексики."""
    def __init__(self):
        self.profanity = Profanity()
        self.profanity.load_censor_words()

    def filter_profanity(self, message: str) -> str:
        """Фильтрует нецензурную лексику в сообщении."""
        return self.profanity.censor(message)
