from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AdminUser(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "admin_users"
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None]
    refresh_token_hash: Mapped[str | None] = mapped_column(String(512))


class Profile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "profiles"
    name_en: Mapped[str] = mapped_column(String(160))
    name_ar: Mapped[str] = mapped_column(String(160))
    title_en: Mapped[str] = mapped_column(String(240))
    title_ar: Mapped[str] = mapped_column(String(240))
    statement_en: Mapped[str] = mapped_column(Text)
    statement_ar: Mapped[str] = mapped_column(Text)
    about_en: Mapped[str] = mapped_column(Text)
    about_ar: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(String(320), default="[EMAIL]")
    phone: Mapped[str] = mapped_column(String(80), default="[PHONE]")
    location_en: Mapped[str] = mapped_column(String(160), default="Syria · Remote")
    location_ar: Mapped[str] = mapped_column(String(160), default="سوريا · عن بُعد")
    profile_image_url: Mapped[str | None] = mapped_column(String(1000))
    profile_image_public_id: Mapped[str | None] = mapped_column(String(500))
    profile_image_alt_en: Mapped[str | None] = mapped_column(String(300))
    profile_image_alt_ar: Mapped[str | None] = mapped_column(String(300))
    profile_image_position: Mapped[str] = mapped_column(String(30), default="50% 50%")
    cv_url: Mapped[str | None] = mapped_column(String(1000))
    cv_public_id: Mapped[str | None] = mapped_column(String(500))
    whatsapp: Mapped[str | None] = mapped_column(String(100))
    telegram: Mapped[str | None] = mapped_column(String(100))
    github_url: Mapped[str | None] = mapped_column(String(1000))
    linkedin_url: Mapped[str | None] = mapped_column(String(1000))
    upwork_url: Mapped[str | None] = mapped_column(String(1000))
    availability_status: Mapped[str | None] = mapped_column(String(80))
    hero_heading_en: Mapped[str | None] = mapped_column(String(240))
    hero_heading_ar: Mapped[str | None] = mapped_column(String(240))
    hero_subheading_en: Mapped[str | None] = mapped_column(Text)
    hero_subheading_ar: Mapped[str | None] = mapped_column(Text)
    hero_cta_en: Mapped[str | None] = mapped_column(String(120))
    hero_cta_ar: Mapped[str | None] = mapped_column(String(120))
    contact_cta_en: Mapped[str | None] = mapped_column(Text)
    contact_cta_ar: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SkillCategory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "skill_categories"
    name_en: Mapped[str] = mapped_column(String(120), unique=True)
    name_ar: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Skill(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "skills"
    category_id: Mapped[Any] = mapped_column(ForeignKey("skill_categories.id"))
    name: Mapped[str] = mapped_column(String(120))
    icon: Mapped[str] = mapped_column(String(120), default="Code2")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Project(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "projects"
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title_en: Mapped[str] = mapped_column(String(200))
    title_ar: Mapped[str] = mapped_column(String(200))
    summary_en: Mapped[str] = mapped_column(Text)
    summary_ar: Mapped[str] = mapped_column(Text)
    content_en: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    content_ar: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    short_description_en: Mapped[str | None] = mapped_column(Text)
    short_description_ar: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(80))
    status_en: Mapped[str | None] = mapped_column(String(120))
    status_ar: Mapped[str | None] = mapped_column(String(120))
    cover_url: Mapped[str | None] = mapped_column(String(1000))
    github_url: Mapped[str | None] = mapped_column(String(1000))
    live_url: Mapped[str | None] = mapped_column(String(1000))
    demo_url: Mapped[str | None] = mapped_column(String(1000))
    project_date: Mapped[date | None] = mapped_column(Date)
    client_name: Mapped[str | None] = mapped_column(String(240))
    role_en: Mapped[str | None] = mapped_column(String(240))
    role_ar: Mapped[str | None] = mapped_column(String(240))
    problem_en: Mapped[str | None] = mapped_column(Text)
    problem_ar: Mapped[str | None] = mapped_column(Text)
    solution_en: Mapped[str | None] = mapped_column(Text)
    solution_ar: Mapped[str | None] = mapped_column(Text)
    features_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    features_ar: Mapped[list[str]] = mapped_column(JSON, default=list)
    architecture_en: Mapped[str | None] = mapped_column(Text)
    architecture_ar: Mapped[str | None] = mapped_column(Text)
    challenges_en: Mapped[str | None] = mapped_column(Text)
    challenges_ar: Mapped[str | None] = mapped_column(Text)
    implemented_solutions_en: Mapped[str | None] = mapped_column(Text)
    implemented_solutions_ar: Mapped[str | None] = mapped_column(Text)
    results_en: Mapped[str | None] = mapped_column(Text)
    results_ar: Mapped[str | None] = mapped_column(Text)
    team_members_en: Mapped[str | None] = mapped_column(Text)
    team_members_ar: Mapped[str | None] = mapped_column(Text)
    development_duration_en: Mapped[str | None] = mapped_column(String(160))
    development_duration_ar: Mapped[str | None] = mapped_column(String(160))
    ownership_type: Mapped[str] = mapped_column(String(30), default="personal")
    team_type: Mapped[str] = mapped_column(String(30), default="solo")
    publication_status: Mapped[str] = mapped_column(String(30), default="published")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProjectImage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_images"
    project_id: Mapped[Any] = mapped_column(ForeignKey("projects.id"))
    secure_url: Mapped[str] = mapped_column(String(1000))
    public_id: Mapped[str] = mapped_column(String(500))
    alt_en: Mapped[str] = mapped_column(String(300))
    alt_ar: Mapped[str] = mapped_column(String(300))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ProjectMedia(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_media"
    __table_args__ = (
        Index("ix_project_media_project_order", "project_id", "sort_order"),
    )
    project_id: Mapped[Any] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    media_type: Mapped[str] = mapped_column(String(20))
    source_type: Mapped[str] = mapped_column(String(30), default="upload")
    secure_url: Mapped[str] = mapped_column(String(1000))
    cloudinary_public_id: Mapped[str | None] = mapped_column(String(500), index=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000))
    title_en: Mapped[str | None] = mapped_column(String(300))
    title_ar: Mapped[str | None] = mapped_column(String(300))
    alt_text_en: Mapped[str | None] = mapped_column(String(300))
    alt_text_ar: Mapped[str | None] = mapped_column(String(300))
    caption_en: Mapped[str | None] = mapped_column(Text)
    caption_ar: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)


