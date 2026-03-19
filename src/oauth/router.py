from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_db
from src.auth.service import create_access_token
from .schemas import GitHubOAuthCallback, OAuthTokenResponse
from .service import exchange_code_for_token, get_github_user, get_or_create_user

router = APIRouter(prefix="/api/v1/oauth", tags=["oauth"])

GITHUB_SCOPES = "read:user user:email"


@router.get("/github/authorize")
async def github_authorize():
    """Return the GitHub OAuth authorization URL."""
    settings = get_settings()
    if not settings.github_client_id:
        raise HTTPException(
            status_code=501, detail="GitHub OAuth is not configured"
        )
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&scope={GITHUB_SCOPES}"
    )
    return {"url": url}


@router.post("/github/callback", response_model=OAuthTokenResponse)
async def github_callback(
    body: GitHubOAuthCallback,
    db: AsyncSession = Depends(get_db),
):
    """Exchange GitHub OAuth code for a JWT token."""
    settings = get_settings()
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=501, detail="GitHub OAuth is not configured"
        )

    try:
        gh_token = await exchange_code_for_token(
            body.code, settings.github_client_id, settings.github_client_secret
        )
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        github_user = await get_github_user(gh_token)
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch GitHub user info: {e}"
        )

    user = await get_or_create_user(db, github_user)
    token = create_access_token({"sub": user.id})
    return OAuthTokenResponse(
        access_token=token,
        user={"email": user.email, "name": user.name},
    )


@router.get("/github/status")
async def github_status():
    """Check if GitHub OAuth is configured."""
    settings = get_settings()
    return {"github_enabled": bool(settings.github_client_id)}
