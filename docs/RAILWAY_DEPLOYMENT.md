# Railway production deployment

This guide deploys the portfolio as three services in one Railway project:

- portfolio-web: Next.js
- portfolio-api: FastAPI
- PostgreSQL: Railway-managed PostgreSQL

It reflects the repository configuration as audited on 2026-08-21. It uses placeholders only. Never commit or paste real secrets into this repository.

## 1. Architecture

    Internet
       |
       | HTTPS
       v
    +---------------------------+
    | portfolio-web             |
    | Next.js on Railway        |
    +---------------------------+
       |                 |
       | browser API     | server-side content fetches
       +--------+--------+
                | HTTPS
                v
    +---------------------------+
    | portfolio-api             |
    | FastAPI on Railway        |
    +---------------------------+
       | private Railway network
       v
    +---------------------------+
    | Railway PostgreSQL        |
    | persistent database       |
    +---------------------------+

    portfolio-api also calls:
      + Cloudinary: permanent production media
      + Resend: transactional notifications
      + Cloudflare Turnstile: server-side challenge verification
      + GitHub API: allowlisted repository data

Public pages and the admin application make credentialed browser requests to the API. Next.js also reads public content from the API while rendering and revalidating pages. PostgreSQL is not exposed to the browser. Important media is never stored on Railway's ephemeral application filesystem.

## 2. Prerequisites

Prepare these before creating production services:

- A Railway account and a plan suitable for three continuously deployed services.
- A GitHub repository containing this monorepo, with Railway authorized to read it.
- A Cloudinary cloud name, API key, and API secret.
- A Cloudflare Turnstile widget with the eventual frontend hostnames.
- A strong, unique JWT signing secret.
- Optionally, a Resend API key and verified sending domain.
- Optionally, a GitHub token with only the access required for the allowlisted repositories.
- The current Railway CLI if you will run the one-time seed and admin commands from a terminal.

Generate a JWT secret locally, then copy the output directly into Railway:

    python -c "import secrets; print(secrets.token_urlsafe(48))"

Do not reuse this value for any other application.

## 3. Create the Railway project

1. Sign in to Railway.
2. Create an empty project in the intended workspace and environment.
3. Give it an identifiable name, such as portfolio-production.
4. Keep the default production environment unless you deliberately maintain separate staging and production environments.
5. Do not deploy an application service until its required variables are ready; production configuration intentionally fails closed.

Railway's interface changes occasionally. The stable concepts are Project, Environment, Service, Source, Variables, Settings, Networking, Deployments, Logs, and Metrics. Use those sections even if a button label is slightly different.

## 4. Connect the GitHub monorepo

Create two empty services from the same GitHub repository and name them:

- portfolio-api
- portfolio-web

Configure each service separately:

| Service | Root directory | Railway config file |
| --- | --- | --- |
| portfolio-api | /apps/api | /apps/api/railway.json |
| portfolio-web | /apps/web | /apps/web/railway.json |

The leading slash is the form Railway documents for repository-relative paths. Railway's [monorepo documentation](https://docs.railway.com/deployments/monorepo) states that the config-as-code file does not automatically follow the service Root Directory. Set the Custom Config File path explicitly for each service. Otherwise Railway can ignore these checked-in start, pre-deploy, and health-check settings.

Both services use their local Dockerfile. Do not set a repository-root Dockerfile path or a repository-root build context.

Optional watch paths can prevent an unrelated application change from rebuilding both services:

