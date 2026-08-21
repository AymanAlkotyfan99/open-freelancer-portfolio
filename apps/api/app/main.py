import logging
import re
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.portfolio import router as portfolio_router
from app.api.router import router
from app.core.config import settings
from app.database.session import engine
from app.services.media import local_media_root

logger = logging.getLogger(__name__)
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


production_docs = None if settings.is_production else "/docs"
app = FastAPI(
    title=settings.app_name,
    docs_url=production_docs,
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    supplied_request_id = request.headers.get("X-Request-ID", "")
    request_id = supplied_request_id if _REQUEST_ID.fullmatch(supplied_request_id) else str(uuid.uuid4())
    request.state.request_id = request_id

    rejected_origin = request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith(
        ("/api/v1/auth", "/api/v1/admin")
    )
    response: Response
    if rejected_origin:
        origin = request.headers.get("Origin")
        if (settings.is_production and not origin) or (origin and origin not in settings.cors_list):
            response = JSONResponse(
                status_code=403,
                content={"detail": "Request origin is not allowed"},
                headers={"X-Request-ID": request_id},
            )
        else:
            response = await call_next(request)
    else:
        response = await call_next(request)
    headers = {
        "X-Request-ID": request_id,
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    }
    if settings.is_production:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path.startswith(("/api/v1/auth", "/api/v1/admin")):
        headers["Cache-Control"] = "no-store"
    response.headers.update(headers)
    return response


@app.exception_handler(Exception)
async def unhandled(request: Request, exception: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.exception("Unhandled request error request_id=%s", request_id, exc_info=exception)
    return JSONResponse(
        status_code=500,
        content={"detail": "The request could not be completed"},
        headers={"X-Request-ID": request_id},
    )


app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")
if not settings.is_production:
    app.mount("/uploads", StaticFiles(directory=local_media_root(), check_dir=False), name="uploads")
