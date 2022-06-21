import base64
import binascii

import pytest

from tokenstore.crypto import CryptoTool

def test_str_key():
    config = {
        "CRYPTOKEY": "1"*32
    }
    crypto = CryptoTool(config)


def test_base64_key():
    config = {
        "CRYPTOKEY": base64.b64encode(b"1"*32).decode()
    }
    crypto = CryptoTool(config)


def test_invalid_base64_key():
    config = {
        "CRYPTOKEY": "b%"*22
    }
    with pytest.raises(ValueError):
        crypto = CryptoTool(config)


def test_bin_key():
    config = {
        "CRYPTOKEY": binascii.b2a_hex(b"1"*32).decode()
    }
    crypto = CryptoTool(config)


def test_invalid_bin_key():
    config = {
        "CRYPTOKEY": "g"*64
    }
    with pytest.raises(ValueError):
        crypto = CryptoTool(config)


def test_invalid_length():
    config = {
        "CRYPTOKEY": "1"*30
    }
    with pytest.raises(ValueError):
        crypto = CryptoTool(config)