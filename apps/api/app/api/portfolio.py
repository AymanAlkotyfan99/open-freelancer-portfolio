import csv
import html
import io
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.entities import (
    AdminUser,
    AuditLog,
    ContactMessage,
    MediaAsset,
    PackageFeatureValue,
    Profile,
    Project,
    ProjectMedia,
    ProjectRequest,
    ProjectRequestAttachment,
    ProjectTechnology,
    Service,
    ServiceFAQ,
    ServiceFeature,
    ServicePackage,
    ServiceProjectLink,
)
from app.schemas.portfolio import (
    ExternalMediaIn,
    FAQIn,
    FeatureIn,
    MediaPatch,
    PackageIn,
    PackagePatch,
    PackageRequestIn,
    ProfilePatch,
    ProjectIn,
    ProjectPatch,
    RelatedProjectIn,
    ReorderIn,
    RequestStatusPatch,
    ServiceIn,
    ServicePatch,
)
from app.security.auth import current_admin
from app.services.integrations import client_ip, enforce_rate_limit, send_email, verify_turnstile
from app.services.media import destroy_media, private_attachment_url, upload_media, validate_media

router = APIRouter()


def row_dict(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def page_data(items: list[Any], total: int, page: int, page_size: int) -> dict[str, Any]:
    return {
        "items": [row_dict(item) if not isinstance(item, dict) else item for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size,
    }


def audit(admin: AdminUser, action: str, entity_type: str, entity_id: Any, request: Request) -> AuditLog:
    return AuditLog(
        admin_id=admin.id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        request_id=getattr(request.state, "request_id", None),
    )


async def project_payload(db: AsyncSession, project: Project) -> dict[str, Any]:
    technologies = (
        await db.scalars(
            select(ProjectTechnology)
            .where(ProjectTechnology.project_id == project.id, ProjectTechnology.deleted_at.is_(None))
            .order_by(ProjectTechnology.sort_order)
        )
    ).all()
    media = (
        await db.scalars(
            select(ProjectMedia)
            .where(ProjectMedia.project_id == project.id, ProjectMedia.deleted_at.is_(None))
            .order_by(ProjectMedia.sort_order)
        )
    ).all()
    result = row_dict(project)
    result["technologies"] = [item.name for item in technologies]
    result["media"] = [row_dict(item) for item in media]
    return result


async def project_payloads(
    db: AsyncSession, projects: list[Project]
) -> list[dict[str, Any]]:
    """Serialize a project collection with two bounded association queries."""
    if not projects:
        return []
    project_ids = [project.id for project in projects]
    technologies = (
        await db.scalars(
            select(ProjectTechnology)
            .where(
                ProjectTechnology.project_id.in_(project_ids),
                ProjectTechnology.deleted_at.is_(None),
            )
            .order_by(ProjectTechnology.sort_order)
        )
    ).all()
    media = (
        await db.scalars(
            select(ProjectMedia)
            .where(
                ProjectMedia.project_id.in_(project_ids),
                ProjectMedia.deleted_at.is_(None),
            )
            .order_by(ProjectMedia.sort_order)
        )
    ).all()
    technologies_by_project: dict[Any, list[str]] = {}
    media_by_project: dict[Any, list[dict[str, Any]]] = {}
    for technology in technologies:
        technologies_by_project.setdefault(technology.project_id, []).append(
            technology.name
        )
    for media_item in media:
        media_by_project.setdefault(media_item.project_id, []).append(
            row_dict(media_item)
        )
    return [
        {
            **row_dict(project),
            "technologies": technologies_by_project.get(project.id, []),
            "media": media_by_project.get(project.id, []),
        }
        for project in projects
    ]


async def service_summaries(
    db: AsyncSession, services: list[Service]
) -> list[dict[str, Any]]:
    """Serialize service cards without an N+1 package query."""
    if not services:
        return []
    packages = (
        await db.scalars(
            select(ServicePackage)
            .where(
                ServicePackage.service_id.in_([service.id for service in services]),
                ServicePackage.deleted_at.is_(None),
            )
            .order_by(ServicePackage.display_order, ServicePackage.package_type)
        )
    ).all()
    packages_by_service: dict[Any, list[ServicePackage]] = {}
    for package in packages:
        packages_by_service.setdefault(package.service_id, []).append(package)
    results: list[dict[str, Any]] = []
    for service in services:
        service_packages = packages_by_service.get(service.id, [])
        active = [package for package in service_packages if package.is_active]
        results.append(
            {
                **row_dict(service),
                "packages": [row_dict(package) for package in service_packages],
                "starting_price": min(
                    (package.price for package in active), default=None
                ),
                "shortest_delivery_days": min(
                    (package.delivery_days for package in active), default=None
                ),
            }
        )
    return results


async def service_payload(db: AsyncSession, service: Service, full: bool = False) -> dict[str, Any]:
    packages = (
        await db.scalars(
            select(ServicePackage)
            .where(ServicePackage.service_id == service.id, ServicePackage.deleted_at.is_(None))
            .order_by(ServicePackage.display_order, ServicePackage.package_type)
        )
    ).all()
    result = row_dict(service)
    result["packages"] = [row_dict(package) for package in packages]
    active = [package for package in packages if package.is_active]
    result["starting_price"] = min((package.price for package in active), default=None)
    result["shortest_delivery_days"] = min(
        (package.delivery_days for package in active), default=None
    )
    if full:
        result["comparison"] = await comparison_payload(db, service.id, list(packages))
        faqs = (
            await db.scalars(
                select(ServiceFAQ)
                .where(ServiceFAQ.service_id == service.id, ServiceFAQ.is_active.is_(True))
                .order_by(ServiceFAQ.sort_order)
            )
        ).all()
        result["faqs"] = [row_dict(faq) for faq in faqs]
        links = (
            await db.scalars(
                select(ServiceProjectLink)
                .where(ServiceProjectLink.service_id == service.id)
                .order_by(ServiceProjectLink.sort_order)
            )
        ).all()
        projects = []
        for link in links:
            project = await db.get(Project, link.project_id)
            if project and project.publication_status == "published" and project.deleted_at is None:
                projects.append(await project_payload(db, project))
        result["related_projects"] = projects
    return result


async def comparison_payload(
    db: AsyncSession, service_id: UUID, packages: list[ServicePackage] | None = None
) -> dict[str, Any]:
    if packages is None:
        packages = list(
            (
                await db.scalars(
                    select(ServicePackage)
                    .where(ServicePackage.service_id == service_id, ServicePackage.deleted_at.is_(None))
                    .order_by(ServicePackage.display_order)
                )
            ).all()
        )
    features = (
        await db.scalars(
            select(ServiceFeature)
            .where(
                ServiceFeature.service_id == service_id,
                ServiceFeature.deleted_at.is_(None),
                ServiceFeature.is_active.is_(True),
            )
            .order_by(ServiceFeature.sort_order)
        )
    ).all()
    values = (
        await db.scalars(
            select(PackageFeatureValue).where(
                PackageFeatureValue.feature_id.in_([feature.id for feature in features])
            )
        )
    ).all() if features else []
    by_feature: dict[Any, list[dict[str, Any]]] = {}
    for value in values:
        by_feature.setdefault(value.feature_id, []).append(row_dict(value))
    return {
        "packages": [row_dict(package) for package in packages if package.is_active],
        "features": [
            {**row_dict(feature), "values": by_feature.get(feature.id, [])} for feature in features
        ],
    }


@router.get("/projects")
async def public_projects(
    search: str = "",
    skill: str = "",
    category: str = "",
    status: str = "",
    sort: str = Query("newest", pattern="^(newest|featured)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    paginated: bool = True,
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(Project).where(
        Project.publication_status == "published",
        Project.is_active.is_(True),
        Project.deleted_at.is_(None),
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(Project.title_en.ilike(term), Project.title_ar.ilike(term), Project.summary_en.ilike(term), Project.summary_ar.ilike(term)))
    if category:
        query = query.where(Project.category == category)
    if status:
        term = f"%{status.strip()}%"
        query = query.where(or_(Project.status_en.ilike(term), Project.status_ar.ilike(term)))
    if skill:
        project_ids = select(ProjectTechnology.project_id).where(ProjectTechnology.name.ilike(f"%{skill.strip()}%"))
        query = query.where(Project.id.in_(project_ids))
    query = (
        query.order_by(desc(Project.is_featured), desc(Project.project_date), desc(Project.created_at))
        if sort == "featured"
        else query.order_by(desc(Project.project_date), desc(Project.created_at))
    )
    count = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list((await db.scalars(query.offset((page - 1) * page_size).limit(page_size))).all())
    items = await project_payloads(db, rows)
    return page_data(items, count, page, page_size) if paginated else items


@router.get("/projects/{slug}")
async def public_project(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.scalar(
        select(Project).where(
            Project.slug == slug,
            Project.publication_status == "published",
            Project.is_active.is_(True),
            Project.deleted_at.is_(None),
        )
    )
    if not project:
        raise HTTPException(404, "Project not found")
    return await project_payload(db, project)


@router.get("/services")
async def public_services(
    search: str = "",
    skill: str = "",
    category: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    paginated: bool = True,
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(Service).where(
        Service.publication_status == "published",
        Service.availability_status == "available",
        Service.is_active.is_(True),
        Service.deleted_at.is_(None),
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(Service.title_en.ilike(term), Service.title_ar.ilike(term), Service.description_en.ilike(term), Service.description_ar.ilike(term)))
    if category:
        query = query.where(Service.category == category)
    if skill:
        # related_skills is JSON on both supported databases; filtering the bounded
        # page in Python keeps matching portable while count remains honest below.
        page_size_for_query = 50
    else:
        page_size_for_query = page_size
    rows = list((await db.scalars(query.order_by(desc(Service.is_featured), Service.sort_order).offset((page - 1) * page_size_for_query).limit(page_size_for_query))).all())
    items = await service_summaries(db, rows)
    if skill:
        lowered = skill.lower()
        items = [item for item in items if any(lowered in str(value).lower() for value in item["related_skills"])]
    count = len(items) if skill else (await db.scalar(select(func.count()).select_from(query.subquery())) or 0)
    return page_data(items, count, page, page_size) if paginated else items


@router.get("/services/{slug}")
async def public_service(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    service = await db.scalar(
        select(Service).where(
            Service.slug == slug,
            Service.publication_status == "published",
            Service.is_active.is_(True),
            Service.deleted_at.is_(None),
        )
    )
    if not service:
        raise HTTPException(404, "Service not found")
    return await service_payload(db, service, full=True)


@router.get("/services/{slug}/packages")
async def public_packages(slug: str, db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    service = await db.scalar(select(Service).where(Service.slug == slug, Service.publication_status == "published"))
    if not service:
        raise HTTPException(404, "Service not found")
    packages = (
        await db.scalars(
            select(ServicePackage).where(ServicePackage.service_id == service.id, ServicePackage.is_active.is_(True), ServicePackage.deleted_at.is_(None)).order_by(ServicePackage.display_order)
        )
    ).all()
    return [row_dict(package) for package in packages]


@router.get("/services/{slug}/comparison")
async def public_comparison(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    service = await db.scalar(select(Service).where(Service.slug == slug, Service.publication_status == "published"))
    if not service:
        raise HTTPException(404, "Service not found")
    return await comparison_payload(db, service.id)


async def create_request(
    payload: PackageRequestIn,
    request: Request,
    db: AsyncSession,
    *,
    custom: bool,
) -> dict[str, str]:
    enforce_rate_limit(request, "custom-offer" if custom else "package-request", 3, 300)
    if payload.website:
        return {"message": "Request received", "reference": "PENDING"}
    await verify_turnstile(payload.turnstile_token, client_ip(request))
    service: Service | None = None
    package: ServicePackage | None = None
    feature_snapshot: list[dict[str, Any]] = []
    if payload.service_id:
        service = await db.scalar(
            select(Service).where(Service.id == payload.service_id).with_for_update()
        )
        if not service or service.deleted_at or service.publication_status != "published" or service.availability_status != "available" or not service.is_active:
            raise HTTPException(422, "The selected service is not currently available")
    if not custom:
        if not service or not payload.package_id:
            raise HTTPException(422, "A published service and active package are required")
        package = await db.scalar(
            select(ServicePackage).where(ServicePackage.id == payload.package_id).with_for_update()
        )
        if not package or package.service_id != service.id or package.deleted_at or not package.is_active:
            raise HTTPException(422, "The selected package is not currently available")
        comparison = await comparison_payload(db, service.id, [package])
        for feature in comparison["features"]:
            value = next((item for item in feature["values"] if item["package_id"] == package.id), None)
            feature_snapshot.append({
                "name_en": feature["name_en"],
                "name_ar": feature["name_ar"],
                "value_type": feature["value_type"],
                "value": None if not value else value.get(f"value_{feature['value_type']}") if feature["value_type"] != "text" else {"en": value.get("value_text_en"), "ar": value.get("value_text_ar")},
            })
    if payload.reference_project_id:
        reference_project = await db.scalar(
            select(Project).where(
                Project.id == payload.reference_project_id,
                Project.publication_status == "published",
                Project.is_active.is_(True),
                Project.deleted_at.is_(None),
            )
        )
        if not reference_project:
            raise HTTPException(422, "The reference project is not available")
    reference = f"AN-{secrets.token_urlsafe(8).replace('-', '').replace('_', '').upper()[:10]}"
    row = ProjectRequest(
        reference=reference,
        client_name=payload.client_name,
        email=str(payload.email),
        company=payload.company_name,
        company_name=payload.company_name,
        phone=payload.phone,
        whatsapp=payload.whatsapp,
        telegram=payload.telegram,
        preferred_contact=payload.preferred_contact_method,
        preferred_contact_method=payload.preferred_contact_method,
        request_type="custom" if custom else "package",
        service_id=service.id if service else None,
        package_id=package.id if package else None,
        reference_project_id=payload.reference_project_id,
        requested_service=service.title_en if service else "Custom offer",
        service_name_snapshot=service.title_en if service else "Custom offer",
        package_name_snapshot=package.name_en if package else None,
        price_snapshot=package.price if package else None,
        currency_snapshot=package.currency if package else None,
        delivery_days_snapshot=package.delivery_days if package else None,
        revisions_snapshot=None if not package or package.unlimited_revisions else package.revisions,
        package_features_snapshot=feature_snapshot,
        included_items_snapshot=package.included_deliverables_en if package else [],
        excluded_items_snapshot=package.excluded_items_en if package else [],
        project_title=payload.project_title,
        description=payload.project_description,
        deliverables=payload.expected_deliverables,
        expected_deliverables=payload.expected_deliverables,
        preferred_start_date=payload.preferred_start_date,
        status="new",
    )
    db.add(row)
    await db.commit()
    delivered = send_email(
        f"New {'custom offer' if custom else 'package'} request {reference}",
        f"<h2>{html.escape(payload.project_title)}</h2><p>{html.escape(payload.client_name)}</p>"
        f"<p>{html.escape(payload.project_description)}</p>",
    )
    row.email_delivered = delivered
    await db.commit()
    return {"message": "Request received", "reference": reference}


@router.post("/project-requests", status_code=201)
async def package_request(payload: PackageRequestIn, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    return await create_request(payload, request, db, custom=False)


@router.post("/custom-offer-requests", status_code=201)
async def custom_offer(payload: PackageRequestIn, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    return await create_request(payload, request, db, custom=True)


@router.get("/admin/overview")
async def overview(_: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    async def count(model: Any, *conditions: Any) -> int:
        return int(await db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0)
    recent = list((await db.scalars(select(ProjectRequest).order_by(ProjectRequest.created_at.desc()).limit(5))).all())
    return {
        "published_projects": await count(Project, Project.publication_status == "published", Project.deleted_at.is_(None)),
        "draft_projects": await count(Project, Project.publication_status == "draft", Project.deleted_at.is_(None)),
        "active_services": await count(Service, Service.is_active.is_(True), Service.deleted_at.is_(None)),
        "new_requests": await count(ProjectRequest, ProjectRequest.status == "new"),
        "unread_messages": await count(ContactMessage, ContactMessage.status == "new"),
        "recent_requests": [row_dict(item) for item in recent],
    }


@router.get("/admin/projects")
async def admin_projects(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str = "",
    _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(Project).where(Project.deleted_at.is_(None))
    if search:
        query = query.where(or_(Project.title_en.ilike(f"%{search}%"), Project.title_ar.ilike(f"%{search}%")))
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list((await db.scalars(query.order_by(Project.sort_order, desc(Project.created_at)).offset((page - 1) * page_size).limit(page_size))).all())
    return page_data(await project_payloads(db, rows), total, page, page_size)


async def replace_technologies(db: AsyncSession, project_id: UUID, names: list[str]) -> None:
    existing = (await db.scalars(select(ProjectTechnology).where(ProjectTechnology.project_id == project_id))).all()
    for item in existing:
        await db.delete(item)
    for order, name in enumerate(names):
        db.add(ProjectTechnology(project_id=project_id, name=name, sort_order=order))


@router.post("/admin/projects", status_code=201)
async def admin_create_project(payload: ProjectIn, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    data = payload.model_dump(exclude={"technologies"})
    data["content_en"] = {**data["content_en"], "technologies": payload.technologies}
    data["content_ar"] = {**data["content_ar"], "technologies": payload.technologies}
    project = Project(**data)
    db.add(project)
    try:
        await db.flush()
        await replace_technologies(db, project.id, payload.technologies)
        db.add(audit(admin, "create", "project", project.id, request))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "A project with this slug already exists") from exc
    return await project_payload(db, project)


@router.get("/admin/projects/{project_id}")
async def admin_project(project_id: UUID, _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project or project.deleted_at:
        raise HTTPException(404, "Project not found")
    return await project_payload(db, project)


@router.patch("/admin/projects/{project_id}")
async def admin_update_project(project_id: UUID, payload: ProjectPatch, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project or project.deleted_at:
        raise HTTPException(404, "Project not found")
    data = payload.model_dump(exclude_unset=True)
    technologies = data.pop("technologies", None)
    for key, value in data.items():
        setattr(project, key, value)
    if technologies is not None:
        if not technologies:
            raise HTTPException(422, "At least one skill or technology is required")
        await replace_technologies(db, project.id, technologies)
        project.content_en = {**project.content_en, "technologies": technologies}
        project.content_ar = {**project.content_ar, "technologies": technologies}
    if not all([project.title_en.strip(), project.title_ar.strip(), project.summary_en.strip(), project.summary_ar.strip()]):
        raise HTTPException(422, "English and Arabic names and descriptions are required")
    db.add(audit(admin, "update", "project", project.id, request))
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "A project with this slug already exists") from exc
    return await project_payload(db, project)


@router.delete("/admin/projects/{project_id}", status_code=204)
async def admin_delete_project(project_id: UUID, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> Response:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.deleted_at = datetime.now(timezone.utc)
    project.is_active = False
    project.publication_status = "archived"
    db.add(audit(admin, "archive", "project", project.id, request))
    await db.commit()
    return Response(status_code=204)


@router.post("/admin/projects/{project_id}/media", status_code=201)
async def upload_project_media(project_id: UUID, request: Request, file: UploadFile = File(...), admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    enforce_rate_limit(request, "admin-project-media", 20, 300)
    project = await db.get(Project, project_id)
    if not project or project.deleted_at:
        raise HTTPException(404, "Project not found")
    content, media_type = await validate_media(file)
    result = await upload_media(content, media_type, f"ayman-portfolio/projects/{project.slug}")
    last_order = await db.scalar(select(func.max(ProjectMedia.sort_order)).where(ProjectMedia.project_id == project.id))
    thumbnail = result.get("thumbnail_url")
    if media_type == "video" and not thumbnail:
        thumbnail = str(result["secure_url"]).replace("/upload/", "/upload/so_0,w_960,f_jpg/").rsplit(".", 1)[0] + ".jpg"
    media = ProjectMedia(
        project_id=project.id, media_type=media_type, source_type="upload",
        secure_url=result["secure_url"], cloudinary_public_id=result["public_id"],
        thumbnail_url=thumbnail, sort_order=(last_order or -1) + 1,
        alt_text_en=project.title_en if media_type == "image" else None,
        alt_text_ar=project.title_ar if media_type == "image" else None,
    )
    db.add(media)
    db.add(MediaAsset(
        cloudinary_public_id=result["public_id"], secure_url=result["secure_url"],
        resource_type=media_type, mime_type=file.content_type, size_bytes=len(content),
        width=result.get("width"), height=result.get("height"), duration_seconds=result.get("duration"),
    ))
    await db.flush()
    db.add(audit(admin, "upload", "project_media", media.id, request))
    await db.commit()
    return row_dict(media)


@router.post("/admin/projects/{project_id}/media/external", status_code=201)
async def add_external_media(project_id: UUID, payload: ExternalMediaIn, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    project = await db.get(Project, project_id)
    if not project or project.deleted_at:
        raise HTTPException(404, "Project not found")
    last_order = await db.scalar(select(func.max(ProjectMedia.sort_order)).where(ProjectMedia.project_id == project.id))
    media = ProjectMedia(project_id=project.id, media_type="video", source_type="external_url", secure_url=payload.url, sort_order=(last_order or -1) + 1, **payload.model_dump(exclude={"url"}))
    db.add(media)
    await db.flush()
    db.add(audit(admin, "create", "project_media", media.id, request))
    await db.commit()
    return row_dict(media)


@router.patch("/admin/project-media/{media_id}")
async def update_project_media(media_id: UUID, payload: MediaPatch, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    media = await db.get(ProjectMedia, media_id)
    if not media or media.deleted_at:
        raise HTTPException(404, "Media not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(media, key, value)
    db.add(audit(admin, "update", "project_media", media.id, request))
    await db.commit()
    await db.refresh(media)
    return row_dict(media)


async def public_id_in_use(db: AsyncSession, public_id: str, excluding_media: UUID | None = None) -> bool:
    media_query = select(func.count()).select_from(ProjectMedia).where(ProjectMedia.cloudinary_public_id == public_id, ProjectMedia.deleted_at.is_(None))
    if excluding_media:
        media_query = media_query.where(ProjectMedia.id != excluding_media)
    if await db.scalar(media_query):
        return True
    if await db.scalar(select(func.count()).select_from(Profile).where(Profile.profile_image_public_id == public_id)):
        return True
    if await db.scalar(select(func.count()).select_from(Service).where(Service.cover_image_public_id == public_id, Service.deleted_at.is_(None))):
        return True
    return bool(await db.scalar(select(func.count()).select_from(ProjectRequestAttachment).where(ProjectRequestAttachment.public_id == public_id, ProjectRequestAttachment.deleted_at.is_(None))))


@router.delete("/admin/project-media/{media_id}", status_code=204)
async def delete_project_media(media_id: UUID, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> Response:
    media = await db.get(ProjectMedia, media_id)
    if not media or media.deleted_at:
        raise HTTPException(404, "Media not found")
    media.deleted_at = datetime.now(timezone.utc)
    media.is_cover = False
    project = await db.get(Project, media.project_id)
    if project and project.cover_url == media.secure_url:
        project.cover_url = None
    db.add(audit(admin, "delete", "project_media", media.id, request))
    await db.commit()
    if media.cloudinary_public_id and not await public_id_in_use(db, media.cloudinary_public_id, media.id):
        await destroy_media(media.cloudinary_public_id, media.media_type)
        asset = await db.scalar(select(MediaAsset).where(MediaAsset.cloudinary_public_id == media.cloudinary_public_id))
        if asset:
            asset.is_active = False
            asset.deleted_at = datetime.now(timezone.utc)
            await db.commit()
    return Response(status_code=204)


@router.post("/admin/projects/{project_id}/media/reorder")
async def reorder_project_media(project_id: UUID, payload: ReorderIn, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    rows = list((await db.scalars(select(ProjectMedia).where(ProjectMedia.project_id == project_id, ProjectMedia.id.in_(payload.ids), ProjectMedia.deleted_at.is_(None)))).all())
    if len(rows) != len(payload.ids):
        raise HTTPException(422, "Every media item must belong to this project")
    by_id = {row.id: row for row in rows}
    for order, media_id in enumerate(payload.ids):
        by_id[media_id].sort_order = order
    db.add(audit(admin, "reorder", "project_media", project_id, request))
    await db.commit()
    return {"message": "Media reordered"}


@router.post("/admin/projects/{project_id}/cover")
async def select_project_cover(project_id: UUID, media_id: UUID, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    rows = list((await db.scalars(select(ProjectMedia).where(ProjectMedia.project_id == project_id, ProjectMedia.deleted_at.is_(None)))).all())
    selected = next((row for row in rows if row.id == media_id and row.media_type == "image"), None)
    if not selected:
        raise HTTPException(422, "The cover must be an image belonging to this project")
    for row in rows:
        row.is_cover = row.id == media_id
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.cover_url = selected.secure_url
    db.add(audit(admin, "set_cover", "project", project_id, request))
    await db.commit()
    await db.refresh(selected)
    return row_dict(selected)


@router.get("/admin/services")
async def admin_services(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str = "", _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    query = select(Service).where(Service.deleted_at.is_(None))
    if search:
        query = query.where(or_(Service.title_en.ilike(f"%{search}%"), Service.title_ar.ilike(f"%{search}%")))
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list((await db.scalars(query.order_by(Service.sort_order).offset((page - 1) * page_size).limit(page_size))).all())
    return page_data([await service_payload(db, row, full=True) for row in rows], total, page, page_size)


@router.post("/admin/services", status_code=201)
async def admin_create_service(payload: ServiceIn, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    service = Service(**payload.model_dump())
    db.add(service)
    try:
        await db.flush()
        db.add(audit(admin, "create", "service", service.id, request))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "A service with this slug already exists") from exc
    return await service_payload(db, service, full=True)


@router.get("/admin/services/{service_id}")
async def admin_service(service_id: UUID, _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    service = await db.get(Service, service_id)
    if not service or service.deleted_at:
        raise HTTPException(404, "Service not found")
    return await service_payload(db, service, full=True)


@router.patch("/admin/services/{service_id}")
async def admin_update_service(service_id: UUID, payload: ServicePatch, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    service = await db.get(Service, service_id)
    if not service or service.deleted_at:
        raise HTTPException(404, "Service not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    if not service.related_skills:
        raise HTTPException(422, "At least one related skill is required")
    db.add(audit(admin, "update", "service", service.id, request))
    await db.commit()
    return await service_payload(db, service, full=True)


@router.post("/admin/services/{service_id}/cover")
async def upload_service_cover(
    service_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    enforce_rate_limit(request, "admin-service-cover", 20, 300)
    service = await db.get(Service, service_id)
    if not service or service.deleted_at:
        raise HTTPException(404, "Service not found")
    content, media_type = await validate_media(file, allow_video=False)
    if media_type != "image":
        raise HTTPException(422, "Service covers must be images")
    result = await upload_media(
        content,
        "image",
        f"ayman-portfolio/services/{service.slug}",
        transformation=[
            {"width": 1800, "height": 1200, "crop": "limit", "quality": "auto", "fetch_format": "auto"}
        ],
    )
    old_public_id = service.cover_image_public_id
    service.cover_image_url = result["secure_url"]
    service.cover_image_public_id = result["public_id"]
    db.add(
        MediaAsset(
            cloudinary_public_id=result["public_id"],
            secure_url=result["secure_url"],
            resource_type="image",
            mime_type=file.content_type,
            size_bytes=len(content),
            width=result.get("width"),
            height=result.get("height"),
        )
    )
    db.add(audit(admin, "replace_cover", "service", service.id, request))
    await db.commit()
    await db.refresh(service)
    if old_public_id and not await public_id_in_use(db, old_public_id):
        await destroy_media(old_public_id, "image")
    return await service_payload(db, service, full=True)


@router.delete("/admin/services/{service_id}/cover", status_code=204)
async def delete_service_cover(
    service_id: UUID,
    request: Request,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = await db.get(Service, service_id)
    if not service or service.deleted_at:
        raise HTTPException(404, "Service not found")
    public_id = service.cover_image_public_id
    service.cover_image_url = None
    service.cover_image_public_id = None
    db.add(audit(admin, "delete_cover", "service", service.id, request))
    await db.commit()
    if public_id and not await public_id_in_use(db, public_id):
        await destroy_media(public_id, "image")
    return Response(status_code=204)


@router.post("/admin/services/{service_id}/faqs", status_code=201)
async def create_service_faq(
    service_id: UUID,
    payload: FAQIn,
    request: Request,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if not await db.get(Service, service_id):
        raise HTTPException(404, "Service not found")
    faq = ServiceFAQ(service_id=service_id, **payload.model_dump())
    db.add(faq)
    await db.flush()
    db.add(audit(admin, "create", "service_faq", faq.id, request))
    await db.commit()
    return row_dict(faq)


@router.patch("/admin/service-faqs/{faq_id}")
async def update_service_faq(
    faq_id: UUID,
    payload: FAQIn,
    request: Request,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    faq = await db.get(ServiceFAQ, faq_id)
    if not faq or faq.deleted_at:
        raise HTTPException(404, "FAQ not found")
    for key, value in payload.model_dump().items():
        setattr(faq, key, value)
    db.add(audit(admin, "update", "service_faq", faq.id, request))
    await db.commit()
    await db.refresh(faq)
    return row_dict(faq)


@router.delete("/admin/service-faqs/{faq_id}", status_code=204)
async def delete_service_faq(
    faq_id: UUID,
    request: Request,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    faq = await db.get(ServiceFAQ, faq_id)
    if not faq:
        raise HTTPException(404, "FAQ not found")
    faq.deleted_at = datetime.now(timezone.utc)
    faq.is_active = False
    db.add(audit(admin, "delete", "service_faq", faq.id, request))
    await db.commit()
    return Response(status_code=204)


@router.post("/admin/services/{service_id}/related-projects", status_code=201)
async def add_related_project(
    service_id: UUID,
    payload: RelatedProjectIn,
    request: Request,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = await db.get(Service, service_id)
    project = await db.get(Project, payload.project_id)
    if not service or service.deleted_at:
        raise HTTPException(404, "Service not found")
    if not project or project.deleted_at:
        raise HTTPException(404, "Project not found")
    link = ServiceProjectLink(service_id=service_id, **payload.model_dump())
    db.add(link)
    try:
        await db.flush()
        db.add(audit(admin, "link", "service_project", link.id, request))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "This project is already related to the service") from exc
    return {"id": link.id, "project": await project_payload(db, project)}


@router.delete("/admin/services/{service_id}/related-projects/{project_id}", status_code=204)
async def remove_related_project(
    service_id: UUID,
    project_id: UUID,
    request: Request,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    link = await db.scalar(
        select(ServiceProjectLink).where(
            ServiceProjectLink.service_id == service_id,
            ServiceProjectLink.project_id == project_id,
        )
    )
    if not link:
        raise HTTPException(404, "Related project not found")
    await db.delete(link)
    db.add(audit(admin, "unlink", "service_project", link.id, request))
    await db.commit()
    return Response(status_code=204)


@router.delete("/admin/services/{service_id}", status_code=204)
async def admin_delete_service(service_id: UUID, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> Response:
    service = await db.get(Service, service_id)
    if not service:
        raise HTTPException(404, "Service not found")
    service.deleted_at = datetime.now(timezone.utc)
    service.is_active = False
    service.publication_status = "archived"
    db.add(audit(admin, "archive", "service", service.id, request))
    await db.commit()
    return Response(status_code=204)


@router.get("/admin/services/{service_id}/packages")
async def admin_packages(service_id: UUID, _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    rows = (await db.scalars(select(ServicePackage).where(ServicePackage.service_id == service_id, ServicePackage.deleted_at.is_(None)).order_by(ServicePackage.display_order))).all()
    return [row_dict(row) for row in rows]


@router.post("/admin/services/{service_id}/packages", status_code=201)
async def admin_create_package(service_id: UUID, payload: PackageIn, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    if not await db.get(Service, service_id):
        raise HTTPException(404, "Service not found")
    count = await db.scalar(select(func.count()).select_from(ServicePackage).where(ServicePackage.service_id == service_id, ServicePackage.deleted_at.is_(None))) or 0
    if count >= 3:
        raise HTTPException(409, "A service can have no more than three package tiers")
    package = ServicePackage(service_id=service_id, **payload.model_dump())
    db.add(package)
    try:
        await db.flush()
        db.add(audit(admin, "create", "service_package", package.id, request))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "This package tier already exists for the service") from exc
    return row_dict(package)


@router.patch("/admin/packages/{package_id}")
async def admin_update_package(package_id: UUID, payload: PackagePatch, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    package = await db.get(ServicePackage, package_id)
    if not package or package.deleted_at:
        raise HTTPException(404, "Package not found")
    for key, value in payload.model_dump().items():
        setattr(package, key, value)
    db.add(audit(admin, "update", "service_package", package.id, request))
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "This package tier already exists for the service") from exc
    await db.refresh(package)
    return row_dict(package)


@router.delete("/admin/packages/{package_id}", status_code=204)
async def admin_delete_package(package_id: UUID, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> Response:
    package = await db.get(ServicePackage, package_id)
    if not package:
        raise HTTPException(404, "Package not found")
    referenced = await db.scalar(select(func.count()).select_from(ProjectRequest).where(ProjectRequest.package_id == package.id))
    if referenced:
        package.is_active = False
        package.deleted_at = datetime.now(timezone.utc)
    else:
        await db.delete(package)
    db.add(audit(admin, "delete", "service_package", package_id, request))
    await db.commit()
    return Response(status_code=204)


@router.post("/admin/services/{service_id}/features", status_code=201)
async def admin_create_feature(service_id: UUID, payload: FeatureIn, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    packages = list((await db.scalars(select(ServicePackage).where(ServicePackage.service_id == service_id, ServicePackage.deleted_at.is_(None)))).all())
    package_ids = {package.id for package in packages}
    if any(value.package_id not in package_ids for value in payload.values):
        raise HTTPException(422, "Feature values must reference packages from this service")
    feature = ServiceFeature(**payload.model_dump(exclude={"values"}), service_id=service_id)
    db.add(feature)
    await db.flush()
    for value in payload.values:
        db.add(PackageFeatureValue(feature_id=feature.id, **value.model_dump()))
    db.add(audit(admin, "create", "service_feature", feature.id, request))
    await db.commit()
    values = (await db.scalars(select(PackageFeatureValue).where(PackageFeatureValue.feature_id == feature.id))).all()
    return {**row_dict(feature), "values": [row_dict(value) for value in values]}


@router.patch("/admin/service-features/{feature_id}")
async def admin_update_feature(feature_id: UUID, payload: FeatureIn, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    feature = await db.get(ServiceFeature, feature_id)
    if not feature or feature.deleted_at:
        raise HTTPException(404, "Feature not found")
    for key, value in payload.model_dump(exclude={"values"}).items():
        setattr(feature, key, value)
    old_values = (await db.scalars(select(PackageFeatureValue).where(PackageFeatureValue.feature_id == feature.id))).all()
    for value in old_values:
        await db.delete(value)
    for value in payload.values:
        db.add(PackageFeatureValue(feature_id=feature.id, **value.model_dump()))
    db.add(audit(admin, "update", "service_feature", feature.id, request))
    await db.commit()
    return {**row_dict(feature), "values": [value.model_dump() for value in payload.values]}


@router.delete("/admin/service-features/{feature_id}", status_code=204)
async def admin_delete_feature(feature_id: UUID, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> Response:
    feature = await db.get(ServiceFeature, feature_id)
    if not feature:
        raise HTTPException(404, "Feature not found")
    await db.delete(feature)
    db.add(audit(admin, "delete", "service_feature", feature_id, request))
    await db.commit()
    return Response(status_code=204)


@router.post("/admin/services/{service_id}/features/reorder")
async def reorder_features(service_id: UUID, payload: ReorderIn, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    rows = list((await db.scalars(select(ServiceFeature).where(ServiceFeature.service_id == service_id, ServiceFeature.id.in_(payload.ids)))).all())
    if len(rows) != len(payload.ids):
        raise HTTPException(422, "Every feature must belong to this service")
    by_id = {row.id: row for row in rows}
    for order, feature_id in enumerate(payload.ids):
        by_id[feature_id].sort_order = order
    db.add(audit(admin, "reorder", "service_feature", service_id, request))
    await db.commit()
    return {"message": "Features reordered"}


@router.get("/admin/project-requests")
async def admin_requests(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str = "", status: str = "", _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    query = select(ProjectRequest)
    if search:
        term = f"%{search}%"
        query = query.where(or_(ProjectRequest.reference.ilike(term), ProjectRequest.client_name.ilike(term), ProjectRequest.email.ilike(term), ProjectRequest.service_name_snapshot.ilike(term)))
    if status:
        query = query.where(ProjectRequest.status == status)
    total = await db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = list((await db.scalars(query.order_by(desc(ProjectRequest.created_at)).offset((page - 1) * page_size).limit(page_size))).all())
    return page_data(rows, total, page, page_size)


@router.get("/admin/project-requests/export.csv")
async def export_requests(_: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    rows = list((await db.scalars(select(ProjectRequest).order_by(desc(ProjectRequest.created_at)))).all())
    output = io.StringIO()
    fields = ["reference", "created_at", "status", "client_name", "email", "preferred_contact_method", "service_name_snapshot", "package_name_snapshot", "price_snapshot", "currency_snapshot", "project_title"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        data = row_dict(row)

        def safe_csv(value: Any) -> Any:
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                return "'" + value
            return value

        writer.writerow({field: safe_csv(data.get(field)) for field in fields})
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=project-requests.csv"})


@router.get("/admin/project-requests/{request_id}")
async def admin_request(request_id: UUID, _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    row = await db.get(ProjectRequest, request_id)
    if not row:
        raise HTTPException(404, "Request not found")
    result = row_dict(row)
    attachments = (await db.scalars(select(ProjectRequestAttachment).where(ProjectRequestAttachment.request_id == row.id, ProjectRequestAttachment.deleted_at.is_(None)))).all()
    result["attachments"] = [
        {
            **row_dict(item),
            "secure_url": private_attachment_url(item.public_id, item.original_name),
            "url_expires_in_seconds": 300,
        }
        for item in attachments
    ]
    return result


@router.patch("/admin/project-requests/{request_id}")
async def update_request(request_id: UUID, data: RequestStatusPatch, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    row = await db.get(ProjectRequest, request_id)
    if not row:
        raise HTTPException(404, "Request not found")
    if data.status is not None:
        row.status = data.status
    if data.admin_notes is not None or data.internal_notes is not None:
        row.internal_notes = data.admin_notes if data.admin_notes is not None else data.internal_notes
    db.add(audit(admin, "update", "project_request", row.id, request))
    await db.commit()
    await db.refresh(row)
    return row_dict(row)


@router.get("/admin/profile")
async def admin_profile(_: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    profile = await db.scalar(select(Profile).where(Profile.deleted_at.is_(None)).order_by(Profile.created_at))
    if not profile:
        raise HTTPException(404, "Profile not configured")
    return row_dict(profile)


@router.patch("/admin/profile")
async def update_profile(payload: ProfilePatch, request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    profile = await db.scalar(select(Profile).where(Profile.deleted_at.is_(None)).order_by(Profile.created_at))
    if not profile:
        raise HTTPException(404, "Profile not configured")
    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(profile, key, value)
    db.add(audit(admin, "update", "profile", profile.id, request))
    await db.commit()
    await db.refresh(profile)
    return row_dict(profile)


@router.post("/admin/profile/photo")
async def update_profile_photo(
    request: Request,
    file: UploadFile = File(...),
    alt_text_en: str = Form(...),
    alt_text_ar: str = Form(...),
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    enforce_rate_limit(request, "admin-profile-photo", 20, 300)
    if not (1 <= len(alt_text_en.strip()) <= 300 and 1 <= len(alt_text_ar.strip()) <= 300):
        raise HTTPException(422, "Photo alternative text must be between 1 and 300 characters")
    profile = await db.scalar(select(Profile).where(Profile.deleted_at.is_(None)).order_by(Profile.created_at))
    if not profile:
        raise HTTPException(404, "Profile not configured")
    content, media_type = await validate_media(file, allow_video=False)
    if media_type != "image":
        raise HTTPException(422, "Profile photos must be images")
    result = await upload_media(content, "image", "ayman-portfolio/profile", transformation=[{"width": 1200, "height": 1200, "crop": "limit", "quality": "auto", "fetch_format": "auto"}])
    old_public_id = profile.profile_image_public_id
    profile.profile_image_url = result["secure_url"]
    profile.profile_image_public_id = result["public_id"]
    profile.profile_image_alt_en = alt_text_en.strip()
    profile.profile_image_alt_ar = alt_text_ar.strip()
    db.add(MediaAsset(cloudinary_public_id=result["public_id"], secure_url=result["secure_url"], resource_type="image", mime_type=file.content_type, size_bytes=len(content), width=result.get("width"), height=result.get("height")))
    db.add(audit(admin, "replace_photo", "profile", profile.id, request))
    await db.commit()
    await db.refresh(profile)
    if old_public_id and not await public_id_in_use(db, old_public_id):
        await destroy_media(old_public_id, "image")
    return row_dict(profile)


@router.delete("/admin/profile/photo", status_code=204)
async def delete_profile_photo(request: Request, admin: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)) -> Response:
    profile = await db.scalar(select(Profile).where(Profile.deleted_at.is_(None)).order_by(Profile.created_at))
    if not profile:
        raise HTTPException(404, "Profile not configured")
    public_id = profile.profile_image_public_id
    profile.profile_image_url = None
    profile.profile_image_public_id = None
    db.add(audit(admin, "delete_photo", "profile", profile.id, request))
    await db.commit()
    if public_id and not await public_id_in_use(db, public_id):
        await destroy_media(public_id, "image")
    return Response(status_code=204)
