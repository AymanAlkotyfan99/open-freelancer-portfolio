# Content management

1. Run `alembic upgrade head`, then `portfolio-seed`. The seed is idempotent: it preserves existing records, adds the 16 suggested services as drafts, and never invents prices, delivery times, revisions, contacts, or social URLs.
2. Create the administrator with `portfolio-admin`; credentials are prompted and never committed.
3. Sign in at `/admin`. The responsive sidebar exposes Overview, Profile, Projects, Project Media, Skills, Services, Packages, Requests, Contact Messages, Experience, Education, Activities, Social Links, Site Settings, and Audit Logs.

## Projects and media

A project needs only English/Arabic names, English/Arabic descriptions, a unique slug, and at least one technology. Images and links are optional. Case-study sections, client facts, ownership, status, links, and feature lists are hidden publicly when empty. Save first, then upload multiple JPG/JPEG/PNG/WebP/AVIF or MP4/WebM files, inspect previews/progress, add YouTube/Vimeo URLs, edit bilingual metadata, choose a cover, and drag to reorder. Archive is recoverable and removes the item publicly.

## Services, packages, and comparison features

A service needs bilingual name/description, slug, and at least one related skill. Optional cover/video/category/scope/inclusion/exclusion/requirement fields do not create commercial claims. Keep a service draft until it is reviewed.

Each service has at most one Basic, Standard, and Premium tier. A configured tier requires bilingual name, non-negative price, currency, positive delivery days, and at least one English deliverable. Tiers can be inactive or recommended. Comparison rows are service-specific and support boolean, number, or bilingual text values. The public comparison renders only active packages and stacks vertically on small screens.

## Requests and profile

The request queue searches and filters persisted inquiries, displays immutable package snapshots, and permits only status/private-note edits; CSV export never exposes data publicly. Profile management controls the hero copy, verified social links, contact CTA, image alt text, crop position, and photo. Replace every bracketed placeholder before launch and verify every outbound URL. Unsaved project/service edits trigger a browser warning, and published records expose a preview link.

Cloudinary deletions are reference-aware. Database backups remain the recovery source for content; Cloudinary retention/backups are configured separately in the provider dashboard.
