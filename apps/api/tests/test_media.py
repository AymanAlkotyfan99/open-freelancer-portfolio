from io import BytesIO

import pytest

from app.api import portfolio
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.entities import Profile


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


@pytest.mark.asyncio
async def test_profile_photo_persists_in_local_development_storage(client, admin, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "")
    monkeypatch.setattr(settings, "cloudinary_api_key", "")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "")
    monkeypatch.setattr(settings, "local_media_dir", str(tmp_path))
    monkeypatch.setattr(settings, "api_public_url", "http://localhost:8000")
    async with SessionLocal() as db:
        db.add(
            Profile(
                name_en="Ayman Naeem",
                name_ar="أيمن نعيم",
                title_en="Software Engineer",
                title_ar="مهندس برمجيات",
                statement_en="Profile statement",
                statement_ar="نبذة شخصية",
                about_en="About profile",
                about_ar="عن الملف الشخصي",
                email="ayman@example.com",
                phone="+963000000000",
                location_en="Syria",
                location_ar="سوريا",
            )
        )
        await db.commit()

    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    uploaded = await client.post(
        "/api/v1/admin/profile/photo",
        files={"file": ("profile.png", BytesIO(png), "image/png")},
        data={"alt_text_en": "Profile portrait", "alt_text_ar": "الصورة الشخصية"},
    )
    assert uploaded.status_code == 200
    result = uploaded.json()
    assert result["profile_image_url"].startswith("http://localhost:8000/uploads/")
    relative = result["profile_image_public_id"].removeprefix("local:")
    saved_file = tmp_path / relative
    assert saved_file.read_bytes() == png
    assert (await client.get("/api/v1/profile")).json()["profile_image_url"] == result["profile_image_url"]

    deleted = await client.delete("/api/v1/admin/profile/photo")
    assert deleted.status_code == 204
    assert not saved_file.exists()
