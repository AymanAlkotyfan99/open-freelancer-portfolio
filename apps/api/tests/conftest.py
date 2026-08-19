import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

import pytest
from httpx import ASGITransport, AsyncClient

from app.database.session import SessionLocal, engine
from app.main import app
from app.models import Base
from app.models.entities import AdminUser
from app.security.auth import current_admin, hash_password
from app.services.integrations import _hits


@pytest.fixture(autouse=True)
async def database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    _hits.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def admin():
    async with SessionLocal() as db:
        row = AdminUser(email="admin@example.com", password_hash=hash_password("StrongPassword123!"))
        db.add(row)
        await db.commit()
        await db.refresh(row)
        async def override_admin():
            return row
        app.dependency_overrides[current_admin] = override_admin
        yield row


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value
