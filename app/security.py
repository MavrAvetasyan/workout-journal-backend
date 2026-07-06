from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, LOGIN_CODE_LENGTH, SECRET_KEY


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 100_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{iterations}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        iterations_raw, salt_raw, digest_raw = password_hash.split("$", 2)
    except ValueError:
        return False

    iterations = int(iterations_raw)
    salt = base64.b64decode(salt_raw.encode())
    expected = base64.b64decode(digest_raw.encode())
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def create_access_token(user_id: str, email: str) -> str:
    now = utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generate_login_code() -> str:
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(LOGIN_CODE_LENGTH))


def hash_login_code(email: str, code: str) -> str:
    normalized_email = email.strip().lower()
    payload = f"{normalized_email}:{code}".encode("utf-8")
    return hmac.new(SECRET_KEY.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_login_code(email: str, code: str, expected_hash: str) -> bool:
    actual_hash = hash_login_code(email=email, code=code)
    return hmac.compare_digest(actual_hash, expected_hash)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
