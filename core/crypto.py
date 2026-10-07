from cryptography.fernet import Fernet
from .config import settings


# 用 .env 里的密钥构造加密器
def _fernet() -> Fernet:
    return Fernet(settings.encrypt_key.encode())


# 加密：原文 → 密文字符串
def encrypt_password(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


# 解密：密文字符串 → 原文
def decrypt_password(cipher: str) -> str:
    return _fernet().decrypt(cipher.encode()).decode()
