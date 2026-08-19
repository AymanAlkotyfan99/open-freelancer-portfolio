import secrets
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.models.entities import (
    Activity,
    AdminUser,
    AuditLog,
    ContactMessage,
    Education,
    Experience,
    Profile,
    Project,
    ProjectImage,
    ProjectRequest,
    ProjectRequestAttachment,
    ProjectTechnology,
    Service,
    SiteSetting,
    Skill,
    SkillCategory,
    SocialLink,
)
from app.schemas.api import ContactIn, LoginIn, PasswordChange, ProjectRequestIn, StatusPatch
from app.security.auth import (
    create_token,
    current_admin,
    hash_password,
    token_hash,
    verify_password,
)
from app.services.integrations import (
    enforce_rate_limit,
    github_summary,
    send_email,
    verify_turnstile,
)

router = APIRouter()


def as_dict(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


PUBLIC_LISTS = {
    "skills": Skill,
    "skill-categories": SkillCategory,
    "projects": Project,
    "project-images": ProjectImage,
    "project-technologies": ProjectTechnology,
    "project-request-attachments": ProjectRequestAttachment,
    "services": Service,
    "experiences": Experience,
    "education": Education,
    "activities": Activity,
    "social-links": SocialLink,
}


@router.get("/profile")
async def profile(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    row = await db.scalar(select(Profile).where(Profile.is_active.is_(True)))
    if not row:
        raise HTTPException(404, "Profile not configured")
    return as_dict(row)


@router.get("/{resource}")
async def public_list(resource: str, db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    model = PUBLIC_LISTS.get(resource)
    if not model:
        raise HTTPException(404, "Not found")
    query = select(model)
    if hasattr(model, "is_active"):
        query = query.where(model.is_active.is_(True))
    if hasattr(model, "publication_status"):
        query = query.where(model.publication_status == "published")
    if hasattr(model, "sort_order"):
        query = query.order_by(asc(model.sort_order))
    return [as_dict(row) for row in (await db.scalars(query)).all()]


@router.get("/projects/{slug}")
async def project_detail(slug: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    row = await db.scalar(
        select(Project).where(Project.slug == slug, Project.publication_status == "published")
    )
    if not row:
        raise HTTPException(404, "Project not found")
    return as_dict(row)


@router.get("/site-settings/public")
async def public_settings(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return [
        as_dict(row)
        for row in (
            await db.scalars(select(SiteSetting).where(SiteSetting.is_public.is_(True)))
        ).all()
    ]


@router.get("/github/summary")
async def github(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    setting = await db.scalar(select(SiteSetting).where(SiteSetting.key == "github_allowlist"))
    allowlist = (setting.value if setting else {}).get("repositories", [])
    return {
        "username": settings.github_username,
        "repositories": await github_summary(allowlist),
        "fallback": not bool(settings.github_token),
    }


@router.post("/contact", status_code=201)
async def contact(
    payload: ContactIn, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    enforce_rate_limit(request, "contact")
    if payload.website:
        return {"message": "Message received"}
    await verify_turnstile(payload.turnstile_token, request.client.host if request.client else "")
    row = ContactMessage(**payload.model_dump(exclude={"consent", "turnstile_token", "website"}))
    db.add(row)
    await db.commit()
    delivered = send_email(
        "New portfolio contact",
        f"<h2>{payload.subject}</h2><p>From {payload.full_name}</p><p>{payload.message}</p>",
    )
    row.email_delivered = delivered
    await db.commit()
    return {"message": "Message received"}


@router.post("/project-requests", status_code=201)
async def request_project(
    payload: ProjectRequestIn, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    enforce_rate_limit(request, "project-request", 3, 300)
    if payload.website:
        return {"message": "Request received", "reference": "PENDING"}
    await verify_turnstile(payload.turnstile_token, request.client.host if request.client else "")
    reference = f"AN-{secrets.token_hex(5).upper()}"
    row = ProjectRequest(
        reference=reference, **payload.model_dump(exclude={"consent", "turnstile_token", "website"})
    )
    db.add(row)
    await db.commit()
    delivered = send_email(
        f"New project request {reference}",
        f"<h2>{payload.project_title}</h2><p>{payload.client_name}</p><p>{payload.description}</p>",
    )
    row.email_delivered = delivered
    await db.commit()
    return {"message": "Request received", "reference": reference}


@router.post("/project-requests/{reference}/attachment", status_code=201)
async def request_attachment(
    reference: str,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    import cloudinary
    import cloudinary.uploader

    enforce_rate_limit(request, "project-attachment", 3, 300)
    project_request = await db.scalar(
        select(ProjectRequest).where(ProjectRequest.reference == reference)
    )
    if not project_request:
        raise HTTPException(404, "Project request not found")
    allowed: dict[str, tuple[str, Callable[[bytes], bool]]] = {
        "application/pdf": (".pdf", lambda value: value.startswith(b"%PDF-")),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
            ".docx",
            lambda value: value.startswith(b"PK"),
        ),
        "image/png": (".png", lambda value: value.startswith(b"\x89PNG\r\n\x1a\n")),
        "image/jpeg": (".jpg", lambda value: value.startswith(b"\xff\xd8\xff")),
    }
    rule = allowed.get(file.content_type or "")
    filename = (file.filename or "").lower()
    valid_jpeg_extension = file.content_type == "image/jpeg" and filename.endswith(".jpeg")
    if not rule or (not filename.endswith(rule[0]) and not valid_jpeg_extension):
        raise HTTPException(422, "Unsupported file type")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 10 MB")
    if not rule[1](content):
        raise HTTPException(422, "File content does not match its declared type")
    if not settings.cloudinary_cloud_name:
        raise HTTPException(503, "Media storage is not configured")
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    public_id = secrets.token_urlsafe(18)
    result = cloudinary.uploader.upload(
        content,
        folder="ayman-portfolio/project-requests",
        public_id=public_id,
        resource_type="auto",
    )
    attachment = ProjectRequestAttachment(
        request_id=project_request.id,
        original_name=file.filename or f"attachment{rule[0]}",
        secure_url=result["secure_url"],
        public_id=result["public_id"],
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    db.add(attachment)
    await db.commit()
    return {"id": attachment.id, "secure_url": attachment.secure_url}


def set_auth_cookies(response: Response, user: AdminUser) -> None:
    secure = settings.environment == "production"
    access = create_token(
        str(user.id), "access", timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh = create_token(
        str(user.id), "refresh", timedelta(days=settings.refresh_token_expire_days)
    )
    user.refresh_token_hash = token_hash(refresh)
    response.set_cookie(
        "access_token",
        access,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/api/v1/auth",
        max_age=settings.refresh_token_expire_days * 86400,
    )


@router.post("/auth/login")
async def login(
    payload: LoginIn, response: Response, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    enforce_rate_limit(request, "login", 5, 300)
    user = await db.scalar(
        select(AdminUser).where(func.lower(AdminUser.email) == payload.email.lower())
    )
    if (
        not user
        or (user.locked_until and user.locked_until > datetime.now(timezone.utc))
        or not verify_password(payload.password, user.password_hash)
    ):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            await db.commit()
        raise HTTPException(401, "Invalid credentials")
    user.failed_login_attempts = 0
    user.locked_until = None
    set_auth_cookies(response, user)
    await db.commit()
    return {"message": "Authenticated"}


@router.post("/auth/refresh")
async def refresh(
    response: Response, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    from app.security.auth import decode_token

    token = request.cookies.get("refresh_token", "")
    payload = decode_token(token, "refresh")
    try:
        subject = UUID(str(payload["sub"]))
    except (TypeError, ValueError) as exc:
        raise HTTPException(401, "Invalid session") from exc
    user = await db.scalar(select(AdminUser).where(AdminUser.id == subject))
    if not user or user.refresh_token_hash != token_hash(token):
        raise HTTPException(401, "Invalid session")
    set_auth_cookies(response, user)
    await db.commit()
    return {"message": "Session refreshed"}


@router.post("/auth/logout")
async def logout(
    response: Response,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    admin.refresh_token_hash = None
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    await db.commit()
    return {"message": "Signed out"}


@router.get("/auth/me")
async def me(admin: AdminUser = Depends(current_admin)) -> dict[str, Any]:
    return {"id": admin.id, "email": admin.email}


@router.post("/auth/change-password")
async def change_password(
    payload: PasswordChange,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if not verify_password(payload.current_password, admin.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    admin.password_hash = hash_password(payload.new_password)
    admin.refresh_token_hash = None
    db.add(
        AuditLog(
            admin_id=admin.id,
            action="change_password",
            entity_type="admin_user",
            entity_id=str(admin.id),
        )
    )
    await db.commit()
    return {"message": "Password changed"}


ADMIN_MODELS = {
    "profile": Profile,
    "skills": Skill,
    "skill-categories": SkillCategory,
    "projects": Project,
    "services": Service,
    "experiences": Experience,
    "education": Education,
    "activities": Activity,
    "social-links": SocialLink,
    "site-settings": SiteSetting,
}


@router.post("/admin/uploads", status_code=201)
async def admin_upload(
    file: UploadFile = File(...), _: AdminUser = Depends(current_admin)
) -> dict[str, Any]:
    import cloudinary
    import cloudinary.uploader

    allowed = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    }
    suffix = allowed.get(file.content_type or "")
    if not suffix or not (file.filename or "").lower().endswith(suffix):
        raise HTTPException(422, "Unsupported file type")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 10 MB")
    if not settings.cloudinary_cloud_name:
        raise HTTPException(503, "Media storage is not configured")
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    result = cloudinary.uploader.upload(
        content,
        folder="ayman-portfolio/admin",
        public_id=secrets.token_urlsafe(18),
        resource_type="auto",
    )
    return {
        "public_id": result["public_id"],
        "secure_url": result["secure_url"],
        "bytes": len(content),
    }


@router.get("/admin/{resource}")
async def admin_list(
    resource: str,
    page: int = 1,
    page_size: int = 20,
    _: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if resource == "contact-messages":
        message_rows = (
            await db.scalars(
                select(ContactMessage)
                .order_by(ContactMessage.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return {
            "items": [as_dict(row) for row in message_rows],
            "page": page,
            "page_size": page_size,
        }
    if resource == "project-requests":
        request_rows = (
            await db.scalars(
                select(ProjectRequest)
                .order_by(ProjectRequest.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return {
            "items": [as_dict(row) for row in request_rows],
            "page": page,
            "page_size": page_size,
        }
    if resource == "audit-logs":
        audit_rows = (
            await db.scalars(
                select(AuditLog)
                .order_by(AuditLog.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return {"items": [as_dict(row) for row in audit_rows], "page": page, "page_size": page_size}
    model = ADMIN_MODELS.get(resource)
    if not model:
        raise HTTPException(404, "Not found")
    model_rows = (
        await db.scalars(select(model).offset((page - 1) * page_size).limit(min(page_size, 100)))
    ).all()
    return {"items": [as_dict(row) for row in model_rows], "page": page, "page_size": page_size}


@router.post("/admin/{resource}", status_code=201)
async def admin_create(
    resource: str,
    data: dict[str, Any],
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    model = ADMIN_MODELS.get(resource)
    if not model:
        raise HTTPException(404, "Not found")
    valid = {
        column.name
        for column in model.__table__.columns
        if column.name not in {"id", "created_at", "updated_at", "deleted_at"}
    }
    row = model(**{key: value for key, value in data.items() if key in valid})
    db.add(row)
    await db.flush()
    db.add(
        AuditLog(
            admin_id=admin.id,
            action="create",
            entity_type=resource,
            entity_id=str(row.id),  # type: ignore[attr-defined]
        )
    )
    await db.commit()
    return as_dict(row)


@router.patch("/admin/{resource}/{entity_id}")
async def admin_update(
    resource: str,
    entity_id: str,
    data: dict[str, Any],
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if resource == "contact-messages":
        contact_row = await db.get(ContactMessage, entity_id)
        if not contact_row:
            raise HTTPException(404, "Not found")
        if "status" in data:
            contact_row.status = str(data["status"])
        db.add(
            AuditLog(
                admin_id=admin.id,
                action="status_update",
                entity_type="contact_message",
                entity_id=entity_id,
            )
        )
        await db.commit()
        return as_dict(contact_row)
    if resource == "project-requests":
        row = await db.get(ProjectRequest, entity_id)
        if not row:
            raise HTTPException(404, "Not found")
        allowed = {
            "new",
            "reviewing",
            "contacted",
            "in_discussion",
            "accepted",
            "rejected",
            "archived",
        }
        if "status" in data and data["status"] not in allowed:
            raise HTTPException(422, "Invalid status")
        for key in ("status", "internal_notes"):
            if key in data:
                setattr(row, key, data[key])
        db.add(
            AuditLog(
                admin_id=admin.id,
                action="status_update",
                entity_type="project_request",
                entity_id=entity_id,
            )
        )
        await db.commit()
        return as_dict(row)
    model = ADMIN_MODELS.get(resource)
    if not model:
        raise HTTPException(404, "Not found")
    row = await db.get(model, entity_id)  # type: ignore[arg-type]
    if not row:
        raise HTTPException(404, "Not found")
    valid = {column.name for column in model.__table__.columns} - {"id", "created_at", "updated_at"}
    for key, value in data.items():
        if key in valid:
            setattr(row, key, value)
    db.add(
        AuditLog(
            admin_id=admin.id,
            action="update",
            entity_type=resource,
            entity_id=entity_id,
            details={"fields": list(data)},
        )
    )
    await db.commit()
    return as_dict(row)


@router.delete("/admin/{resource}/{entity_id}", status_code=204)
async def admin_delete(
    resource: str,
    entity_id: str,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    model = ADMIN_MODELS.get(resource)
    row = await db.get(model, entity_id) if model else None
    if not row:
        raise HTTPException(404, "Not found")
    if hasattr(row, "deleted_at"):
        row.deleted_at = datetime.now(timezone.utc)
        if hasattr(row, "is_active"):
            row.is_active = False
    else:
        await db.delete(row)
    db.add(AuditLog(admin_id=admin.id, action="delete", entity_type=resource, entity_id=entity_id))
    await db.commit()
    return Response(status_code=204)


@router.get("/admin/contact-messages")
async def admin_messages(
    _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        as_dict(row)
        for row in (
            await db.scalars(select(ContactMessage).order_by(ContactMessage.created_at.desc()))
        ).all()
    ]


@router.get("/admin/project-requests")
async def admin_requests(
    _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        as_dict(row)
        for row in (
            await db.scalars(select(ProjectRequest).order_by(ProjectRequest.created_at.desc()))
        ).all()
    ]


@router.patch("/admin/project-requests/{entity_id}")
async def update_request(
    entity_id: str,
    payload: StatusPatch,
    admin: AdminUser = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    allowed = {"new", "reviewing", "contacted", "in_discussion", "accepted", "rejected", "archived"}
    if payload.status not in allowed:
        raise HTTPException(422, "Invalid status")
    row = await db.get(ProjectRequest, entity_id)
    if not row:
        raise HTTPException(404, "Not found")
    row.status, row.internal_notes = payload.status, payload.internal_notes
    db.add(
        AuditLog(
            admin_id=admin.id,
            action="status_update",
            entity_type="project_request",
            entity_id=entity_id,
        )
    )
    await db.commit()
    return as_dict(row)


@router.get("/admin/audit-logs")
async def audit_logs(
    _: AdminUser = Depends(current_admin), db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        as_dict(row)
        for row in (
            await db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200))
        ).all()
    ]
