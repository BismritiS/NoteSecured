import hashlib
import secrets


def generate_salt() -> str:
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def create_password_record(password: str) -> dict:
    salt = generate_salt()
    password_hash = hash_password(password, salt)
    return {
        "salt": salt,
        "password_hash": password_hash
    }


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    return hash_password(password, salt) == stored_hash