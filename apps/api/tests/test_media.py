from io import BytesIO

import pytest

from app.api import portfolio


def project_payload():
    return {
        "slug": "media-project", "title_en": "Media project", "title_ar": "مشروع وسائط",
        "summary_en": "Project media validation.", "summary_ar": "التحقق من وسائط المشروع.",
        "technologies": ["FastAPI"],
    }


@pytest.mark.asyncio
async def test_multiple_images_video_cover_reorder_and_safe_delete(client, admin, monkeypatch):
    counter = {"value": 0, "destroyed": []}
    async def fake_upload(content, media_type, folder, **kwargs):
        counter["value"] += 1
        return {"secure_url": f"https://res.cloudinary.com/demo/{media_type}-{counter['value']}", "public_id": f"asset-{counter['value']}", "width": 100, "height": 100}
    async def fake_destroy(public_id, media_type):
        counter["destroyed"].append((public_id, media_type))
    monkeypatch.setattr(portfolio, "upload_media", fake_upload)
    monkeypatch.setattr(portfolio, "destroy_media", fake_destroy)
    project = (await client.post("/api/v1/admin/projects", json=project_payload())).json()
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    image_one = await client.post(f"/api/v1/admin/projects/{project['id']}/media", files={"file": ("one.png", BytesIO(png), "image/png")})
    image_two = await client.post(f"/api/v1/admin/projects/{project['id']}/media", files={"file": ("two.png", BytesIO(png), "image/png")})
    mp4 = b"\x00\x00\x00\x18ftypisom" + b"0" * 100
    video = await client.post(f"/api/v1/admin/projects/{project['id']}/media", files={"file": ("demo.mp4", BytesIO(mp4), "video/mp4")})
    assert [image_one.status_code, image_two.status_code, video.status_code] == [201, 201, 201]
    ids = [video.json()["id"], image_two.json()["id"], image_one.json()["id"]]
    reorder = await client.post(f"/api/v1/admin/projects/{project['id']}/media/reorder", json={"ids": ids})
    assert reorder.status_code == 200
    cover = await client.post(f"/api/v1/admin/projects/{project['id']}/cover?media_id={image_two.json()['id']}")
    assert cover.status_code == 200
    assert cover.json()["is_cover"] is True
    deleted = await client.delete(f"/api/v1/admin/project-media/{image_one.json()['id']}")
    assert deleted.status_code == 204
    assert counter["destroyed"] == [("asset-1", "image")]


@pytest.mark.asyncio
async def test_upload_security_rejects_mismatched_content(client, admin):
    project = (await client.post("/api/v1/admin/projects", json=project_payload())).json()
    response = await client.post(
        f"/api/v1/admin/projects/{project['id']}/media",
        files={"file": ("attack.png", BytesIO(b"not a png"), "image/png")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_service_cover_upload_and_reference_safe_delete(client, admin, monkeypatch):
    destroyed = []

    async def fake_upload(content, media_type, folder, **kwargs):
        return {
            "secure_url": "https://res.cloudinary.com/demo/service-cover.webp",
            "public_id": "service-cover",
            "width": 1200,
            "height": 800,
        }

    async def fake_destroy(public_id, media_type):
        destroyed.append((public_id, media_type))

    monkeypatch.setattr(portfolio, "upload_media", fake_upload)
    monkeypatch.setattr(portfolio, "destroy_media", fake_destroy)
    service = (
        await client.post(
            "/api/v1/admin/services",
            json={
                "slug": "cover-service",
                "title_en": "Cover service",
                "title_ar": "خدمة الغلاف",
                "description_en": "Service cover validation.",
                "description_ar": "التحقق من غلاف الخدمة.",
                "related_skills": ["Cloudinary"],
            },
        )
    ).json()
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    uploaded = await client.post(
        f"/api/v1/admin/services/{service['id']}/cover",
        files={"file": ("cover.png", BytesIO(png), "image/png")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["cover_image_public_id"] == "service-cover"
    deleted = await client.delete(f"/api/v1/admin/services/{service['id']}/cover")
    assert deleted.status_code == 204
    assert destroyed == [("service-cover", "image")]
