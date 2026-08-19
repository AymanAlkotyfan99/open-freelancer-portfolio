import time
from collections import defaultdict
from typing import Any

import httpx
import resend
from fastapi import HTTPException, Request

from app.core.config import settings

_hits: dict[str, list[float]] = defaultdict(list)
_github_cache: tuple[float, list[dict[str, Any]]] = (0, [])


def enforce_rate_limit(request: Request, scope: str, limit: int = 5, window: int = 60) -> None:
    key = f"{scope}:{request.client.host if request.client else 'unknown'}"
    now = time.time()
    _hits[key] = [stamp for stamp in _hits[key] if now - stamp < window]
    if len(_hits[key]) >= limit:
        raise HTTPException(429, "Please wait before trying again")
    _hits[key].append(now)


async def verify_turnstile(token: str, remote_ip: str = "") -> None:
    if not settings.turnstile_secret_key and settings.environment != "production":
        return
    if not token:
        raise HTTPException(400, "Verification required")
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": settings.turnstile_secret_key,
                "response": token,
                "remoteip": remote_ip,
            },
        )
    if not response.json().get("success"):
        raise HTTPException(400, "Verification failed")


def send_email(subject: str, html: str, recipient: str | None = None) -> bool:
    if not settings.resend_api_key or not (recipient or settings.email_to):
        return False
    try:
        resend.api_key = settings.resend_api_key
        resend.Emails.send(
            {
                "from": settings.email_from,
                "to": [recipient or settings.email_to],
                "subject": subject,
                "html": html,
            }
        )
        return True
    except Exception:
        return False


async def github_summary(allowlist: list[str]) -> list[dict[str, Any]]:
    global _github_cache
    if _github_cache[1] and time.time() - _github_cache[0] < 900:
        return _github_cache[1]
    if not settings.github_username or not allowlist:
        return []
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    try:
        async with httpx.AsyncClient(timeout=8, headers=headers) as client:
            rows = []
            for repo in allowlist:
                response = await client.get(
                    f"https://api.github.com/repos/{settings.github_username}/{repo}"
                )
                response.raise_for_status()
                data = response.json()
                rows.append(
                    {
                        "name": data["name"],
                        "description": data.get("description"),
                        "language": data.get("language"),
                        "stars": data.get("stargazers_count", 0),
                        "url": data["html_url"],
                    }
                )
        _github_cache = (time.time(), rows)
        return rows
    except Exception:
        return []
