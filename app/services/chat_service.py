from better_profanity import Profanity
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64


class ChatService:
    """Сервис для обработки чата, включая фильтрацию нецензурной лексики и шифрование сообщения."""
    def __init__(self, key: bytes = None):
        self.profanity = Profanity()
        
        if key is None:
            self.key = AESGCM.generate_key(bit_length=256)
        else:
            if len(key) != 32:
                raise ValueError('Для AES-256 ключ должен иметь длину 32 байта (256 бит).')
            self.key = key
        self.aesgcm = AESGCM(self.key)
    
    def load_censor_words(self) -> None:
        """Загружает слова для цензуры."""
        self.profanity.load_censor_words()
    
    def filter_profanity(self, message: str) -> str:
        """Фильтрует нецензурную лексику в сообщении."""
        return self.profanity.censor(message)
    
    def encrypt_message(self, message: str) -> str:
        """Шифрование сообщение с помощью AES-256 GCM."""
        nonce = os.urandom(12)
        data = message.encode('utf-8')
        ct = self.aesgcm.encrypt(nonce, data, None)
        encrypted = nonce + ct
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_message(self, encrypted_message: str) -> str:
        """Расшифровывает сообщение, зашифрованное AES-256 GCM."""
        encrypted_data = base64.b64decode(encrypted_message)
        nonce = encrypted_data[:12]
        ct = encrypted_data[12:]
        decrypted = self.aesgcm.decrypt(nonce, ct, None)
        return decrypted.decode('utf-8')
