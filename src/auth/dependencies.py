from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.models.api_key import ApiKey
from .service import decode_access_token, get_user_by_id, find_api_key

bearer_scheme = HTTPBearer(auto_error=False)

# Store the current API key on the request state for permission checks
_REQUEST_API_KEY_ATTR = "_bhapi_api_key"


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials

    # Try API key first (bhapi_ prefix)
    if token.startswith("bhapi_"):
        result = await find_api_key(db, token)
        if result is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        api_key, user = result
        # Store API key on request for permission checks
        request.state._bhapi_api_key = api_key
        return user

    # Try JWT
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await get_user_by_id(db, payload.get("sub", ""))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    # JWT users have full access (no API key restrictions)
    request.state._bhapi_api_key = None
    return user


def require_permission(scope: str):
    """Dependency factory that checks API key has the required scope.

    Scopes in api_key.permissions["scopes"] are checked. "*" grants all access.
    JWT-authenticated users bypass permission checks.
    """
    async def _check(request: Request, user: User = Depends(get_current_user)) -> User:
        api_key: ApiKey | None = getattr(request.state, _REQUEST_API_KEY_ATTR, None)
        if api_key is None:
            # JWT user — full access
            return user
        scopes = (api_key.permissions or {}).get("scopes", [])
        if "*" in scopes or not scopes:
            # Wildcard or empty scopes = full access (backward compatible)
            return user
        if scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key lacks required scope: {scope}",
            )
        return user
    return _check


async def require_auth(user: User = Depends(get_current_user)) -> User:
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return user
