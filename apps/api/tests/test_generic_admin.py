import pytest


@pytest.mark.asyncio
async def test_generic_admin_updates_and_deletes_uuid_records(client, admin):
    created = await client.post(
        "/api/v1/admin/education",
        json={
            "institution_en": "Damascus University",
            "institution_ar": "جامعة دمشق",
            "title_en": "Software Engineering",
            "title_ar": "هندسة البرمجيات",
            "description_en": "Initial description",
            "description_ar": "الوصف الأولي",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert created.status_code == 201
    education_id = created.json()["id"]

    updated = await client.patch(
        f"/api/v1/admin/education/{education_id}",
        json={"description_en": "Updated description", "sort_order": 2},
    )
    assert updated.status_code == 200
    assert updated.json()["description_en"] == "Updated description"
    assert updated.json()["sort_order"] == 2

    deleted = await client.delete(f"/api/v1/admin/education/{education_id}")
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_generic_admin_rejects_malformed_uuid(client, admin):
    response = await client.patch(
        "/api/v1/admin/education/not-a-uuid",
        json={"description_en": "Updated description"},
    )
    assert response.status_code == 422
