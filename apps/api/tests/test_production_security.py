from io import BytesIO

import pytest
from fastapi.routing import APIRoute
from httpx import AsyncClient
from pydantic import ValidationError
from starlette.datastructures import Headers, UploadFile

from app.api import router as legacy_router
from app.core.config import Settings, settings
from app.main import app
from app.security.auth import current_admin
from app.services.media import validate_attachment


def production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": "production",
        "database_url": "postgresql://portfolio:password@database.internal/portfolio?sslmode=require",
        "frontend_url": "https://portfolio.example.test",
        "cors_origins": "https://portfolio.example.test",
        "api_public_url": "https://api.example.test",
        "trusted_hosts": "api.example.test,api.railway.internal",
        "trust_proxy_headers": True,
        "jwt_secret_key": "unit-test-random-looking-secret-that-is-not-used-anywhere",
        "cloudinary_cloud_name": "test-cloud",
        "cloudinary_api_key": "test-key",
        "cloudinary_api_secret": "test-secret",
        "turnstile_secret_key": "test-turnstile-secret",
        "turnstile_expected_hostnames": "portfolio.example.test",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[call-arg]


def test_provider_database_url_is_normalized_for_asyncpg() -> None:
    configured = production_settings()
    assert configured.database_url.startswith("postgresql+asyncpg://")
    assert "ssl=require" in configured.database_url
    assert "sslmode=" not in configured.database_url


def test_production_rejects_placeholder_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="unique production secret"):
        production_settings(jwt_secret_key="replace-with-at-least-32-random-characters")


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"trusted_hosts": "*.example.test"}, "exact hostnames"),
        ({"trust_proxy_headers": False}, "enabled behind Railway"),
        ({"turnstile_expected_hostnames": "other.example.test"}, "FRONTEND_URL hostname"),
        ({"cookie_domain": ".up.railway.app"}, "blank for Railway-generated domains"),
    ],
)
def test_production_rejects_unsafe_domain_or_proxy_configuration(
    override: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        production_settings(**override)


def test_every_admin_route_has_backend_authentication() -> None:
    unprotected: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/v1/admin"):
            continue
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        if current_admin not in dependency_calls:
            unprotected.append(f"{','.join(sorted(route.methods or []))} {route.path}")
    assert unprotected == []


@pytest.mark.asyncio
async def test_request_attachments_are_not_publicly_listable(client: AsyncClient) -> None:
    response = await client.get("/api/v1/project-request-attachments")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_production_admin_mutations_require_an_allowed_origin(
    client: AsyncClient, admin: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    response = await client.post("/api/v1/admin/projects", json={})
    assert response.status_code == 403
    assert response.json() == {"detail": "Request origin is not allowed"}


@pytest.mark.asyncio
async def test_invalid_docx_container_is_rejected() -> None:
    upload = UploadFile(
        BytesIO(b"PK" + b"not-a-real-zip"),
        filename="proposal.docx",
        headers=Headers(
            {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        ),
    )
    with pytest.raises(Exception) as caught:
        await validate_attachment(upload)
    assert getattr(caught.value, "status_code", None) == 422


@pytest.mark.asyncio
async def test_contact_email_html_escapes_user_content(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: dict[str, str] = {}

    def capture(subject: str, body: str, recipient: str | None = None) -> bool:
        sent.update(subject=subject, body=body)
        return True

    monkeypatch.setattr(legacy_router, "send_email", capture)
    response = await client.post(
        "/api/v1/contact",
        json={
            "full_name": "<b>Client Name</b>",
            "email": "client@example.com",
            "subject": "<img src=x onerror=alert(1)>",
            "message": "A sufficiently long message with <script>alert(1)</script> content.",
            "preferred_contact": "email",
            "consent": True,
            "turnstile_token": "",
            "website": "",
        },
    )
    assert response.status_code == 201
    assert "<script>" not in sent["body"]
    assert "&lt;script&gt;" in sent["body"]
