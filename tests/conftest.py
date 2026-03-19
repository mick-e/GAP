import pytest
import os

# Force test env vars BEFORE any imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gap.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["GITHUB_TOKEN"] = "ghp_test_token_for_testing"
os.environ["GITHUB_ORG"] = "test-org"

from src.config import get_settings
get_settings.cache_clear()

from src.middleware import limiter  # noqa: E402

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402

from src.database import Base, get_db  # noqa: E402
import src.models  # noqa: F401, E402 - populate metadata

engine = create_async_engine("sqlite+aiosqlite:///./test_gap.db", echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    # Reset rate limiter between tests so auth fixtures aren't blocked
    limiter.reset()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db():
    async with TestSession() as session:
        yield session


@pytest.fixture
async def client(db):
    from src.main import app

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(client, db):
    """Client with authenticated user."""
    await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123",
    })
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
