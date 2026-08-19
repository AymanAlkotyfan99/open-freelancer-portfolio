import pytest

from app.database.session import SessionLocal
from app.models.entities import AdminUser
from app.security.auth import hash_password


@pytest.mark.asyncio
async def test_cookie_session_resolves_uuid_subject(client):
    async with SessionLocal() as db:
        db.add(
            AdminUser(
                email="session@example.com",
                password_hash=hash_password("StrongPassword123!"),
            )
        )
        await db.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "session@example.com", "password": "StrongPassword123!"},
    )
    assert login.status_code == 200
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "session@example.com"

    client.cookies.delete("access_token")
    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert (await client.get("/api/v1/auth/me")).status_code == 200
