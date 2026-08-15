import secrets
import string

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_token():
    # 12 base32-like characters: 60 bits of entropy, URL-safe and easy to type.
    return "".join(secrets.choice(ALPHABET) for _ in range(12))


def format_code(token):
    return f"{token[:4]}-{token[4:8]}-{token[8:]}"


def generate_delete_secret():
    return secrets.token_urlsafe(32)
