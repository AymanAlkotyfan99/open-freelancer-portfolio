import asyncio
import secrets
from collections.abc import Callable
from pathlib import Path
from typing import Any

import cloudinary
import cloudinary.uploader
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


def cloudinary_ready() -> None:
    if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
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


async def upload_media(
    content: bytes,
    media_type: str,
    folder: str,
    *,
    transformation: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
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
    cloudinary_ready()
    result = await asyncio.to_thread(
        cloudinary.uploader.destroy,
        public_id,
        resource_type=media_type,
        invalidate=True,
    )
    if result.get("result") not in {"ok", "not found"}:
        raise HTTPException(502, "The media provider could not delete the asset")
