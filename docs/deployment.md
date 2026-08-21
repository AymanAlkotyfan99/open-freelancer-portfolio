# Production deployment

The supported production topology runs all primary runtime components on Railway:

- Next.js web service from `apps/web`
- FastAPI service from `apps/api`
- Railway PostgreSQL

Cloudinary stores permanent production media. Cloudflare Turnstile verifies public submissions. Resend provides optional transactional notifications, and the API can read allowlisted GitHub repositories.

Use the complete [Railway deployment guide](RAILWAY_DEPLOYMENT.md) for service roots, config-file paths, variables, migrations, one-time seeding/admin creation, domains, providers, verification, backups, rollback, monitoring, and troubleshooting.

Use the [production checklist](PRODUCTION_CHECKLIST.md) before making the site public.

Do not substitute the old Vercel/Neon topology, enable local production uploads, place Alembic in the application start command, or create the administrator automatically on deployment.
