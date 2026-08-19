import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_contact_validation(client):
    response = await client.post("/api/v1/contact", json={"full_name": "A"})
    assert response.status_code == 422
