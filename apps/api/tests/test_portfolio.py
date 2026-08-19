from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models.entities import AuditLog, ProjectRequest


def project_payload(**changes):
    value = {
        "slug": "minimum-project",
        "title_en": "Minimum project",
        "title_ar": "مشروع بالحد الأدنى",
        "summary_en": "A complete project description.",
        "summary_ar": "وصف كامل للمشروع.",
        "technologies": ["FastAPI"],
    }
    value.update(changes)
    return value


def service_payload(**changes):
    value = {
        "slug": "api-development",
        "title_en": "API Development",
        "title_ar": "تطوير واجهات API",
        "description_en": "Backend API design and implementation.",
        "description_ar": "تصميم وتنفيذ واجهات الأنظمة الخلفية.",
        "related_skills": ["FastAPI"],
        "publication_status": "published",
    }
    value.update(changes)
    return value


def package_payload(package_type="basic", price="100.00", **changes):
    value = {
        "package_type": package_type,
        "name_en": package_type.title(),
        "name_ar": {"basic": "أساسية", "standard": "قياسية", "premium": "مميزة"}[package_type],
        "price": price,
        "currency": "USD",
        "delivery_days": 7,
        "revisions": 2,
        "included_deliverables_en": ["Source code"],
        "included_deliverables_ar": ["الشيفرة المصدرية"],
    }
    value.update(changes)
    return value


def request_payload(service_id=None, package_id=None, **changes):
    value = {
        "client_name": "Client Name",
        "email": "client@example.com",
        "preferred_contact_method": "email",
        "service_id": service_id,
        "package_id": package_id,
        "displayed_price": "0.01",
        "currency": "FAKE",
        "delivery_days": 999,
        "project_title": "New client project",
        "project_description": "A sufficiently detailed description of the requested project.",
        "expected_deliverables": "Working application",
        "consent": True,
    }
    value.update(changes)
    return value


