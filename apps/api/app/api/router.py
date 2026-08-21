import asyncio
import html
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import JSON, String, asc, func, select, text
from sqlalchemy.exc import IntegrityError, StatementError
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
    DUMMY_PASSWORD_HASH,
    create_token,
    current_admin,
    hash_password,
    token_hash,
    verify_password,
)
from app.services.integrations import (
    client_ip,
    enforce_rate_limit,
    github_summary,
    send_email,
    verify_turnstile,
)
from app.services.media import upload_private_attachment, validate_attachment

router = APIRouter()


def as_dict(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "reachable"}


PUBLIC_LISTS = {
    "skills": Skill,
    "skill-categories": SkillCategory,
    "projects": Project,
    "project-images": ProjectImage,
    "project-technologies": ProjectTechnology,
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
async def github(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    # Bound calls to the external provider even when its response is not cacheable.
    enforce_rate_limit(request, "github-summary", 30, 300)
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
    await verify_turnstile(payload.turnstile_token, client_ip(request))
    row = ContactMessage(**payload.model_dump(exclude={"consent", "turnstile_token", "website"}))
    db.add(row)
    await db.commit()
    delivered = send_email(
        "New portfolio contact",
        f"<h2>{html.escape(payload.subject)}</h2><p>From {html.escape(payload.full_name)}</p>"
        f"<p>{html.escape(payload.message)}</p>",
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
    await verify_turnstile(payload.turnstile_token, client_ip(request))
    reference = f"AN-{secrets.token_hex(5).upper()}"
    row = ProjectRequest(
        reference=reference, **payload.model_dump(exclude={"consent", "turnstile_token", "website"})
    )
    db.add(row)
    await db.commit()
    delivered = send_email(
        f"New project request {reference}",
        f"<h2>{html.escape(payload.project_title)}</h2><p>{html.escape(payload.client_name)}</p>"
        f"<p>{html.escape(payload.description)}</p>",
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
    enforce_rate_limit(request, "project-attachment", 3, 300)
    project_request = await db.scalar(
        select(ProjectRequest).where(ProjectRequest.reference == reference)
    )
    if not project_request:
        raise HTTPException(404, "Project request not found")
    content, mime, suffix, original_name = await validate_attachment(file)
    result = await upload_private_attachment(content, suffix)
    attachment = ProjectRequestAttachment(
        request_id=project_request.id,
        original_name=original_name,
        secure_url=result["secure_url"],
        public_id=result["public_id"],
        mime_type=mime,
        size_bytes=len(content),
    )
    db.add(attachment)
    await db.commit()
    return {"id": attachment.id, "message": "Attachment stored"}


def set_auth_cookies(response: Response, user: AdminUser) -> None:
    secure = settings.is_production
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
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain or None,
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        secure=secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain or None,
        path="/api/v1/auth",
        max_age=settings.refresh_token_expire_days * 86400,
    )


@router.post("/auth/login")
async def login(
    payload: LoginIn, response: Response, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    enforce_rate_limit(request, "login", 5, 300)
    user = await db.scalar(
        select(AdminUser)
        .where(func.lower(AdminUser.email) == payload.email.lower())
        .with_for_update()
    )
    now = datetime.now(timezone.utc)
    if not user:
        verify_password(payload.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active or (user.locked_until and user.locked_until > now):
        verify_password(payload.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(401, "Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
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

    enforce_rate_limit(request, "refresh", 10, 300)
    token = request.cookies.get("refresh_token", "")
    payload = decode_token(token, "refresh")
    try:
        subject = UUID(str(payload["sub"]))
    except (TypeError, ValueError) as exc:
        raise HTTPException(401, "Invalid session") from exc
    user = await db.scalar(select(AdminUser).where(AdminUser.id == subject).with_for_update())
    if not user or not user.is_active or user.refresh_token_hash != token_hash(token):
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
    response.delete_cookie("access_token", domain=settings.cookie_domain or None)
    response.delete_cookie(
        "refresh_token", path="/api/v1/auth", domain=settings.cookie_domain or None
    )
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
    "skills": Skill,
    "skill-categories": SkillCategory,
    "experiences": Experience,
    "education": Education,
    "activities": Activity,
    "social-links": SocialLink,
    "site-settings": SiteSetting,
}

_SYSTEM_FIELDS = {"id", "created_at", "updated_at", "deleted_at"}


def validate_admin_data(model: Any, data: dict[str, Any], *, creating: bool) -> dict[str, Any]:
    columns = {column.name: column for column in model.__table__.columns if column.name not in _SYSTEM_FIELDS}
    unknown = sorted(set(data) - set(columns))
    if unknown:
        raise HTTPException(422, f"Unknown or protected fields: {', '.join(unknown)}")
    if not data:
        raise HTTPException(422, "At least one field is required")
    validated: dict[str, Any] = {}
    for name, value in data.items():
        column = columns[name]
        if value is None:
            if not column.nullable and (creating or column.default is None):
                raise HTTPException(422, f"{name} cannot be null")
            validated[name] = None
            continue
        if isinstance(column.type, String) and column.type.length and len(str(value)) > column.type.length:
            raise HTTPException(422, f"{name} exceeds its maximum length")
        if isinstance(column.type, JSON):
            validated[name] = value
            continue
        try:
            validated[name] = TypeAdapter(column.type.python_type).validate_python(value)
        except (NotImplementedError, ValidationError, ValueError, TypeError) as exc:
            raise HTTPException(422, f"Invalid value for {name}") from exc
    return validated


@router.post("/admin/uploads", status_code=201)
async def admin_upload(
    request: Request,
    file: UploadFile = File(...),
    _: AdminUser = Depends(current_admin),
) -> dict[str, Any]:
    import cloudinary
    import cloudinary.uploader

    enforce_rate_limit(request, "admin-upload", 20, 300)
    content, _mime, suffix, _original_name = await validate_attachment(file)
    if not settings.cloudinary_cloud_name:
        raise HTTPException(503, "Media storage is not configured")
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        content,
        folder="ayman-portfolio/admin",
        public_id=secrets.token_urlsafe(18),
        resource_type="image" if suffix in {".jpg", ".jpeg", ".png"} else "raw",
        overwrite=False,
    )
    return {
        "public_id": result["public_id"],
        "secure_url": result["secure_url"],
        "bytes": len(content),
    }


@router.get("/admin/{resource}")
async def admin_list(
    resource: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
    row = model(**validate_admin_data(model, data, creating=True))
    db.add(row)
    try:
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
    except (IntegrityError, StatementError) as exc:
        await db.rollback()
        raise HTTPException(409, "The record conflicts with existing or required data") from exc
    await db.refresh(row)
    return as_dict(row)


@router.patch("/admin/{resource}/{entity_id}")
async def admin_update(
    resource: str,
    entity_id: UUID,
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
                entity_id=str(entity_id),
            )
        )
        await db.commit()
        await db.refresh(contact_row)
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
                entity_id=str(entity_id),
            )
        )
        await db.commit()
        await db.refresh(row)
        return as_dict(row)
    model = ADMIN_MODELS.get(resource)
    if not model:
        raise HTTPException(404, "Not found")
    row = await db.get(model, entity_id)  # type: ignore[arg-type]
    if not row:
        raise HTTPException(404, "Not found")
    validated = validate_admin_data(model, data, creating=False)
    for key, value in validated.items():
        setattr(row, key, value)
    db.add(
        AuditLog(
            admin_id=admin.id,
            action="update",
            entity_type=resource,
            entity_id=str(entity_id),
            details={"fields": list(data)},
        )
    )
    await db.commit()
    await db.refresh(row)
    return as_dict(row)


@router.delete("/admin/{resource}/{entity_id}", status_code=204)
async def admin_delete(
    resource: str,
    entity_id: UUID,
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
    db.add(
        AuditLog(
            admin_id=admin.id,
            action="delete",
            entity_type=resource,
            entity_id=str(entity_id),
        )
    )
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
    entity_id: UUID,
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
            entity_id=str(entity_id),
        )
    )
    await db.commit()
    await db.refresh(row)
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