class ProjectTechnology(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_technologies"
    project_id: Mapped[Any] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class BilingualContent(UUIDMixin, TimestampMixin):
    __abstract__ = True
    title_en: Mapped[str] = mapped_column(String(240))
    title_ar: Mapped[str] = mapped_column(String(240))
    description_en: Mapped[str] = mapped_column(Text)
    description_ar: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Service(BilingualContent, Base):
    __tablename__ = "services"
    slug: Mapped[str] = mapped_column(String(180), unique=True)
    icon: Mapped[str] = mapped_column(String(120), default="Sparkles")
    short_description_en: Mapped[str | None] = mapped_column(Text)
    short_description_ar: Mapped[str | None] = mapped_column(Text)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000))
    cover_image_public_id: Mapped[str | None] = mapped_column(String(500))
    introduction_video_url: Mapped[str | None] = mapped_column(String(1000))
    category: Mapped[str | None] = mapped_column(String(120), index=True)
    related_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    scope_en: Mapped[str | None] = mapped_column(Text)
    scope_ar: Mapped[str | None] = mapped_column(Text)
    included_items_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    included_items_ar: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_items_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_items_ar: Mapped[list[str]] = mapped_column(JSON, default=list)
    client_requirements_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    client_requirements_ar: Mapped[list[str]] = mapped_column(JSON, default=list)
    deliverables_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    deliverables_ar: Mapped[list[str]] = mapped_column(JSON, default=list)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    publication_status: Mapped[str] = mapped_column(String(30), default="published")
    availability_status: Mapped[str] = mapped_column(String(40), default="available")


class ServicePackage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "service_packages"
    __table_args__ = (
        UniqueConstraint("service_id", "package_type", name="uq_service_package_type"),
        Index("ix_service_packages_service_order", "service_id", "display_order"),
    )
    service_id: Mapped[Any] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"))
    package_type: Mapped[str] = mapped_column(String(20))
    name_en: Mapped[str] = mapped_column(String(160))
    name_ar: Mapped[str] = mapped_column(String(160))
    short_description_en: Mapped[str | None] = mapped_column(Text)
    short_description_ar: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Any] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    delivery_days: Mapped[int] = mapped_column(Integer)
    revisions: Mapped[int | None] = mapped_column(Integer)
    unlimited_revisions: Mapped[bool] = mapped_column(Boolean, default=False)
    included_deliverables_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    included_deliverables_ar: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_items_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_items_ar: Mapped[list[str]] = mapped_column(JSON, default=list)
    client_requirements_en: Mapped[list[str]] = mapped_column(JSON, default=list)
    client_requirements_ar: Mapped[list[str]] = mapped_column(JSON, default=list)
    additional_notes_en: Mapped[str | None] = mapped_column(Text)
    additional_notes_ar: Mapped[str | None] = mapped_column(Text)
    cta_label_en: Mapped[str | None] = mapped_column(String(120))
    cta_label_ar: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)


