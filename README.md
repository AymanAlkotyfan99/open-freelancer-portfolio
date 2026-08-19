# Ayman Naeem — production portfolio

A bilingual, content-managed portfolio for an AI Software Engineer and Full-Stack Developer. It includes premium responsive public pages, a purpose-built admin dashboard, normalized project media, three-tier service packages with typed comparisons, immutable commercial request snapshots, secure uploads, transactional email hooks, Docker, CI, and Vercel/Railway/Neon deployment configuration.

## Requirements

- Node.js 22 and npm
- Python 3.10+ and uv (or pip)
- PostgreSQL 16, or Docker Desktop

## Direct local development

```powershell
Copy-Item .env.example .env
docker compose up -d db
Set-Location apps/api
uv venv
uv pip install -e ".[dev]"
.venv\Scripts\alembic upgrade head
.venv\Scripts\portfolio-seed
.venv\Scripts\portfolio-admin
.venv\Scripts\uvicorn app.main:app --reload
```

In a second terminal:

```powershell
Set-Location apps/web
Copy-Item .env.example .env.local
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:3000/en`, `/ar`, and `/admin`. Development can omit email, Turnstile, and Cloudinary credentials; validated media is stored under `apps/api/uploads` when Cloudinary is absent locally. Production requires Cloudinary, Turnstile, and the documented provider configuration.

## Docker development

```powershell
Copy-Item .env.example .env
docker compose up --build
```

After first startup, run seed/admin commands inside the API container. Never use example secrets in production.

## Checks

```powershell
Set-Location apps/web
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npm.cmd run test:e2e

Set-Location ..\api
ruff check .
mypy app
pytest
alembic upgrade head
alembic check
```

The Playwright command starts isolated Next.js/FastAPI servers and recreates only `apps/api/e2e.db`. See [architecture](docs/architecture.md), [API](docs/api.md), [content management](docs/content-management.md), and [deployment](docs/deployment.md). The social preview in `apps/web/public/og.png` was generated specifically for this portfolio; personal photography remains an editable profile field.
