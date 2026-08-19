# Production deployment

The repository is configured for Vercel (web), Railway (API), Neon PostgreSQL, Cloudinary, Resend, and Cloudflare Turnstile. It does not contain credentials and has not been deployed by this implementation.

## Required configuration

Copy `.env.example` and set a TLS Neon `DATABASE_URL`, a random 32+ character `JWT_SECRET_KEY`, exact HTTPS `FRONTEND_URL`/`CORS_ORIGINS`, Cloudinary credentials and upload limits, Resend credentials/sender/recipient, Turnstile keys, and optional GitHub credentials. Web variables are documented in `apps/web/.env.example`; `NEXT_PUBLIC_API_URL` must include `/api/v1`. Replace `[DOMAIN]`, `[EMAIL]`, `[PHONE]`, `[WHATSAPP]`, `[TELEGRAM]`, `[GITHUB_URL]`, `[GITHUB_USERNAME]`, `[LINKEDIN_URL]`, `[UPWORK_URL]`, and `[CV_URL]` through verified configuration/content.

## Railway / Neon API

1. Create Neon and enable the backup/PITR policy appropriate to the selected plan.
2. Create a Railway service rooted at `apps/api`; `railway.json` and the Dockerfile run `alembic upgrade head` before Uvicorn and expose `/api/v1/health`.
3. Add API environment values. Attach `api.[DOMAIN]`, verify health and migrations, then restrict CORS/frontend settings to the final origins.
4. Run `portfolio-seed` once and `portfolio-admin` in a secure Railway shell.

## Vercel web

Create a Vercel project rooted at `apps/web`, set the web variables, and deploy. The CSP derives its API origin from `NEXT_PUBLIC_API_URL`. Attach `[DOMAIN]`/`www.[DOMAIN]`, register those domains in Turnstile, and verify `/en`, `/ar`, `/admin`, dynamic metadata, `/sitemap.xml`, `/robots.txt`, request forms, and mobile navigation.

## Provider and recovery checks

- Verify the Resend sender domain and confirm that a deliberate email failure still leaves the inquiry in PostgreSQL.
- Configure Cloudinary folder policy, transformations, resource limits, and backups; test upload/reorder/cover/delete for image and video.
- Run a quarterly Neon restore drill into an isolated database and record recovery time. Export request CSV before changing retention.
- Run `docker compose config` and the CI/static/unit/E2E commands before release. Docker image execution still requires a working Docker daemon.
