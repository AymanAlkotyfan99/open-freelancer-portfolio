import re
import time
from collections import defaultdict
from ipaddress import ip_address
from typing import Any

import httpx
import resend
from fastapi import HTTPException, Request

from app.core.config import settings

_hits: dict[str, list[float]] = defaultdict(list)
_github_cache: tuple[float, list[dict[str, Any]]] = (0, [])
_REPOSITORY_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


def client_ip(request: Request) -> str:
    fallback = request.client.host if request.client else "unknown"
    if not settings.trust_proxy_headers:
        return fallback
    candidate = request.headers.get("X-Real-IP", "")
    try:
        return str(ip_address(candidate))
    except ValueError:
        return fallback


def enforce_rate_limit(request: Request, scope: str, limit: int = 5, window: int = 60) -> None:
    key = f"{scope}:{client_ip(request)}"
    now = time.time()
    if len(_hits) >= settings.rate_limit_max_keys and key not in _hits:
        for stale_key in [name for name, stamps in _hits.items() if not stamps or now - stamps[-1] >= window]:
            _hits.pop(stale_key, None)
        if len(_hits) >= settings.rate_limit_max_keys:
            raise HTTPException(503, "Rate limiting is temporarily unavailable")
    _hits[key] = [stamp for stamp in _hits[key] if now - stamp < window]
    if len(_hits[key]) >= limit:
        raise HTTPException(429, "Please wait before trying again")
    _hits[key].append(now)


async def verify_turnstile(token: str, remote_ip: str = "") -> None:
    if not settings.turnstile_secret_key and settings.environment != "production":
        return
    if not token:
        raise HTTPException(400, "Verification required")
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": settings.turnstile_secret_key,
                    "response": token,
                    "remoteip": remote_ip,
                },
            )
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, "Verification service is unavailable") from exc
    hostname = str(result.get("hostname", "")).lower()
    if not result.get("success") or (
        settings.turnstile_hostname_list and hostname not in settings.turnstile_hostname_list
    ):
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
    repositories = list(dict.fromkeys(allowlist))[:50]
    if not settings.github_username or not repositories:
        return []
    if not _REPOSITORY_NAME.fullmatch(settings.github_username) or any(
        not _REPOSITORY_NAME.fullmatch(repository) for repository in repositories
    ):
        return []
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    try:
        async with httpx.AsyncClient(timeout=8, headers=headers) as client:
            rows = []
            for repo in repositories:
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
