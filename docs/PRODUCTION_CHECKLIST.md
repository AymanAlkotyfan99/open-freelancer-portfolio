# Production launch checklist

Use this checklist with [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md). Check an item only after verifying it in the production environment. Record evidence, the deployed commit, and the date in the release record.

## Before deployment

- [ ] The production commit has been reviewed and approved.
- [ ] The working tree contains no real secrets, local databases, uploaded media, build output, or test artifacts.
- [ ] The GitHub repository contains the intended Dockerfiles and both service railway.json files.
- [ ] The API service Root Directory is /apps/api.
- [ ] The API Custom Config File is /apps/api/railway.json.
- [ ] The web service Root Directory is /apps/web.
- [ ] The web Custom Config File is /apps/web/railway.json.
- [ ] The production domains and canonical frontend hostname are decided.
- [ ] Cloudinary, Turnstile, and optional Resend/GitHub accounts are ready.
- [ ] A unique production JWT secret was generated and stored in Railway only.
- [ ] The complete local static, unit, build, migration, and E2E suite passed.
- [ ] Dependency audit results were reviewed; no force upgrade was used.

## Security

- [ ] ENVIRONMENT and APP_ENVIRONMENT are both production on their respective services.
- [ ] JWT_SECRET_KEY is unique, random, at least 32 characters, and not an example value.
- [ ] The JWT secret does not appear in Git, logs, frontend assets, or documentation.
- [ ] Production API docs, Redoc, and OpenAPI endpoints return 404.
- [ ] Production errors do not expose tracebacks, database URLs, provider responses, or secrets.
- [ ] TRUSTED_HOSTS contains only actual API hostnames and no global wildcard.
- [ ] TRUST_PROXY_HEADERS is enabled only behind Railway's proxy.
- [ ] CORS_ORIGINS contains exact HTTPS frontend origins and no wildcard.
- [ ] Logged-out requests cannot access representative admin read or write APIs.
- [ ] Admin/auth unsafe requests from an unconfigured Origin are rejected.
- [ ] Login and refresh rate limits were exercised in staging.
- [ ] Public form, upload, and GitHub-provider rate limits were exercised in staging.
- [ ] HSTS is present on production HTTPS responses.
- [ ] CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, and frame protection are present.
- [ ] Admin routes are noindex/nofollow.
- [ ] Browser bundles contain no server-only variables.
- [ ] Audit/request logs contain useful request IDs but no request bodies or secrets.

## Database

- [ ] Railway PostgreSQL is in the same project/environment as the API.
- [ ] DATABASE_URL uses a Railway reference variable to the intended PostgreSQL service.
- [ ] No application start command drops, resets, seeds, or recreates the database.
- [ ] The API pre-deploy command is alembic upgrade head.
- [ ] The migration pre-deploy completed successfully.
- [ ] alembic current reports the expected head revision.
- [ ] /api/v1/ready returns HTTP 200.
- [ ] A record remains after API and frontend redeployment.
- [ ] A commercial request retains its immutable package snapshot after its package changes.
- [ ] Foreign keys, unique constraints, and deletion behavior were exercised for critical data.
- [ ] Scheduled database backups are enabled where available.
- [ ] A manual pre-launch backup exists.
- [ ] An encrypted logical dump is stored outside the Railway project.
- [ ] A restore drill into an isolated database succeeded.
- [ ] The recovery owner and procedure are documented.

## Backend

- [ ] portfolio-api builds from apps/api/Dockerfile.
- [ ] The container runs as a non-root user.
- [ ] Uvicorn binds 0.0.0.0 and Railway's dynamic PORT.
- [ ] The health-check path is /api/v1/ready.
- [ ] /api/v1/health and /api/v1/ready return expected sanitized responses.
- [ ] Startup fails when mandatory production configuration is deliberately omitted in staging.
- [ ] PostgreSQL provider URLs and SSL settings work in Railway.
- [ ] Database pool settings fit the selected PostgreSQL connection limit.
- [ ] Graceful shutdown disposes database connections.
- [ ] One API replica is used while rate limiting is process-local.
- [ ] No development upload directory is exposed in production.
- [ ] Seed is run only once if its starter content is wanted.
- [ ] The first administrator was created once with the interactive portfolio-admin command.
- [ ] No admin password exists in source, Railway variables, or shell history.

## Frontend

- [ ] portfolio-web builds from apps/web/Dockerfile.
- [ ] The container runs as a non-root user.
- [ ] The Next.js standalone server starts with node server.js.
- [ ] The server binds Railway's dynamic PORT and 0.0.0.0.
- [ ] NEXT_PUBLIC_SITE_URL is the exact canonical HTTPS origin.
- [ ] NEXT_PUBLIC_API_URL is the exact HTTPS API URL ending in /api/v1.
- [ ] NEXT_PUBLIC_TURNSTILE_SITE_KEY is the public site key, not the secret.
- [ ] The production build fails rather than using development content when the API configuration is invalid.
- [ ] /en renders correct English content and LTR layout.
- [ ] /ar renders correct Arabic content and RTL layout.
- [ ] Project, service, package, comparison, and FAQ states render correctly.
- [ ] Loading, empty, not-found, and error states are usable.
- [ ] Canonical metadata, sitemap, robots, structured data, and social image use production domains.
- [ ] /admin is usable but not indexable.
- [ ] No hydration or browser-console errors remain.

## Cloudinary

