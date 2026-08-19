"""Add service packages, project media, request snapshots, and managed profile fields.

Revision ID: 20260819_0002
Revises: 20260719_0001
"""

from collections.abc import Iterable

import sqlalchemy as sa

from alembic import op

revision = "20260819_0002"
down_revision = "20260719_0001"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table)}


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _add_columns(table: str, columns: Iterable[sa.Column]) -> None:
    existing = _columns(table)
    missing = [column for column in columns if column.name not in existing]
    if not missing:
        return
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table(table, recreate="always") as batch:
            for column in missing:
                batch.add_column(column)
    else:
        for column in missing:
            op.add_column(table, column)


def _make_nullable(table: str, names: set[str]) -> None:
    columns = {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns(table)}
    targets = [name for name in names if name in columns and not columns[name]["nullable"]]
    if not targets:
        return
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table(table, recreate="always") as batch:
            for name in targets:
                batch.alter_column(name, existing_type=columns[name]["type"], nullable=True)
    else:
        for name in targets:
            op.alter_column(table, name, existing_type=columns[name]["type"], nullable=True)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    json_empty = sa.text("'[]'")
    _add_columns(
        "profiles",
        [
            sa.Column("profile_image_public_id", sa.String(500)),
            sa.Column("profile_image_alt_en", sa.String(300)),
            sa.Column("profile_image_alt_ar", sa.String(300)),
            sa.Column("profile_image_position", sa.String(30), nullable=False, server_default="50% 50%"),
            sa.Column("cv_public_id", sa.String(500)),
            sa.Column("whatsapp", sa.String(100)),
            sa.Column("telegram", sa.String(100)),
            sa.Column("github_url", sa.String(1000)),
            sa.Column("linkedin_url", sa.String(1000)),
            sa.Column("upwork_url", sa.String(1000)),
            sa.Column("availability_status", sa.String(80)),
            sa.Column("hero_heading_en", sa.String(240)),
            sa.Column("hero_heading_ar", sa.String(240)),
            sa.Column("hero_subheading_en", sa.Text()),
            sa.Column("hero_subheading_ar", sa.Text()),
            sa.Column("hero_cta_en", sa.String(120)),
            sa.Column("hero_cta_ar", sa.String(120)),
            sa.Column("contact_cta_en", sa.Text()),
            sa.Column("contact_cta_ar", sa.Text()),
        ],
    )
    _add_columns(
        "projects",
        [
            sa.Column("short_description_en", sa.Text()),
            sa.Column("short_description_ar", sa.Text()),
            sa.Column("demo_url", sa.String(1000)),
            sa.Column("client_name", sa.String(240)),
            sa.Column("role_en", sa.String(240)),
            sa.Column("role_ar", sa.String(240)),
            sa.Column("problem_en", sa.Text()),
            sa.Column("problem_ar", sa.Text()),
            sa.Column("solution_en", sa.Text()),
            sa.Column("solution_ar", sa.Text()),
            sa.Column("features_en", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("features_ar", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("architecture_en", sa.Text()),
            sa.Column("architecture_ar", sa.Text()),
            sa.Column("challenges_en", sa.Text()),
            sa.Column("challenges_ar", sa.Text()),
            sa.Column("implemented_solutions_en", sa.Text()),
            sa.Column("implemented_solutions_ar", sa.Text()),
            sa.Column("results_en", sa.Text()),
            sa.Column("results_ar", sa.Text()),
            sa.Column("team_members_en", sa.Text()),
            sa.Column("team_members_ar", sa.Text()),
            sa.Column("development_duration_en", sa.String(160)),
            sa.Column("development_duration_ar", sa.String(160)),
            sa.Column("ownership_type", sa.String(30), nullable=False, server_default="personal"),
        ],
    )
    _add_columns(
        "services",
        [
            sa.Column("short_description_en", sa.Text()),
            sa.Column("short_description_ar", sa.Text()),
            sa.Column("cover_image_url", sa.String(1000)),
            sa.Column("cover_image_public_id", sa.String(500)),
            sa.Column("introduction_video_url", sa.String(1000)),
            sa.Column("category", sa.String(120)),
            sa.Column("related_skills", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("scope_en", sa.Text()),
            sa.Column("scope_ar", sa.Text()),
            sa.Column("included_items_en", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("included_items_ar", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("excluded_items_en", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("excluded_items_ar", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("client_requirements_en", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("client_requirements_ar", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("availability_status", sa.String(40), nullable=False, server_default="available"),
        ],
    )

    tables = _tables()
    if "project_media" not in tables:
        op.create_table(
            "project_media",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("media_type", sa.String(20), nullable=False),
            sa.Column("source_type", sa.String(30), nullable=False, server_default="upload"),
            sa.Column("secure_url", sa.String(1000), nullable=False),
            sa.Column("cloudinary_public_id", sa.String(500)),
            sa.Column("thumbnail_url", sa.String(1000)),
            sa.Column("title_en", sa.String(300)),
            sa.Column("title_ar", sa.String(300)),
            sa.Column("alt_text_en", sa.String(300)),
            sa.Column("alt_text_ar", sa.String(300)),
            sa.Column("caption_en", sa.Text()),
            sa.Column("caption_ar", sa.Text()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_cover", sa.Boolean(), nullable=False, server_default=sa.false()),
            *_timestamps(),
        )
        op.create_index("ix_project_media_project_order", "project_media", ["project_id", "sort_order"])
        op.create_index("ix_project_media_cloudinary_public_id", "project_media", ["cloudinary_public_id"])

    if "service_packages" not in tables:
        op.create_table(
            "service_packages",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("package_type", sa.String(20), nullable=False),
            sa.Column("name_en", sa.String(160), nullable=False),
            sa.Column("name_ar", sa.String(160), nullable=False),
            sa.Column("short_description_en", sa.Text()),
            sa.Column("short_description_ar", sa.Text()),
            sa.Column("price", sa.Numeric(12, 2), nullable=False),
            sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
            sa.Column("delivery_days", sa.Integer(), nullable=False),
            sa.Column("revisions", sa.Integer()),
            sa.Column("unlimited_revisions", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("included_deliverables_en", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("included_deliverables_ar", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("excluded_items_en", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("excluded_items_ar", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("client_requirements_en", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("client_requirements_ar", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("additional_notes_en", sa.Text()),
            sa.Column("additional_notes_ar", sa.Text()),
            sa.Column("cta_label_en", sa.String(120)),
            sa.Column("cta_label_ar", sa.String(120)),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_recommended", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            *_timestamps(),
            sa.UniqueConstraint("service_id", "package_type", name="uq_service_package_type"),
            sa.CheckConstraint("package_type IN ('basic','standard','premium')", name="ck_package_type"),
            sa.CheckConstraint("price >= 0", name="ck_package_price"),
            sa.CheckConstraint("delivery_days > 0", name="ck_package_delivery"),
        )
        op.create_index("ix_service_packages_service_order", "service_packages", ["service_id", "display_order"])

    tables = _tables()
    if "service_features" not in tables:
        op.create_table(
            "service_features",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name_en", sa.String(200), nullable=False),
            sa.Column("name_ar", sa.String(200), nullable=False),
            sa.Column("value_type", sa.String(20), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *_timestamps(),
            sa.CheckConstraint("value_type IN ('boolean','number','text')", name="ck_feature_value_type"),
        )
        op.create_index("ix_service_features_service_order", "service_features", ["service_id", "sort_order"])
    if "package_feature_values" not in tables:
        op.create_table(
            "package_feature_values",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("feature_id", sa.Uuid(), sa.ForeignKey("service_features.id", ondelete="CASCADE"), nullable=False),
            sa.Column("package_id", sa.Uuid(), sa.ForeignKey("service_packages.id", ondelete="CASCADE"), nullable=False),
            sa.Column("value_boolean", sa.Boolean()),
            sa.Column("value_number", sa.Numeric(12, 2)),
            sa.Column("value_text_en", sa.Text()),
            sa.Column("value_text_ar", sa.Text()),
            *_timestamps(),
            sa.UniqueConstraint("feature_id", "package_id", name="uq_feature_package_value"),
        )
    if "service_faqs" not in tables:
        op.create_table(
            "service_faqs",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
            sa.Column("question_en", sa.Text(), nullable=False),
            sa.Column("question_ar", sa.Text(), nullable=False),
            sa.Column("answer_en", sa.Text(), nullable=False),
            sa.Column("answer_ar", sa.Text(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *_timestamps(),
        )
    if "service_requirements" not in tables:
        op.create_table(
            "service_requirements",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
            sa.Column("text_en", sa.Text(), nullable=False),
            sa.Column("text_ar", sa.Text(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *_timestamps(),
        )
    if "service_project_links" not in tables:
        op.create_table(
            "service_project_links",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False),
            sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            *_timestamps(),
            sa.UniqueConstraint("service_id", "project_id", name="uq_service_project"),
        )
    if "media_assets" not in tables:
        op.create_table(
            "media_assets",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("cloudinary_public_id", sa.String(500), nullable=False, unique=True),
            sa.Column("secure_url", sa.String(1000), nullable=False),
            sa.Column("resource_type", sa.String(30), nullable=False),
            sa.Column("mime_type", sa.String(120)),
            sa.Column("size_bytes", sa.Integer()),
            sa.Column("width", sa.Integer()),
            sa.Column("height", sa.Integer()),
            sa.Column("duration_seconds", sa.Numeric(10, 2)),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *_timestamps(),
        )
        op.create_index("ix_media_assets_cloudinary_public_id", "media_assets", ["cloudinary_public_id"], unique=True)

    _add_columns(
        "project_requests",
        [
            sa.Column("company_name", sa.String(200)),
            sa.Column("whatsapp", sa.String(100)),
            sa.Column("request_type", sa.String(30), nullable=False, server_default="custom"),
            sa.Column("service_id", sa.Uuid(), sa.ForeignKey("services.id", ondelete="SET NULL", name="fk_project_requests_service_id")),
            sa.Column("package_id", sa.Uuid(), sa.ForeignKey("service_packages.id", ondelete="SET NULL", name="fk_project_requests_package_id")),
            sa.Column("reference_project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="SET NULL", name="fk_project_requests_reference_project_id")),
            sa.Column("service_name_snapshot", sa.String(240)),
            sa.Column("package_name_snapshot", sa.String(240)),
            sa.Column("price_snapshot", sa.Numeric(12, 2)),
            sa.Column("currency_snapshot", sa.String(10)),
            sa.Column("delivery_days_snapshot", sa.Integer()),
            sa.Column("revisions_snapshot", sa.Integer()),
            sa.Column("package_features_snapshot", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("included_items_snapshot", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("excluded_items_snapshot", sa.JSON(), nullable=False, server_default=json_empty),
            sa.Column("expected_deliverables", sa.Text()),
            sa.Column("preferred_contact_method", sa.String(50)),
        ],
    )
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("project_requests")}
    if "ix_project_requests_service_id" not in indexes:
        op.create_index("ix_project_requests_service_id", "project_requests", ["service_id"])
    if "ix_project_requests_package_id" not in indexes:
        op.create_index("ix_project_requests_package_id", "project_requests", ["package_id"])
    _make_nullable("profiles", {"cv_url"})
    _make_nullable("projects", {"category", "status_en", "status_ar"})
    _make_nullable(
        "project_requests", {"requested_service", "deliverables", "budget_range", "timeline"}
    )


def downgrade() -> None:
    tables = _tables()
    for table in [
        "package_feature_values",
        "service_project_links",
        "service_requirements",
        "service_faqs",
        "service_features",
        "project_media",
        "media_assets",
    ]:
        if table in tables:
            op.drop_table(table)

    request_columns = [
        "preferred_contact_method", "expected_deliverables", "excluded_items_snapshot",
        "included_items_snapshot", "package_features_snapshot", "revisions_snapshot",
        "delivery_days_snapshot", "currency_snapshot", "price_snapshot", "package_name_snapshot",
        "service_name_snapshot", "reference_project_id", "package_id", "service_id", "request_type",
        "whatsapp", "company_name",
    ]
    dialect = op.get_bind().dialect.name
    existing_request_columns = _columns("project_requests")
    request_indexes = {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes("project_requests")
    }
    for index_name in ("ix_project_requests_package_id", "ix_project_requests_service_id"):
        if index_name in request_indexes:
            op.drop_index(index_name, table_name="project_requests")
    if dialect == "sqlite":
        with op.batch_alter_table("project_requests", recreate="always") as batch:
            for name in request_columns:
                if name in existing_request_columns:
                    batch.drop_column(name)
    else:
        for name in request_columns:
            if name in existing_request_columns:
                op.drop_column("project_requests", name)
    if "service_packages" in _tables():
        op.drop_table("service_packages")

    column_groups = {
        "services": [
            "availability_status", "client_requirements_ar", "client_requirements_en",
            "excluded_items_ar", "excluded_items_en", "included_items_ar", "included_items_en",
            "scope_ar", "scope_en", "related_skills", "category", "introduction_video_url",
            "cover_image_public_id", "cover_image_url", "short_description_ar", "short_description_en",
        ],
        "projects": [
            "ownership_type", "development_duration_ar", "development_duration_en", "team_members_ar",
            "team_members_en", "results_ar", "results_en", "implemented_solutions_ar",
            "implemented_solutions_en", "challenges_ar", "challenges_en", "architecture_ar",
            "architecture_en", "features_ar", "features_en", "solution_ar", "solution_en", "problem_ar",
            "problem_en", "role_ar", "role_en", "client_name", "demo_url", "short_description_ar",
            "short_description_en",
        ],
        "profiles": [
            "contact_cta_ar", "contact_cta_en", "hero_cta_ar", "hero_cta_en", "hero_subheading_ar",
            "hero_subheading_en", "hero_heading_ar", "hero_heading_en", "availability_status", "upwork_url",
            "linkedin_url", "github_url", "telegram", "whatsapp", "cv_public_id", "profile_image_position",
            "profile_image_alt_ar", "profile_image_alt_en", "profile_image_public_id",
        ],
    }
    for table, names in column_groups.items():
        existing = _columns(table)
        if dialect == "sqlite":
            for index in sa.inspect(op.get_bind()).get_indexes(table):
                if set(index["column_names"]) & set(names):
                    op.drop_index(index["name"], table_name=table)
            with op.batch_alter_table(table, recreate="always") as batch:
                for name in names:
                    if name in existing:
                        batch.drop_column(name)
        else:
            for name in names:
                if name in existing:
                    op.drop_column(table, name)
