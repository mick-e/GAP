from pydantic import BaseModel


class GitHubOAuthCallback(BaseModel):
    code: str


class OAuthUserInfo(BaseModel):
    login: str
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict | None = None
