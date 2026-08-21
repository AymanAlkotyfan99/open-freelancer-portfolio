# Architecture

The monorepo keeps its two-application boundary: Next.js 15 App Router in `apps/web` and FastAPI/SQLAlchemy/Alembic in `apps/api`. All primary runtime services deploy to Railway. Railway PostgreSQL is the production source of truth; SQLite is used only by isolated automated tests.

```text
Browser -> Next.js (Railway) -> FastAPI /api/v1 (Railway) -> Railway PostgreSQL
                                  |-> Cloudinary (media)
                                  |-> Resend (notifications)
                                  |-> Turnstile (abuse protection)
                                  `-> GitHub API (allowlisted repositories)
```

Public content is explicitly bilingual (`*_en`, `*_ar`). Draft/archived projects and services never enter public endpoints. Project collections batch-load technologies and media; service collections batch-load packages. Detail endpoints load comparison data, FAQs, and related work only when needed. Next caches managed reads for `CONTENT_REVALIDATE_SECONDS` (60 by default); setting it to `0` enables deterministic no-store reads for E2E or immediate-preview environments.

## Commercial data model

- `services` owns bilingual scope, media, category, skills, availability, and publication state.
- `service_packages` allows at most one Basic, Standard, and Premium tier per service. Every tier owns its current price, currency, delivery, revisions, inclusions, exclusions, requirements, recommendation, activity, and order.
- `service_features` defines service-specific boolean, number, or bilingual-text comparison rows. `package_feature_values` stores one value per package/feature pair.
- `project_requests` references the chosen service/package when still present, but also stores immutable names, price, currency, delivery, revisions, feature values, inclusions, and exclusions. Later catalog edits cannot rewrite the commercial agreement received by the administrator.

## Media lifecycle

`project_media` is the normalized ordered gallery for uploaded images/videos and external YouTube/Vimeo URLs. It stores provider IDs, secure URLs, thumbnail/metadata fields, cover selection, and ordering. `media_assets` is the shared deletion registry. The backend validates extension, MIME declaration, signature/content structure, and size before upload. Development falls back to API-served local media when Cloudinary is not configured; production requires Cloudinary and never silently uses local storage. Commercial-request attachments use authenticated Cloudinary assets and short-lived signed admin URLs. Deleting a record destroys the stored asset only after reference checks; referenced projects/services are archived instead of hard-deleted.

## Security boundaries

No registration route exists. Argon2 passwords, short access cookies, rotating/revocable refresh cookies, UUID-normalized JWT subjects, lockout, exact credentialed CORS, unsafe-method Origin checks, trusted hosts, dynamically configured CSP API origins, audit logs, honeypots, throttling, Turnstile, allowlisted upload signatures, and generic production errors are enforced server-side. Production refuses obvious/default secrets, non-PostgreSQL databases, non-HTTPS public URLs, missing Cloudinary/Turnstile configuration, and broad host/origin configuration. Browser-submitted prices are display hints only and are ignored by persistence logic.

The in-memory rate limiter is appropriate for one API process. Before horizontal scaling, move throttling to a trusted shared store such as Redis and re-test Railway proxy client-IP handling.
