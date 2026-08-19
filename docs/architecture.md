# Architecture

The monorepo keeps its original two-application boundary: Next.js 15 App Router in `apps/web` and FastAPI/SQLAlchemy/Alembic in `apps/api`. PostgreSQL is the production source of truth; SQLite is used only by isolated automated tests.

```text
Browser → Next.js (Vercel) → FastAPI /api/v1 (Railway) → Neon PostgreSQL
                                      ├─ Cloudinary (media)
                                      ├─ Resend (notifications)
                                      └─ Turnstile (abuse protection)
```

Public content is explicitly bilingual (`*_en`, `*_ar`). Draft/archived projects and services never enter public endpoints. Project collections batch-load technologies and media; service collections batch-load packages. Detail endpoints load comparison data, FAQs, and related work only when needed. Next caches managed reads for `CONTENT_REVALIDATE_SECONDS` (60 by default); setting it to `0` enables deterministic no-store reads for E2E or immediate-preview environments.

## Commercial data model

- `services` owns bilingual scope, media, category, skills, availability, and publication state.
- `service_packages` allows at most one Basic, Standard, and Premium tier per service. Every tier owns its current price, currency, delivery, revisions, inclusions, exclusions, requirements, recommendation, activity, and order.
- `service_features` defines service-specific boolean, number, or bilingual-text comparison rows. `package_feature_values` stores one value per package/feature pair.
- `project_requests` references the chosen service/package when still present, but also stores immutable names, price, currency, delivery, revisions, feature values, inclusions, and exclusions. Later catalog edits cannot rewrite the commercial agreement received by the administrator.

## Media lifecycle

`project_media` is the normalized ordered gallery for uploaded images/videos and external YouTube/Vimeo URLs. It stores Cloudinary public IDs, secure URLs, thumbnail/metadata fields, cover selection, and ordering. `media_assets` is the shared deletion registry. The backend validates extension, MIME declaration, signature, and size before upload. Deleting a record destroys a Cloudinary asset only after reference checks; referenced projects/services are archived instead of hard-deleted.

## Security boundaries

No registration route exists. Argon2 passwords, short access cookies, rotating refresh cookies, UUID-normalized JWT subjects, lockout, strict CORS, dynamically configured CSP API origins, audit logs, honeypots, throttling, Turnstile, allowlisted upload signatures, and generic production errors are enforced server-side. Browser-submitted prices are display hints only and are ignored by persistence logic.

The in-memory rate limiter is appropriate for a single Railway instance. For horizontal scaling, move throttling to the edge or a managed shared store; Redis is intentionally not added to this architecture.