- API: /apps/api/**
- Web: /apps/web/**

Include shared root files in a watch path if a future change makes either service depend on them.

## 5. Create PostgreSQL

1. In the same Railway project and production environment, add a PostgreSQL database service from Railway's database templates.
2. Wait until it reports healthy.
3. Open portfolio-api Variables.
4. Add DATABASE_URL by using Railway's reference-variable picker and selecting the PostgreSQL service's DATABASE_URL. The resulting expression is normally:

       DATABASE_URL=${{Postgres.DATABASE_URL}}

   Replace Postgres with the actual service name if it differs.
5. Use the private service variable for the deployed API. Do not use a public TCP URL unless an external client genuinely needs it.

Railway commonly supplies a provider URL beginning with postgresql://. The API normalizes postgresql:// and legacy postgres:// URLs to SQLAlchemy's async asyncpg form. It also translates a provider sslmode query parameter to the asyncpg ssl parameter.

Do not run database reset, drop, or create-all logic in production. Schema state is owned by Alembic.

See Railway's [PostgreSQL service documentation](https://docs.railway.com/databases/postgresql) and [variable-reference documentation](https://docs.railway.com/variables/reference).

## 6. Deploy the backend

### Service settings

- Service: portfolio-api
- Source: this GitHub repository
- Root directory: /apps/api
- Custom config file: /apps/api/railway.json
- Builder: Dockerfile, supplied by railway.json
- Pre-deploy command: alembic upgrade head
- Start command: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level ${LOG_LEVEL:-info}
- Health-check path: /api/v1/ready
- Health-check timeout: 120 seconds

The Docker image installs locked production dependencies, runs as an unprivileged user, and binds Uvicorn to Railway's dynamic PORT. A separate Gunicorn layer is unnecessary for this application. Begin with one API replica because the current rate limiter is process-local; see Residual operational limits below.

### Required backend variables

Use temporary generated Railway frontend and API domains first, then repeat the domain-change procedure in section 17 for custom domains.

| Variable | Classification | Production value |
| --- | --- | --- |
| ENVIRONMENT | REQUIRED IN PRODUCTION | production |
| DATABASE_URL | REQUIRED / SERVER SECRET | Railway PostgreSQL reference |
| FRONTEND_URL | REQUIRED | Exact public frontend HTTPS origin |
| CORS_ORIGINS | REQUIRED | Comma-separated exact frontend HTTPS origins |
| API_PUBLIC_URL | REQUIRED | Exact public API HTTPS origin, without /api/v1 |
| TRUSTED_HOSTS | REQUIRED | Comma-separated API hostnames, without schemes or paths |
| TRUST_PROXY_HEADERS | REQUIRED ON RAILWAY | true |
| JWT_SECRET_KEY | REQUIRED / SERVER SECRET | Unique random value, at least 32 characters |
| CLOUDINARY_CLOUD_NAME | REQUIRED | Cloudinary cloud name |
| CLOUDINARY_API_KEY | REQUIRED / SERVER SECRET | Cloudinary API key |
| CLOUDINARY_API_SECRET | REQUIRED / SERVER SECRET | Cloudinary API secret |
| TURNSTILE_SECRET_KEY | REQUIRED / SERVER SECRET | Turnstile secret key |
| TURNSTILE_EXPECTED_HOSTNAMES | REQUIRED | Comma-separated frontend hostnames |
| LOG_LEVEL | OPTIONAL | info |

TRUSTED_HOSTS contains hostnames only, for example:

    portfolio-api-production.up.railway.app,api.example.com

CORS_ORIGINS contains full origins and must never contain a wildcard:

    https://portfolio-web-production.up.railway.app

If both apex and www are active frontend origins:

    https://example.com,https://www.example.com

### Optional backend variables

| Variable | Classification | Purpose |
| --- | --- | --- |
| APP_NAME | OPTIONAL | API display name |
| DATABASE_POOL_SIZE | OPTIONAL | Base connection pool size |
| DATABASE_MAX_OVERFLOW | OPTIONAL | Temporary extra connections |
| DATABASE_POOL_RECYCLE_SECONDS | OPTIONAL | Recycle aged connections |
| ACCESS_TOKEN_EXPIRE_MINUTES | OPTIONAL | Access-cookie lifetime |
| REFRESH_TOKEN_EXPIRE_DAYS | OPTIONAL | Refresh-cookie lifetime |
| COOKIE_SAMESITE | OPTIONAL | lax by default |
| COOKIE_DOMAIN | OPTIONAL | Blank for host-only cookies |
| MAX_IMAGE_UPLOAD_MB | OPTIONAL | Validated image limit |
| MAX_VIDEO_UPLOAD_MB | OPTIONAL | Validated video limit |
| MAX_REQUEST_ATTACHMENT_MB | OPTIONAL | Validated private attachment limit |
| RESEND_API_KEY | OPTIONAL / SERVER SECRET | Enables notification email |
| EMAIL_FROM | OPTIONAL | Verified sender |
| EMAIL_TO | OPTIONAL | Owner notification recipient |
| GITHUB_USERNAME | OPTIONAL | Default GitHub owner |
| GITHUB_TOKEN | OPTIONAL / SERVER SECRET | Authenticated GitHub API calls |
| RATE_LIMIT_MAX_KEYS | OPTIONAL | Bounds in-memory limiter state |

LOCAL_MEDIA_DIR is DEVELOPMENT ONLY. It is intentionally unavailable as a production persistence fallback.

### First deployment

1. Add every required variable.
2. Generate an API domain in the service Networking section.
3. Put that exact HTTPS URL in API_PUBLIC_URL.
4. Put its hostname in TRUSTED_HOSTS.
5. Trigger or redeploy the service after all staged changes are applied.
6. Confirm the pre-deploy log completed the migration.
7. Confirm the deployment health check reaches HTTP 200.
8. Visit:

       https://YOUR-API-DOMAIN/api/v1/health
       https://YOUR-API-DOMAIN/api/v1/ready

health checks the process. ready also verifies database connectivity. In production, /docs, /redoc, and /openapi.json intentionally return 404.

## 7. Database migrations

The checked-in API railway.json uses Railway's pre-deploy phase:

    alembic upgrade head

This is the migration mechanism for normal deployments. It runs before the new application starts and separately from every Uvicorn worker. Railway documents that a failed [pre-deploy command](https://docs.railway.com/deployments/pre-deploy-command) prevents the application deployment.

Safe procedure:

1. Back up production before a risky or destructive schema change.
2. Review the Alembic revision in the pull request.
3. Prefer backward-compatible, expand-and-contract migrations when the old and new application may overlap.
4. Deploy the API and watch the pre-deploy logs.
5. Confirm /api/v1/ready before exercising write routes.
6. Run alembic current from a Railway SSH session if the reported revision is uncertain.

Do not add alembic upgrade head to the Uvicorn start command. Do not run it independently in every replica. Do not run alembic downgrade during an incident unless the revision's downgrade path and data-loss implications were explicitly reviewed.

## 8. Optional initial content seed

portfolio-seed is optional. It inserts missing starter profile, skill categories, projects, draft services, experience, education, activity, placeholder social links, and an empty GitHub allowlist. It does not create an administrator. It checks for existing records and is additive, but it is not a substitute for a database backup and its placeholder content must be reviewed before publishing.

To seed a new, empty production database:

1. Install and authenticate the current Railway CLI.
2. Link it to the project/environment, or copy the exact SSH command from the service menu.
3. Open an interactive session in the API service:

       railway ssh --service portfolio-api

4. Inside the deployed container run:

       portfolio-seed

5. Exit and inspect the content through the admin dashboard.

Run this once only if the starter content is desired. Never place it in the start or pre-deploy command.

Railway documents the current interactive command at [railway ssh](https://docs.railway.com/cli/ssh).

## 9. Create the first administrator

portfolio-admin is interactive. It asks for the email and obtains the password twice through getpass, so the password is not supplied as a command argument or stored in shell history. It requires at least 12 characters and refuses to replace an existing account.

1. Open an interactive API session:

       railway ssh --service portfolio-api

2. Run:

       portfolio-admin

3. Enter the email.
4. Enter a unique password from a password manager at both hidden prompts.
5. Exit the session.
6. Log in through /admin and verify the authentication flow.

Never automate this command on each deployment. Do not store an admin password in Railway variables or source control. Create additional admin-management tooling before adding multiple administrators; do not manipulate password hashes manually.

## 10. Deploy the frontend

### Service settings

- Service: portfolio-web
- Source: the same GitHub repository
- Root directory: /apps/web
- Custom config file: /apps/web/railway.json
- Builder: Dockerfile
- Build: npm ci followed by next build inside the Dockerfile
- Runtime: Next.js standalone server with node server.js
- Health-check path: /robots.txt

The standalone server reads Railway's PORT and HOSTNAME=0.0.0.0. The production build validates public URLs and refuses to build with missing or unsafe production values.

### Frontend variables

| Variable | Classification | Production value |
| --- | --- | --- |
| APP_ENVIRONMENT | REQUIRED IN PRODUCTION | production |
| NEXT_PUBLIC_SITE_URL | PUBLIC FRONTEND / REQUIRED | Exact frontend HTTPS origin |
| NEXT_PUBLIC_API_URL | PUBLIC FRONTEND / REQUIRED | Exact API URL ending in /api/v1 |
| NEXT_PUBLIC_TURNSTILE_SITE_KEY | PUBLIC FRONTEND / REQUIRED | Turnstile site key |
| NEXT_PUBLIC_GITHUB_USERNAME | PUBLIC FRONTEND / OPTIONAL | Public GitHub username |
| CONTENT_REVALIDATE_SECONDS | SERVER/BUILD / OPTIONAL | 60, or 0 to disable caching |

NEXT_PUBLIC variables are embedded in browser-visible assets. Never use them for Cloudinary API secrets, Turnstile secrets, JWT secrets, Resend keys, database URLs, or GitHub tokens.

Example:

    APP_ENVIRONMENT=production
    NEXT_PUBLIC_SITE_URL=https://YOUR-WEB-DOMAIN
    NEXT_PUBLIC_API_URL=https://YOUR-API-DOMAIN/api/v1
    NEXT_PUBLIC_TURNSTILE_SITE_KEY=<public-site-key>
    CONTENT_REVALIDATE_SECONDS=60

Create the frontend generated domain first, update NEXT_PUBLIC_SITE_URL, and redeploy. Update the API's FRONTEND_URL, CORS_ORIGINS, and TURNSTILE_EXPECTED_HOSTNAMES to match before testing forms and admin authentication.

## 11. CORS setup

The API accepts credentialed requests only from exact configured origins.

For one generated frontend domain:

    FRONTEND_URL=https://YOUR-WEB-DOMAIN
    CORS_ORIGINS=https://YOUR-WEB-DOMAIN

For apex and www custom domains:

    FRONTEND_URL=https://example.com
    CORS_ORIGINS=https://example.com,https://www.example.com

Rules:

- Include scheme and hostname, but no path, query, fragment, or trailing wildcard.
- Never use Access-Control-Allow-Origin: * with credentialed requests.
- Do not add the API origin unless a real frontend is served there.
- Preview deployments do not automatically receive access. Use a deliberate staging environment and explicit staging origin instead of a broad pattern.
- Administrative and authentication unsafe methods also validate the Origin header in production.

## 12. Cookies and authentication

The API sets HttpOnly access and refresh cookies. Production cookies are Secure. The access and refresh paths are intentionally scoped, refresh tokens rotate, and logout revokes the stored refresh session.

### Railway-generated domains

Use:

    COOKIE_SAMESITE=lax
    COOKIE_DOMAIN=

Keep COOKIE_DOMAIN blank. Browsers must not be given a shared .railway.app cookie domain. Browser behavior for distinct generated domains can be affected by cross-site cookie/privacy policies. Test login, refresh, and logout in the target browsers before launch.

### Custom sibling domains

For:

    Frontend: https://example.com
    API:      https://api.example.com

the recommended values remain:

    COOKIE_SAMESITE=lax
    COOKIE_DOMAIN=

Host-only API cookies are sent to api.example.com when the frontend performs credentialed requests. Both are same-site under example.com, while the frontend cannot directly read HttpOnly cookies.

If the frontend and API must live on unrelated registrable domains, COOKIE_SAMESITE=none may be necessary. Secure is already enforced in production, but browser third-party-cookie blocking can still make that topology unreliable. Prefer sibling custom domains.

After changing domains, clear old cookies or use a private window when testing. Rotate JWT_SECRET_KEY only as a planned session-invalidation event because existing sessions become invalid.

## 13. Cloudinary

Set on the API only:

- CLOUDINARY_CLOUD_NAME
- CLOUDINARY_API_KEY
- CLOUDINARY_API_SECRET

Production startup fails if they are missing. Public portfolio images/videos are uploaded after server-side type, extension, and size checks. Commercial-request attachments use authenticated Cloudinary delivery and receive short-lived signed admin download URLs. The secret never reaches the browser.

Cloudinary documents that authenticated assets require signed access and are not publicly deliverable by ordinary URLs in [access-controlled media](https://cloudinary.com/documentation/control_access_to_media).

Do not mount or depend on apps/api/uploads in production. Railway application filesystems are ephemeral. Test upload, render, replacement, deletion, and private attachment access after deployment.

Existing attachments uploaded by an older release as public Cloudinary assets are not retroactively converted by this code. Inventory and migrate/delete those manually before treating legacy attachments as private.

## 14. Cloudflare Turnstile

Frontend:

- NEXT_PUBLIC_TURNSTILE_SITE_KEY: public widget key

Backend:

- TURNSTILE_SECRET_KEY: server-only secret
- TURNSTILE_EXPECTED_HOSTNAMES: exact frontend hostname list

In the Turnstile dashboard, add every active frontend hostname, without scheme or path. Add both example.com and www.example.com if both serve forms. Add the temporary Railway frontend hostname during the initial phase, then remove it if it is no longer used.

The API verifies tokens server-side, validates the returned hostname, and fails closed on invalid tokens. Provider/network failures return a service error rather than silently accepting the request. Cloudflare requires server-side Siteverify validation and documents hostname restrictions in its [Turnstile validation guide](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/) and [hostname management guide](https://developers.cloudflare.com/turnstile/additional-configuration/hostname-management/any-hostname/).

## 15. Resend

Set on the API:

- RESEND_API_KEY
- EMAIL_FROM
- EMAIL_TO

Verify the sending domain in Resend, including its required DNS records, before selecting EMAIL_FROM. Resend documents domain verification in its [domain guide](https://resend.com/docs/dashboard/domains/introduction).

EMAIL_FROM should be a fixed application-controlled sender, for example:

    Portfolio <notifications@example.com>

User input is never used as a mail header. Notification HTML is escaped. A commercial request is committed to PostgreSQL before email is attempted, so a Resend outage does not discard the request. Email remains optional at application startup; if omitted, the database workflow works but notifications do not.

## 16. GitHub integration

Optional API variables:

- GITHUB_USERNAME
- GITHUB_TOKEN

Optional frontend variable:

- NEXT_PUBLIC_GITHUB_USERNAME

The token stays on the API. Give it the narrowest repository access possible and no write permission unless a future feature explicitly requires it. Configure the repository allowlist through the private github_allowlist site setting. Repository identifiers are validated before the API calls GitHub; arbitrary URLs are not fetched.

The API caches responses and rate-limits the provider route, but GitHub availability and rate limits remain external dependencies. Public portfolio rendering must be checked both with and without a valid GitHub response.

## 17. Custom domains

Recommended final topology:

    https://example.com
    https://www.example.com        optional redirect or secondary origin
    https://api.example.com

1. Add example.com to portfolio-web Networking and follow Railway's displayed DNS instructions.
2. Add www.example.com if wanted. Prefer redirecting one canonical host to the other.
3. Add api.example.com to portfolio-api and create the shown DNS record.
4. Wait for DNS and Railway certificate validation.
5. Update frontend variables:

       NEXT_PUBLIC_SITE_URL=https://example.com
       NEXT_PUBLIC_API_URL=https://api.example.com/api/v1

6. Update API variables:

       FRONTEND_URL=https://example.com
       CORS_ORIGINS=https://example.com,https://www.example.com
       API_PUBLIC_URL=https://api.example.com
       TRUSTED_HOSTS=api.example.com
       COOKIE_DOMAIN=
       COOKIE_SAMESITE=lax
       TURNSTILE_EXPECTED_HOSTNAMES=example.com,www.example.com

7. Update the Turnstile widget's hostname allowlist.
8. Verify the Resend domain if email uses the new domain.
9. Cloudinary credentials normally do not change. If transformations or delivery URLs have domain allowlists in your account, update those account-level policies.
10. Redeploy API and web after variable changes. NEXT_PUBLIC values require a new frontend build.
11. Repeat the complete authentication and form smoke tests.
12. Remove old generated domains from CORS/Turnstile only after confirming no clients use them.

Generated domain names are assigned by Railway; do not assume the examples in this guide will be available. Railway explains the current DNS records and managed certificates in its [domain documentation](https://docs.railway.com/networking/domains/working-with-domains).

## 18. HTTPS

Railway terminates TLS and manages certificates for generated and correctly configured custom domains. Always publish HTTPS URLs in application variables. The API enables HSTS only in production and sends CSP, frame, referrer, permissions, and MIME-sniffing protections. Do not put an additional proxy in front without reviewing forwarded-host/IP trust and TLS behavior.

## 19. Deployment verification

Record the deployed commit and timestamp, then complete every item.

### Public site

- Open /en and confirm English content, navigation, metadata, and no console errors.
- Open /ar and confirm Arabic content, RTL layout, navigation, and typography.
- Open several project detail pages in both languages.
- Confirm project images/video and responsive image loading.
- Open services and service detail/package views.
- Exercise package comparisons and FAQ presentation.
- Submit every public form with valid data.
- Confirm validation for malformed email, overly long text, invalid IDs, and disallowed attachment types.
- Confirm Turnstile blocks invalid/missing challenges in production.
- Check not-found and error behavior.
- Inspect /sitemap.xml, /robots.txt, and the social preview image.
- Confirm the canonical site URL and structured metadata use the final domain.

### Admin

- Confirm /admin is marked noindex/nofollow.
- Log in with the initial administrator.
- Confirm the access cookie is HttpOnly and Secure.
- Allow the access token to expire or exercise refresh explicitly; confirm transparent rotation.
- Log out and confirm the refresh session is revoked.
- From a logged-out session, call representative admin GET/POST/PATCH/DELETE APIs and confirm 401/403.
- Create, update, publish/unpublish, reorder, and delete a test project.
- Upload an image and video; test cover, reorder, replacement, and delete.
- Edit profile and hero content.
- Create/update services.
- Create/update packages.
- Create/update comparison rows.
- Create/update FAQs.
- Open a commercial request, download its attachment through the signed URL, change status, and export CSV.
- Confirm public users cannot fetch request details or the raw attachment.
- Remove test content when finished.

### Integrations

- Cloudinary: verify new permanent public media remains after an API redeploy.
- Cloudinary: verify a new request attachment is authenticated/private and its admin URL expires.
- Resend: receive a notification from the verified sender.
- Resend: temporarily simulate/configure a rejected send in staging and confirm the database request persists.
- Turnstile: test valid, invalid, expired, and wrong-hostname tokens.
- GitHub: verify only allowlisted repositories load, then verify a provider error is handled without leaking the token.

### Database

- Confirm the API reports ready.
- Confirm Alembic is at head.
- Create a harmless test record, redeploy API and web, and confirm it remains.
- Confirm commercial package fields on an existing request do not change when the package is edited later.
- Confirm backups are configured and complete a restore drill before launch.

### Security and operations

- Confirm API docs endpoints return 404 in production.
- Confirm malformed requests return generic errors without stack traces.
- Confirm Access-Control-Allow-Origin is the requesting configured origin, never a wildcard.
- Confirm an unconfigured Origin cannot perform an admin/auth mutation.
- Confirm HSTS and Content-Security-Policy are present on HTTPS responses.
- Confirm secrets do not appear in frontend JavaScript, build logs, runtime logs, or error responses.
- Confirm no local upload path is used in production.
- Confirm rate-limit responses occur on repeated login/form/provider requests in staging.
- Test from browsers with third-party-cookie protection enabled.

## 20. Redeployment

A push to the connected default GitHub branch triggers each affected Railway service. With watch paths, only the service whose files changed should rebuild.

API sequence:

1. Docker image builds from apps/api.
2. Alembic pre-deploy runs.
3. Uvicorn starts on PORT.
4. Railway waits for /api/v1/ready.
5. Healthy traffic is switched to the new deployment.

Web sequence:

1. Docker image builds from apps/web.
2. Production public variables are validated during next build.
3. The standalone server starts on PORT.
4. Railway waits for /robots.txt.

Changing a Railway variable triggers a redeploy. NEXT_PUBLIC values are build-time public configuration and must rebuild the web image.

## 21. Database backup

At the time this guide was verified, Railway documents scheduled/manual volume backups, point-in-time recovery where enabled, and user-managed logical dumps. Availability can depend on plan and current platform configuration; confirm the options shown in the PostgreSQL service before relying on them.

Recommended layers:

1. Enable an appropriate scheduled volume-backup policy in the PostgreSQL Backups tab.
2. Create a manual backup immediately before a risky migration.
3. Enable point-in-time recovery if the selected plan and risk profile warrant it.
4. Schedule encrypted pg_dump exports to storage outside the Railway project.
5. Perform and document a restore drill into an isolated database.
6. Protect access to backups and test restoration after credential changes.

Do not treat application rollback as database rollback. Do not delete or wipe the PostgreSQL volume as a recovery experiment. Railway's current procedures and limitations are documented in [Back Up and Restore Postgres](https://docs.railway.com/guides/postgres-backups-restores).

## 22. Rollback

For a bad web or API release, open the service Deployments tab, choose the last known-good deployment, and use its Rollback action. Railway currently restores that deployment's image and custom variables when the image is still within the plan's retention window; see [Deployment Actions](https://docs.railway.com/deployments/deployment-actions).

Database warning:

- Rolling the API image back does not reverse an Alembic migration.
- A newly required column can break old code; a removed/renamed column can make rollback impossible.
- Prefer expand-and-contract schema changes so old and new code can coexist.
- For a destructive migration incident, stop writes if necessary, preserve evidence, and choose between a reviewed forward fix and a tested database restore.
- Never run alembic downgrade blindly against production.

After rollback, verify /ready, authentication, writes, and integration calls. Then fix forward through the normal reviewed deployment path.

## 23. Monitoring

Monitor all three services:

- Deployments: build, pre-deploy, health-check, active/crashed status.
- Logs: application errors, status codes, request IDs, migration failures, provider failures.
- Metrics: CPU, memory, network, disk/volume, and database resource use.
- PostgreSQL: connections, storage growth, slow/failing operations, backup status.
- Alerts: crashed services, failed deployments, usage thresholds, and database capacity.

The API logs structured request context without request bodies or secrets. Correlate client-visible failures with the sanitized X-Request-ID. Configure log retention/exports appropriate to operational and privacy requirements. Railway describes its current [metrics](https://docs.railway.com/observability/metrics), [logs](https://docs.railway.com/observability/logs), and [deployment alerts](https://docs.railway.com/guides/alerts-crashes-failed-deploys).

## 24. Cost control

Railway billing is usage-based and its plans change. Review the current plan page instead of relying on a hardcoded price.

- Set a monthly usage notification suitable for a small portfolio.
- If available for the selected plan, set a hard usage limit only after understanding that reaching it can stop services.
- Watch build frequency, egress, PostgreSQL volume growth, backup storage, CPU, and RAM.
- Use watch paths to avoid unnecessary monorepo builds.
- Start with one modest web replica and one API replica; scale only from measured demand.
- Investigate traffic abuse before raising resource limits.

See Railway's current [cost-control documentation](https://docs.railway.com/pricing/cost-control).

## 25. Troubleshooting

### Frontend cannot reach the API

- Confirm NEXT_PUBLIC_API_URL is HTTPS and ends exactly in /api/v1.
- Redeploy the frontend after changing a NEXT_PUBLIC value.
- Open the API health and readiness URLs directly.
- Inspect browser network errors and API logs using the request ID.

### CORS error

- Compare the browser Origin exactly with CORS_ORIGINS.
- Include scheme and port where applicable; do not include a path.
- Confirm credentialed requests use credentials: include.
- Do not solve it with a wildcard.

### Database connection failure

- Confirm DATABASE_URL references the correct Railway PostgreSQL service/environment.
- Confirm the database itself is healthy.
- Check whether an external/public URL was mistakenly used inside Railway.
- Inspect asyncpg/SSL errors without printing the URL.
- Review pool sizes against the database connection limit.

### Migration failure

- Read the pre-deploy logs and identify the failing revision.
- Run alembic current and alembic history in an API SSH session.
- Do not stamp, downgrade, or edit the production revision table until the cause and data state are understood.
- Restore a backup or ship a reviewed forward migration as appropriate.

### Admin login cookies are not stored

- Confirm API and frontend are HTTPS.
- Check Secure, HttpOnly, SameSite, Domain, and Path in browser developer tools.
- Keep COOKIE_DOMAIN blank for generated domains and the normal sibling-domain design.
- Confirm browser requests include credentials.
- Confirm CORS returns the exact frontend origin and allows credentials.
- Remove stale cookies after a domain change.

### Cloudinary upload failure

- Confirm all three Cloudinary variables are on the API service.
- Check API log status without exposing the API secret.
- Verify allowed extension, MIME signature, file structure, and configured size.
- Confirm Cloudinary account quota and asset access mode.

### Turnstile failure

- Confirm site key is on the frontend and secret is only on the API.
- Add the exact frontend hostname in both Cloudflare and TURNSTILE_EXPECTED_HOSTNAMES.
- Redeploy the frontend after changing the site key.
- Check token expiration, hostname, and Siteverify availability.

### Resend failure

- Verify RESEND_API_KEY, EMAIL_FROM, and EMAIL_TO.
- Confirm the sender domain and DNS records are verified.
- Check Resend and API logs.
- Confirm the request exists in PostgreSQL; email failure must not remove it.

### Next.js does not bind to Railway PORT

- Confirm /apps/web/railway.json is the selected Custom Config File.
- Confirm the standalone runtime is node server.js.
- Do not override PORT or HOSTNAME with fixed local values.
- Inspect startup logs for production environment validation.

### FastAPI health check fails

- Use /api/v1/ready, not /docs.
- Check production configuration validation, migration logs, and database connectivity.
- Confirm Uvicorn binds 0.0.0.0 and $PORT.
- Confirm TRUSTED_HOSTS includes the public API hostname.

### Deployment succeeds but returns 502

- Inspect runtime logs for a crashed process or wrong start command.
- Confirm the service listens on Railway's PORT.
- Confirm the health-check path is correct.
- Check memory/CPU limits and dependency startup failures.
- Confirm config-file paths and service root directories.

### Wrong environment variable

- Compare names character-for-character with section 26 below.
- Check that variables were added to the correct service and environment.
- Apply staged changes and redeploy.
- Never paste secrets into logs, issue trackers, screenshots, or the repository.

### Generated domain changes

- Update SITE/API URLs, CORS, trusted hosts, Turnstile hostnames, and any provider allowlists.
- Redeploy both services.
- Clear stale cookies and repeat the full auth/form smoke tests.

### Custom domain or DNS problems

- Use the exact DNS target Railway displays.
- Remove conflicting A/AAAA/CNAME records.
- Allow normal DNS propagation time.
- Confirm certificate issuance in Railway before forcing HTTPS traffic.
- Verify apex and www independently and choose a canonical redirect.

## 26. Complete environment-variable inventory

Names only, grouped by service:

portfolio-api:

- ENVIRONMENT
- APP_NAME
- LOG_LEVEL
- DATABASE_URL
- DATABASE_POOL_SIZE
- DATABASE_MAX_OVERFLOW
- DATABASE_POOL_RECYCLE_SECONDS
- FRONTEND_URL
- CORS_ORIGINS
- API_PUBLIC_URL
- TRUSTED_HOSTS
- TRUST_PROXY_HEADERS
- JWT_SECRET_KEY
- ACCESS_TOKEN_EXPIRE_MINUTES
- REFRESH_TOKEN_EXPIRE_DAYS
- COOKIE_SAMESITE
- COOKIE_DOMAIN
- CLOUDINARY_CLOUD_NAME
- CLOUDINARY_API_KEY
- CLOUDINARY_API_SECRET
- MAX_IMAGE_UPLOAD_MB
- MAX_VIDEO_UPLOAD_MB
- MAX_REQUEST_ATTACHMENT_MB
- LOCAL_MEDIA_DIR (development only)
- TURNSTILE_SECRET_KEY
- TURNSTILE_EXPECTED_HOSTNAMES
- RESEND_API_KEY
- EMAIL_FROM
- EMAIL_TO
- GITHUB_USERNAME
- GITHUB_TOKEN
- RATE_LIMIT_MAX_KEYS
- PORT (provided by Railway)

portfolio-web:

- APP_ENVIRONMENT
- NEXT_PUBLIC_SITE_URL
- NEXT_PUBLIC_API_URL
- NEXT_PUBLIC_TURNSTILE_SITE_KEY
- NEXT_PUBLIC_GITHUB_USERNAME
- CONTENT_REVALIDATE_SECONDS
- PORT (provided by Railway)
- HOSTNAME (set in the Docker image)

local Docker Compose additionally uses:

- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD

## Residual operational limits

- The request rate limiter is in-memory and per API process. Keep one API replica initially. Before horizontal API scaling, move rate-limit state to a shared trusted store such as Redis and test proxy client-IP handling.
- Production behavior of real Cloudinary, Resend, Turnstile, GitHub, DNS, browser privacy controls, and Railway resources cannot be fully validated locally.
- Legacy request attachments created before authenticated Cloudinary delivery was introduced require a separate inventory and remediation.
- Backup and point-in-time recovery availability depends on the Railway plan and options visible when deployed.
- This deployment configuration reduces identified risk; it is not a claim that the application is completely secure.
