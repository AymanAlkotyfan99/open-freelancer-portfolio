# REST API

Base prefix: `/api/v1`. OpenAPI is available at `/docs` outside production. List endpoints use `page`, `page_size`, search/filter parameters, and a `{items,page,page_size,total,pages}` envelope unless `paginated=false` is supported.

## Public portfolio

- `GET /profile`, `/skills`, `/skill-categories`, `/experiences`, `/education`, `/activities`, `/social-links`
- `GET /projects` with search, skill, category, status, sort and pagination; `GET /projects/{slug}`
- `GET /services` with search, skill, category and pagination
- `GET /services/{slug}`, `/services/{slug}/packages`, `/services/{slug}/comparison`
- `POST /contact`
- `POST /project-requests` for an active package on a published/available service
- `POST /custom-offer-requests` when no package applies
- `POST /project-requests/{reference}/attachment` for PDF, DOCX, PNG, JPG/JPEG up to the configured limit

Request creation loads the service/package and feature values from the database, rejects unavailable selections, ignores manipulated display values, commits the immutable snapshot, and only then attempts email. Email failure never loses the request. Success returns a private non-sequential reference such as `AN-…`.

## Authentication and administration

Authentication: `POST /auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/change-password`; `GET /auth/me`. Access and refresh tokens are HttpOnly cookies.

Purpose-built admin endpoints cover:

- overview counts and recent requests;
- project CRUD/archive, media upload/external media/edit/delete/reorder/cover;
- service CRUD/archive, three-tier package CRUD, and typed feature matrix CRUD/reorder;
- request list/detail/status/private notes and `GET /admin/project-requests/export.csv`;
- profile content and verified photo replacement/removal.

Legacy content resources remain available for skills, experience, education, activities, social links, settings, contact messages, and audit logs. Mutations require authentication and write audit records. Errors use `{"detail":"…"}` with an `X-Request-ID` correlation header.
