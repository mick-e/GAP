import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.user import User
from src.models.api_key import ApiKey


def _get_settings():
    return get_settings()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
    return f"{salt}${hashed}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, stored_hash = hashed.split("$", 1)
        computed = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100000).hex()
        return secrets.compare_digest(computed, stored_hash)
    except (ValueError, AttributeError):
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    settings = _get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    settings = _get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str, str]:
    """Returns (raw_key, hashed_key, prefix)."""
    raw = f"gap_{secrets.token_urlsafe(32)}"
    prefix = raw[:10]
    hashed = hash_password(raw)
    return raw, hashed, prefix


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, email: str, password: str, name: str | None = None
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        name=name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def find_api_key(db: AsyncSession, raw_key: str) -> tuple[ApiKey, User] | None:
    prefix = raw_key[:10]
    result = await db.execute(select(ApiKey).where(ApiKey.prefix == prefix))
    keys = result.scalars().all()
    for key in keys:
        if verify_password(raw_key, key.hashed_key):
            key.last_used_at = datetime.now(timezone.utc)
            await db.commit()
            user = await get_user_by_id(db, key.user_id)
            if user:
                return key, user
    return None
