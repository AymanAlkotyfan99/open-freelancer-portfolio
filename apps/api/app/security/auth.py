import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from fastapi import Cookie, Depends, HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.models.entities import AdminUser

hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return hasher.verify(password_hash, password)
    except Exception:
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_token(subject: str, kind: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": kind,
        "iat": now,
        "exp": now + expires,
        "jti": secrets.token_urlsafe(12),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_token(token: str, kind: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        if payload.get("type") != kind:
            raise InvalidTokenError("Wrong token type")
        return payload
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        ) from exc


async def current_admin(
    access_token: str | None = Cookie(default=None), db: AsyncSession = Depends(get_db)
) -> AdminUser:
    if not access_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(access_token, "access")
    try:
        subject = UUID(str(payload["sub"]))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc
    user = await db.scalar(select(AdminUser).where(AdminUser.id == subject))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user
