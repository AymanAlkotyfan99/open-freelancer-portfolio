import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.portfolio import router as portfolio_router
from app.api.router import router
from app.core.config import settings
from app.services.media import local_media_root

app = FastAPI(
    title=settings.app_name, docs_url=None if settings.environment == "production" else "/docs"
)
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
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers.update(
        {
            "X-Request-ID": request_id,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }
    )
    return response


@app.exception_handler(Exception)
async def unhandled(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "The request could not be completed"})


app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")
app.mount("/uploads", StaticFiles(directory=local_media_root(), check_dir=False), name="uploads")
