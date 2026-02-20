import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import current_app


def _get_fernet():
    secret = current_app.config['SECRET_KEY'].encode()
    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'cv-creator-api-key-salt',
        info=b'api-key-encryption',
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret))
    return Fernet(key)


def encrypt_api_key(plaintext):
    f = _get_fernet()
    return f.encrypt(plaintext.encode())


def decrypt_api_key(ciphertext):
    f = _get_fernet()
    return f.decrypt(ciphertext).decode()
