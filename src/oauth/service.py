import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.auth.service import create_access_token, hash_password

logger = logging.getLogger(__name__)


async def exchange_code_for_token(
    code: str, client_id: str, client_secret: str
) -> str:
    """Exchange GitHub OAuth code for an access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(
                f"GitHub OAuth error: {data.get('error_description', data['error'])}"
            )
        return data["access_token"]


async def get_github_user(token: str):
    """Get GitHub user info using an access token."""
    from .schemas import OAuthUserInfo

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        # Get primary email if not public
        email = data.get("email")
        if not email:
            email_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if email_resp.status_code == 200:
                emails = email_resp.json()
                for e in emails:
                    if e.get("primary") and e.get("verified"):
                        email = e["email"]
                        break

        return OAuthUserInfo(
            login=data["login"],
            email=email,
            name=data.get("name"),
            avatar_url=data.get("avatar_url"),
        )


async def get_or_create_user(
    db: AsyncSession, github_user
) -> User:
    """Find existing user by github_id or email, or create a new one."""
    # Try to find by github_id first
    result = await db.execute(
        select(User).where(User.github_id == github_user.login)
    )
    user = result.scalar_one_or_none()
    if user:
        # Update avatar if changed
        if github_user.avatar_url and user.avatar_url != github_user.avatar_url:
            user.avatar_url = github_user.avatar_url
            user.updated_at = datetime.now(timezone.utc)
            await db.commit()
        return user

    # Try to find by email
    if github_user.email:
        result = await db.execute(
            select(User).where(User.email == github_user.email)
        )
        user = result.scalar_one_or_none()
        if user:
            # Link GitHub account to existing user
            user.github_id = github_user.login
            user.avatar_url = github_user.avatar_url
            user.auth_provider = "github"
            user.updated_at = datetime.now(timezone.utc)
            await db.commit()
            return user

    # Create new user
    email = github_user.email or f"{github_user.login}@github.oauth"
    user = User(
        email=email,
        hashed_password=hash_password(f"oauth_{github_user.login}_{datetime.now(timezone.utc).isoformat()}"),
        name=github_user.name or github_user.login,
        github_id=github_user.login,
        avatar_url=github_user.avatar_url,
        auth_provider="github",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
