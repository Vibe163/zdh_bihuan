from core.crypto import encrypt_password, decrypt_password


# 加密再解密，应拿回原文
def test_roundtrip():
    raw = "mypassword123"
    assert decrypt_password(encrypt_password(raw)) == raw


# 密文不应等于原文
def test_changes():
    raw = "abc123456"
    assert encrypt_password(raw) != raw
