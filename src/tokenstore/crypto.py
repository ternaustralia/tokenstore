import base64
import binascii

from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from flask import current_app


def init_app(app):
    crypto = CryptoTool(app.config)
    app.extensions["crypto"] = crypto


class CryptoTool:

    def __init__(self, config):
        keys = [
            self._validate_key(key.strip())
            for key in
            config.get('CRYPTOKEY').split(',')
            if key.strip()
        ]
        self.fernet = MultiFernet(
            Fernet(base64.urlsafe_b64encode(key)) for key in keys
        )

    def _validate_key(self, key):
        # key raw(32bytes), base64(44bytes), hex(64bytes)
        if isinstance(key, str):
            key = key.encode("ascii")
        if len(key) == 44:
            # base64 encoded
            try:
                key = base64.b64decode(key)
            except ValueError:
                pass
        elif len(key) == 64:
            try:
                return binascii.a2b_hex(key)
            except ValueError:
                pass
        if len(key) != 32:
            raise ValueError("Encryption keys must be be 32 bytes")
        return key

    def encrypt(self, data):
        # need binary / bytes to encrypt
        return self.fernet.encrypt(data.encode('utf-8'))

    # TODO: this may throw an InvalidToken Exception?
    def decrypt(self, data):
        return self.fernet.decrypt(data).decode('utf-8')


def encrypt(data):
    return current_app.extensions["crypto"].encrypt(data)


def decrypt(data):
    return current_app.extensions["crypto"].decrypt(data)
