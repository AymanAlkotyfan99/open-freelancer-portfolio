import asyncio
import io
import secrets
import time
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from fastapi import HTTPException, UploadFile

from app.core.config import settings

MediaRule = tuple[set[str], Callable[[bytes], bool]]

IMAGE_RULES: dict[str, MediaRule] = {
    "image/jpeg": ({".jpg", ".jpeg"}, lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": ({".png"}, lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": ({".webp"}, lambda data: data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
    "image/avif": ({".avif"}, lambda data: data[4:8] == b"ftyp" and data[8:12] in {b"avif", b"avis"}),
}
VIDEO_RULES: dict[str, MediaRule] = {
    "video/mp4": ({".mp4"}, lambda data: data[4:8] == b"ftyp"),
    "video/webm": ({".webm"}, lambda data: data.startswith(b"\x1aE\xdf\xa3")),
}
ATTACHMENT_RULES: dict[str, MediaRule] = {
    "application/pdf": ({".pdf"}, lambda data: data.startswith(b"%PDF-")),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        {".docx"},
        lambda data: data.startswith(b"PK"),
    ),
    "image/png": IMAGE_RULES["image/png"],
    "image/jpeg": IMAGE_RULES["image/jpeg"],
}


def local_media_root() -> Path:
    configured = Path(settings.local_media_dir)
    return configured.resolve() if configured.is_absolute() else (Path(__file__).resolve().parents[2] / configured).resolve()


def cloudinary_configured() -> bool:
    return bool(
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    )


def cloudinary_ready() -> None:
    if not cloudinary_configured():
        raise HTTPException(503, "Media storage is not configured")
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


async def validate_media(file: UploadFile, allow_video: bool = True) -> tuple[bytes, str]:
    rules = {**IMAGE_RULES, **(VIDEO_RULES if allow_video else {})}
    mime = file.content_type or ""
    rule = rules.get(mime)
    suffix = Path(file.filename or "").suffix.lower()
    if not rule or suffix not in rule[0]:
        raise HTTPException(422, "Unsupported file extension or MIME type")
    media_type = "video" if mime.startswith("video/") else "image"
    limit_mb = settings.max_video_upload_mb if media_type == "video" else settings.max_image_upload_mb
    content = await file.read(limit_mb * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(422, "The uploaded file is empty")
    if len(content) > limit_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds the configured {limit_mb} MB limit")
    if not rule[1](content[:64]):
        raise HTTPException(422, "File content does not match its declared type")
    return content, media_type


def _is_valid_docx(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = set(archive.namelist())
        return "[Content_Types].xml" in names and "word/document.xml" in names
    except (OSError, zipfile.BadZipFile):
        return False


async def validate_attachment(file: UploadFile) -> tuple[bytes, str, str, str]:
    mime = file.content_type or ""
    rule = ATTACHMENT_RULES.get(mime)
    original_name = Path((file.filename or "attachment").replace("\\", "/")).name
    original_name = original_name.replace("\r", "").replace("\n", "")[:255]
    suffix = Path(original_name).suffix.lower()
    if not rule or suffix not in rule[0]:
        raise HTTPException(422, "Unsupported file extension or MIME type")
    limit = settings.max_request_attachment_mb * 1024 * 1024
    content = await file.read(limit + 1)
    if not content:
        raise HTTPException(422, "The uploaded file is empty")
    if len(content) > limit:
        raise HTTPException(413, f"File exceeds the configured {settings.max_request_attachment_mb} MB limit")
    if not rule[1](content[:64]):
        raise HTTPException(422, "File content does not match its declared type")
    if suffix == ".docx" and not _is_valid_docx(content):
        raise HTTPException(422, "The uploaded DOCX structure is invalid")
    return content, mime, suffix, original_name or f"attachment{suffix}"


async def upload_private_attachment(content: bytes, suffix: str) -> dict[str, Any]:
    cloudinary_ready()
    return await asyncio.to_thread(
        cloudinary.uploader.upload,
        content,
        folder="ayman-portfolio/project-requests",
        public_id=secrets.token_urlsafe(18),
        format=suffix.removeprefix("."),
        resource_type="raw",
        type="authenticated",
        overwrite=False,
    )


def private_attachment_url(public_id: str, original_name: str) -> str:
    cloudinary_ready()
    return str(
        cloudinary.utils.private_download_url(
            public_id,
            Path(original_name).suffix.removeprefix(".").lower(),
            resource_type="raw",
            type="authenticated",
            attachment=True,
            expires_at=int(time.time()) + 300,
            secure=True,
        )
    )


def media_extension(content: bytes, media_type: str) -> str:
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    if content[4:8] == b"ftyp" and content[8:12] in {b"avif", b"avis"}:
        return ".avif"
    if media_type == "video" and content[4:8] == b"ftyp":
        return ".mp4"
    if media_type == "video" and content.startswith(b"\x1aE\xdf\xa3"):
        return ".webm"
    raise HTTPException(422, "Unsupported media content")


async def upload_local_media(content: bytes, media_type: str, folder: str) -> dict[str, Any]:
    root = local_media_root()
    safe_parts = [part for part in folder.replace("\\", "/").split("/") if part and part not in {".", ".."}]
    destination_dir = root.joinpath(*safe_parts)
    destination = destination_dir / f"{secrets.token_urlsafe(18)}{media_extension(content, media_type)}"
    await asyncio.to_thread(destination_dir.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(destination.write_bytes, content)
    relative = destination.relative_to(root).as_posix()
    return {
        "secure_url": f"{settings.api_public_url.rstrip('/')}/uploads/{relative}",
        "public_id": f"local:{relative}",
        "width": None,
        "height": None,
    }


async def upload_media(
    content: bytes,
    media_type: str,
    folder: str,
    *,
    transformation: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not cloudinary_configured():
        if settings.environment == "production":
            cloudinary_ready()
        return await upload_local_media(content, media_type, folder)
    cloudinary_ready()
    options: dict[str, Any] = {
        "folder": folder,
        "public_id": secrets.token_urlsafe(18),
        "resource_type": media_type,
        "overwrite": False,
    }
    if transformation:
        options["transformation"] = transformation
    return await asyncio.to_thread(cloudinary.uploader.upload, content, **options)


async def destroy_media(public_id: str, media_type: str) -> None:
    if public_id.startswith("local:"):
        root = local_media_root()
        destination = (root / public_id.removeprefix("local:")).resolve()
        if destination != root and root in destination.parents:
            await asyncio.to_thread(destination.unlink, missing_ok=True)
        return
    cloudinary_ready()
    result = await asyncio.to_thread(
        cloudinary.uploader.destroy,
        public_id,
        resource_type=media_type,
        invalidate=True,
    )
    if result.get("result") not in {"ok", "not found"}:
        raise HTTPException(502, "The media provider could not delete the asset")
