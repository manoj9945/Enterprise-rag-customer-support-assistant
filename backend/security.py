import os, hashlib, hmac
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

SECRET = os.getenv("JWT_SECRET", "local-demo-secret-change-me")
ALGORITHM = "HS256"

def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180_000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        calculated = hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
        return hmac.compare_digest(calculated, digest_hex)
    except Exception:
        return False

def create_access_token(subject: str, role: str = "admin") -> str:
    payload = {"sub": subject, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None
