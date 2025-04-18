import hashlib

from app.core.constants import APP_NAME, ENCODING

_KEY_BYTES = APP_NAME.encode(ENCODING)
_KEY_BYTES_LENGTH = len(_KEY_BYTES)


def encrypt(password: str) -> str:
    """Encrypt the password using PBKDF2-HMAC-SHA256.

    Args:
        password: The password to encrypt.

    Returns:
        The encrypted password.
    """
    salt = _KEY_BYTES
    hash = hashlib.pbkdf2_hmac("sha256", password.encode(ENCODING), salt, 100000)
    return hash.hex()


def xor(input_str: str) -> str:
    """Encrypt/Decrypt the input string using XOR operation.

    Args:
        input_str: The input string.

    Returns:
        The encrypted/decrypted string.
    """
    input_bytes = input_str.encode(ENCODING)
    output_bytes = bytearray()
    for i in range(len(input_bytes)):
        output_bytes.append(input_bytes[i] ^ _KEY_BYTES[i % _KEY_BYTES_LENGTH])
    return output_bytes.decode(ENCODING)