class ServiceFeature(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "service_features"
    __table_args__ = (Index("ix_service_features_service_order", "service_id", "sort_order"),)
    service_id: Mapped[Any] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    name_en: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str] = mapped_column(String(200))
    value_type: Mapped[str] = mapped_column(String(20))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PackageFeatureValue(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "package_feature_values"
    __table_args__ = (
        UniqueConstraint("feature_id", "package_id", name="uq_feature_package_value"),
    )
    feature_id: Mapped[Any] = mapped_column(ForeignKey("service_features.id", ondelete="CASCADE"))
    package_id: Mapped[Any] = mapped_column(ForeignKey("service_packages.id", ondelete="CASCADE"))
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    value_number: Mapped[Any | None] = mapped_column(Numeric(12, 2))
    value_text_en: Mapped[str | None] = mapped_column(Text)
    value_text_ar: Mapped[str | None] = mapped_column(Text)


class ServiceFAQ(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "service_faqs"
    service_id: Mapped[Any] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    question_en: Mapped[str] = mapped_column(Text)
    question_ar: Mapped[str] = mapped_column(Text)
    answer_en: Mapped[str] = mapped_column(Text)
    answer_ar: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ServiceRequirement(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "service_requirements"
    service_id: Mapped[Any] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    text_en: Mapped[str] = mapped_column(Text)
    text_ar: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ServiceProjectLink(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "service_project_links"
    __table_args__ = (UniqueConstraint("service_id", "project_id", name="uq_service_project"),)
    service_id: Mapped[Any] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    project_id: Mapped[Any] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Experience(BilingualContent, Base):
    __tablename__ = "experiences"
    organization_en: Mapped[str | None] = mapped_column(String(240))
    organization_ar: Mapped[str | None] = mapped_column(String(240))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)


class Education(BilingualContent, Base):
    __tablename__ = "education"
    institution_en: Mapped[str] = mapped_column(String(240))
    institution_ar: Mapped[str] = mapped_column(String(240))


class Activity(BilingualContent, Base):
    __tablename__ = "activities"


class SocialLink(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "social_links"
    platform: Mapped[str] = mapped_column(String(80), unique=True)
    url: Mapped[str] = mapped_column(String(1000))
    icon: Mapped[str] = mapped_column(String(80))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ContactMessage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "contact_messages"
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(320), index=True)
    subject: Mapped[str] = mapped_column(String(240))
    message: Mapped[str] = mapped_column(Text)
    preferred_contact: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(40), default="new")
    email_delivered: Mapped[bool] = mapped_column(Boolean, default=False)


class ProjectRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_requests"
    reference: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    client_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(320), index=True)
    company: Mapped[str | None] = mapped_column(String(200))
    company_name: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(80))
    whatsapp: Mapped[str | None] = mapped_column(String(100))
    telegram: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(120))
    requested_service: Mapped[str | None] = mapped_column(String(180))
    request_type: Mapped[str] = mapped_column(String(30), default="custom")
    service_id: Mapped[Any | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL"), index=True
    )
    package_id: Mapped[Any | None] = mapped_column(
        ForeignKey("service_packages.id", ondelete="SET NULL"), index=True
    )
    reference_project_id: Mapped[Any | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    service_name_snapshot: Mapped[str | None] = mapped_column(String(240))
    package_name_snapshot: Mapped[str | None] = mapped_column(String(240))
    price_snapshot: Mapped[Any | None] = mapped_column(Numeric(12, 2))
    currency_snapshot: Mapped[str | None] = mapped_column(String(10))
    delivery_days_snapshot: Mapped[int | None] = mapped_column(Integer)
    revisions_snapshot: Mapped[int | None] = mapped_column(Integer)
    package_features_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    included_items_snapshot: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_items_snapshot: Mapped[list[str]] = mapped_column(JSON, default=list)
    project_title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    deliverables: Mapped[str | None] = mapped_column(Text)
    expected_deliverables: Mapped[str | None] = mapped_column(Text)
    budget_range: Mapped[str | None] = mapped_column(String(100))
    timeline: Mapped[str | None] = mapped_column(String(100))
    preferred_start_date: Mapped[date | None] = mapped_column(Date)
    preferred_contact: Mapped[str] = mapped_column(String(50))
    preferred_contact_method: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(40), default="new")
    internal_notes: Mapped[str | None] = mapped_column(Text)
    email_delivered: Mapped[bool] = mapped_column(Boolean, default=False)


class MediaAsset(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "media_assets"
    cloudinary_public_id: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    secure_url: Mapped[str] = mapped_column(String(1000))
    resource_type: Mapped[str] = mapped_column(String(30))
    mime_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[Any | None] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProjectRequestAttachment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_request_attachments"
    request_id: Mapped[Any] = mapped_column(ForeignKey("project_requests.id"))
    original_name: Mapped[str] = mapped_column(String(300))
    secure_url: Mapped[str] = mapped_column(String(1000))
    public_id: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)


class SiteSetting(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "site_settings"
    key: Mapped[str] = mapped_column(String(160), unique=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"
    admin_id: Mapped[Any | None] = mapped_column(ForeignKey("admin_users.id"))
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(120))
    entity_id: Mapped[str | None] = mapped_column(String(80))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    request_id: Mapped[str | None] = mapped_column(String(80))