- [ ] CLOUDINARY_CLOUD_NAME is set on the API only as needed.
- [ ] CLOUDINARY_API_KEY is set on the API only.
- [ ] CLOUDINARY_API_SECRET is set on the API only.
- [ ] Production fails closed when Cloudinary credentials are absent.
- [ ] Allowed image/video/attachment extensions, MIME signatures, content structure, and size limits are enforced.
- [ ] SVG and other unapproved active content cannot be uploaded.
- [ ] Public portfolio image and video upload/render/delete behavior works.
- [ ] New commercial-request attachments are authenticated/private.
- [ ] Admin attachment URLs are signed and expire.
- [ ] Logged-out users cannot download commercial-request attachments.
- [ ] Existing legacy public attachments have been inventoried and migrated or deleted.
- [ ] Media remains available after application redeployment.
- [ ] Railway's ephemeral filesystem is not used for permanent production media.

## Turnstile

- [ ] NEXT_PUBLIC_TURNSTILE_SITE_KEY is configured on the web service.
- [ ] TURNSTILE_SECRET_KEY is configured on the API service only.
- [ ] TURNSTILE_EXPECTED_HOSTNAMES contains every active frontend hostname.
- [ ] The same hostnames are allowed on the Cloudflare widget.
- [ ] Server-side Siteverify succeeds for a valid production form.
- [ ] Missing, invalid, expired, replayed, and wrong-hostname challenges fail.
- [ ] Provider timeout/failure does not silently accept the submission.
- [ ] Temporary Railway hostnames are removed after they are retired.

## Email

- [ ] The Resend sending domain is verified.
- [ ] RESEND_API_KEY is configured on the API only.
- [ ] EMAIL_FROM is a fixed verified application-controlled sender.
- [ ] EMAIL_TO is the intended notification mailbox.
- [ ] User input cannot control email headers.
- [ ] User-provided HTML is escaped in notification messages.
- [ ] A valid request sends the expected notification.
- [ ] A deliberate email failure still leaves the request persisted in PostgreSQL.
- [ ] Email errors do not expose keys or personal request data in public responses.

## Domains

- [ ] Railway-generated domains were tested before custom DNS changes.
- [ ] The web custom domain points to the exact Railway DNS target.
- [ ] The API custom domain points to the exact Railway DNS target.
- [ ] Railway has issued valid HTTPS certificates.
- [ ] Apex/www canonical behavior is deliberate and tested.
- [ ] FRONTEND_URL matches the canonical frontend origin.
- [ ] API_PUBLIC_URL matches the public API origin without /api/v1.
- [ ] CORS_ORIGINS includes every served frontend origin and nothing broader.
- [ ] TRUSTED_HOSTS contains each served API hostname.
- [ ] COOKIE_DOMAIN is blank for host-only cookies.
- [ ] COOKIE_SAMESITE is lax for the recommended same-site sibling domains.
- [ ] Turnstile hostnames were updated after the domain change.
- [ ] Resend domain/sender settings were updated if applicable.
- [ ] Old generated domains are removed from allowlists only after cutover.

## Railway

- [ ] The project contains portfolio-web, portfolio-api, and PostgreSQL services.
- [ ] Each application service uses the intended GitHub branch.
- [ ] Each Custom Config File path is explicitly set.
- [ ] Required variables are in the production environment and correct service.
- [ ] Variable references point to the production PostgreSQL service.
- [ ] API pre-deploy, start, and health-check settings match railway.json.
- [ ] Web start and health-check settings match railway.json.
- [ ] Build and runtime logs show no secrets.
- [ ] Crash/failed-deployment alerts are configured.
- [ ] Usage notifications and an appropriate cost-control policy are configured.
- [ ] CPU, RAM, network, database, and volume metrics are being observed.
- [ ] Deployment rollback is available for the intended retention window.
- [ ] The team knows that application rollback does not reverse migrations.

## After deployment

- [ ] The deployed commit SHA and variable-change record are saved.
- [ ] The API migration revision is recorded.
- [ ] Public and admin smoke tests passed on the production domains.
- [ ] Cloudinary, Turnstile, Resend, and GitHub integrations passed.
- [ ] Authentication passed in the target desktop and mobile browsers.
- [ ] Access refresh and logout/revocation passed.
- [ ] No secret appears in page source, downloaded JavaScript, network payloads, or logs.
- [ ] No production content came from a silent development fallback.
- [ ] Database and Cloudinary content survived redeployment.
- [ ] Test content and test administrator sessions were removed or revoked.
- [ ] Monitoring and alerts were checked after real traffic began.
- [ ] A post-launch backup was created and verified.

## Final smoke test

- [ ] /en
- [ ] /ar
- [ ] Project listing and project details
- [ ] Images and video
- [ ] Services and service details
- [ ] Packages and comparisons
- [ ] FAQs
- [ ] Public forms
- [ ] Turnstile validation
- [ ] Admin login
- [ ] Access-token refresh rotation
- [ ] Admin logout and refresh-session revocation
- [ ] Project CRUD
- [ ] Media upload, reorder, cover, replace, and delete
- [ ] Service CRUD
- [ ] Package CRUD
- [ ] Comparison CRUD
- [ ] FAQ CRUD
- [ ] Commercial-request list, details, status, attachment, and CSV
- [ ] Profile and hero editing
- [ ] GitHub allowlist/provider behavior
- [ ] Resend notification and persistence-on-failure
- [ ] Logged-out admin API denial
- [ ] Exact credentialed CORS
- [ ] Secure/HttpOnly/SameSite cookie attributes
- [ ] Generic production errors with no stack trace
- [ ] API docs disabled
- [ ] Persistence across redeploy
- [ ] Alembic at head
- [ ] Backup restore drill
- [ ] No leaked secret or production filesystem upload

Launch only when all applicable items are checked or an explicit, documented risk acceptance has been approved.