@pytest.mark.asyncio
async def test_project_minimum_fields_and_optional_media(client, admin):
    response = await client.post("/api/v1/admin/projects", json=project_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["technologies"] == ["FastAPI"]
    assert body["cover_url"] is None
    assert body["media"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("missing", ["title_en", "title_ar", "summary_en", "summary_ar", "technologies"])
async def test_project_rejects_missing_minimum_fields(client, admin, missing):
    payload = project_payload()
    payload.pop(missing)
    response = await client.post("/api/v1/admin/projects", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_project_rejects_empty_skills(client, admin):
    response = await client.post("/api/v1/admin/projects", json=project_payload(technologies=[]))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_three_packages_duplicate_and_limit(client, admin):
    service = (await client.post("/api/v1/admin/services", json=service_payload())).json()
    ids = []
    for package_type in ("basic", "standard", "premium"):
        response = await client.post(f"/api/v1/admin/services/{service['id']}/packages", json=package_payload(package_type))
        assert response.status_code == 201
        ids.append(response.json()["id"])
    duplicate = await client.post(f"/api/v1/admin/services/{service['id']}/packages", json=package_payload("basic"))
    assert duplicate.status_code == 409
    disabled = await client.patch(f"/api/v1/admin/packages/{ids[0]}", json=package_payload("basic", is_active=False))
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("value_type", "values"),
    [
        ("boolean", lambda package_id: {"package_id": package_id, "value_boolean": True}),
        ("number", lambda package_id: {"package_id": package_id, "value_number": 3}),
        ("text", lambda package_id: {"package_id": package_id, "value_text_en": "Included", "value_text_ar": "مشمول"}),
    ],
)
async def test_dynamic_feature_value_types(client, admin, value_type, values):
    service = (await client.post("/api/v1/admin/services", json=service_payload(slug=f"feature-{value_type}"))).json()
    package = (await client.post(f"/api/v1/admin/services/{service['id']}/packages", json=package_payload())).json()
    response = await client.post(
        f"/api/v1/admin/services/{service['id']}/features",
        json={"name_en": "Feature", "name_ar": "ميزة", "value_type": value_type, "values": [values(package["id"])]},
    )
    assert response.status_code == 201
    assert response.json()["values"]


@pytest.mark.asyncio
async def test_package_request_uses_database_snapshot_and_stays_immutable(client, admin):
    service = (await client.post("/api/v1/admin/services", json=service_payload())).json()
    package = (await client.post(f"/api/v1/admin/services/{service['id']}/packages", json=package_payload(price="425.00"))).json()
    response = await client.post("/api/v1/project-requests", json=request_payload(service["id"], package["id"]))
    assert response.status_code == 201
    reference = response.json()["reference"]
    await client.patch(f"/api/v1/admin/packages/{package['id']}", json=package_payload(price="900.00"))
    async with SessionLocal() as db:
        saved = await db.scalar(select(ProjectRequest).where(ProjectRequest.reference == reference))
        assert saved is not None
        assert saved.price_snapshot == Decimal("425.00")
        assert saved.currency_snapshot == "USD"
        assert saved.delivery_days_snapshot == 7
        assert saved.included_items_snapshot == ["Source code"]


@pytest.mark.asyncio
async def test_request_rejects_inactive_package_and_unpublished_service(client, admin):
    service = (await client.post("/api/v1/admin/services", json=service_payload())).json()
    package = (await client.post(f"/api/v1/admin/services/{service['id']}/packages", json=package_payload(is_active=False))).json()
    inactive = await client.post("/api/v1/project-requests", json=request_payload(service["id"], package["id"]))
    assert inactive.status_code == 422
    draft_service = (await client.post("/api/v1/admin/services", json=service_payload(slug="draft-service", publication_status="draft"))).json()
    draft_package = (await client.post(f"/api/v1/admin/services/{draft_service['id']}/packages", json=package_payload())).json()
    unpublished = await client.post("/api/v1/project-requests", json=request_payload(draft_service["id"], draft_package["id"]))
    assert unpublished.status_code == 422


@pytest.mark.asyncio
async def test_custom_offer_has_no_price_snapshot(client, admin):
    response = await client.post("/api/v1/custom-offer-requests", json=request_payload(package_id=None, service_id=None))
    assert response.status_code == 201
    async with SessionLocal() as db:
        saved = await db.scalar(select(ProjectRequest).where(ProjectRequest.reference == response.json()["reference"]))
        assert saved is not None
        assert saved.request_type == "custom"
        assert saved.price_snapshot is None


@pytest.mark.asyncio
async def test_admin_authentication_required(client):
    response = await client.get("/api/v1/admin/overview")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_mutations_create_audit_log(client, admin):
    response = await client.post("/api/v1/admin/projects", json=project_payload())
    assert response.status_code == 201
    async with SessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(AuditLog)) == 1


@pytest.mark.asyncio
async def test_service_faqs_and_related_projects(client, admin):
    service = (await client.post("/api/v1/admin/services", json=service_payload())).json()
    project = (
        await client.post(
            "/api/v1/admin/projects",
            json=project_payload(publication_status="published"),
        )
    ).json()
    faq = await client.post(
        f"/api/v1/admin/services/{service['id']}/faqs",
        json={
            "question_en": "What is included?",
            "question_ar": "ما الذي تتضمنه الخدمة؟",
            "answer_en": "Architecture and implementation.",
            "answer_ar": "المعمارية والتنفيذ.",
        },
    )
    assert faq.status_code == 201
    linked = await client.post(
        f"/api/v1/admin/services/{service['id']}/related-projects",
        json={"project_id": project["id"]},
    )
    assert linked.status_code == 201
    public = await client.get(f"/api/v1/services/{service['slug']}")
    assert public.status_code == 200
    assert public.json()["faqs"][0]["question_en"] == "What is included?"
    assert public.json()["related_projects"][0]["id"] == project["id"]
    assert (
        await client.delete(f"/api/v1/admin/service-faqs/{faq.json()['id']}")
    ).status_code == 204
    assert (
        await client.delete(
            f"/api/v1/admin/services/{service['id']}/related-projects/{project['id']}"
        )
    ).status_code == 204
