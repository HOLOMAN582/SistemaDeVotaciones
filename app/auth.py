from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from secrets import compare_digest, token_bytes
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings

ALGORITHM = "HS256"
HASH_ITERATIONS = 310_000
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = pbkdf2_hmac("sha256", password.encode(), salt, HASH_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded_password: str | None) -> bool:
    if not encoded_password or "$" not in encoded_password:
        return False
    salt_hex, digest_hex = encoded_password.split("$", maxsplit=1)
    try:
        expected = bytes.fromhex(digest_hex)
        actual = pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), HASH_ITERATIONS)
    except ValueError:
        return False
    return compare_digest(actual, expected)


def create_access_token(subject: str, role: str, voter_id: int | None = None) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    claims: dict[str, Any] = {"sub": subject, "role": role, "exp": expires_at}
    if voter_id is not None:
        claims["voter_id"] = voter_id
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=ALGORITHM)


def authenticate_admin(username: str, password: str) -> bool:
    settings = get_settings()
    return compare_digest(username, settings.admin_username) and compare_digest(password, settings.admin_password)


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Se requiere autenticación", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, get_settings().jwt_secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        role = payload.get("role")
        if not isinstance(subject, str) or role not in {"admin", "voter"}:
            raise JWTError
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido o expirado", headers={"WWW-Authenticate": "Bearer"}) from exc


def require_admin(principal: dict[str, Any] = Depends(get_principal)) -> dict[str, Any]:
    if principal.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol administrador")
    return principal


def require_voter(principal: dict[str, Any] = Depends(get_principal)) -> dict[str, Any]:
    if principal.get("role") != "voter":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol votante")
    return principal
