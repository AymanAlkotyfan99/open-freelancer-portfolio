# Container notes

The root Compose file builds both applications and runs PostgreSQL 16. The API image executes migrations before startup. Production uses the same API Dockerfile on Railway; the web image is an optional self-hosted build because Vercel is the intended frontend platform.

