from datetime import date
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if "<script" in cleaned.lower() or "javascript:" in cleaned.lower():
        raise ValueError("Unsafe content is not allowed")
    return cleaned or None


def _https_url(value: str | None) -> str | None:
    cleaned = _clean(value)
    if cleaned and not cleaned.lower().startswith("https://"):
        raise ValueError("External URLs must use HTTPS")
    return cleaned


class PortfolioModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProjectIn(PortfolioModel):
    slug: str = Field(min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title_en: str = Field(min_length=1, max_length=200)
    title_ar: str = Field(min_length=1, max_length=200)
    summary_en: str = Field(min_length=1, max_length=10000)
    summary_ar: str = Field(min_length=1, max_length=10000)
    technologies: list[str] = Field(min_length=1, max_length=50)
    short_description_en: str | None = None
    short_description_ar: str | None = None
    content_en: dict[str, Any] = Field(default_factory=dict)
    content_ar: dict[str, Any] = Field(default_factory=dict)
    category: str | None = Field(None, max_length=80)
    status_en: str | None = Field(None, max_length=120)
    status_ar: str | None = Field(None, max_length=120)
    cover_url: str | None = Field(None, max_length=1000)
    github_url: str | None = Field(None, max_length=1000)
    live_url: str | None = Field(None, max_length=1000)
    demo_url: str | None = Field(None, max_length=1000)
    project_date: date | None = None
    client_name: str | None = Field(None, max_length=240)
    role_en: str | None = Field(None, max_length=240)
    role_ar: str | None = Field(None, max_length=240)
    problem_en: str | None = None
    problem_ar: str | None = None
    solution_en: str | None = None
    solution_ar: str | None = None
    features_en: list[str] = Field(default_factory=list)
    features_ar: list[str] = Field(default_factory=list)
    architecture_en: str | None = None
    architecture_ar: str | None = None
    challenges_en: str | None = None
    challenges_ar: str | None = None
    implemented_solutions_en: str | None = None
    implemented_solutions_ar: str | None = None
    results_en: str | None = None
    results_ar: str | None = None
    team_members_en: str | None = None
    team_members_ar: str | None = None
    development_duration_en: str | None = Field(None, max_length=160)
    development_duration_ar: str | None = Field(None, max_length=160)
    ownership_type: Literal["personal", "client", "university", "team"] = "personal"
    team_type: str = Field("solo", max_length=30)
    publication_status: Literal["draft", "published", "archived"] = "draft"
    sort_order: int = Field(0, ge=0)
    is_featured: bool = False
    is_active: bool = True

    @field_validator("technologies", "features_en", "features_ar")
    @classmethod
    def clean_lists(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values if item.strip()]
        if not cleaned and cls.__name__ == "ProjectIn" and values is not None:
            if values == []:
                return []
        return list(dict.fromkeys(cleaned))

    @field_validator(
        "short_description_en", "short_description_ar", "problem_en", "problem_ar",
        "solution_en", "solution_ar", "architecture_en", "architecture_ar", "challenges_en",
        "challenges_ar", "implemented_solutions_en", "implemented_solutions_ar", "results_en",
        "results_ar", "team_members_en", "team_members_ar", mode="before",
    )
    @classmethod
    def safe_text(cls, value: str | None) -> str | None:
        return _clean(value)

    @field_validator("cover_url", "github_url", "live_url", "demo_url", mode="before")
    @classmethod
    def safe_url(cls, value: str | None) -> str | None:
        return _https_url(value)


class ProjectPatch(PortfolioModel):
    slug: str | None = Field(None, min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title_en: str | None = Field(None, min_length=1, max_length=200)
    title_ar: str | None = Field(None, min_length=1, max_length=200)
    summary_en: str | None = Field(None, min_length=1, max_length=10000)
    summary_ar: str | None = Field(None, min_length=1, max_length=10000)
    technologies: list[str] | None = None
    short_description_en: str | None = None
    short_description_ar: str | None = None
    content_en: dict[str, Any] | None = None
    content_ar: dict[str, Any] | None = None
    category: str | None = None
    status_en: str | None = None
    status_ar: str | None = None
    cover_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    demo_url: str | None = None
    project_date: date | None = None
    client_name: str | None = None
    role_en: str | None = None
    role_ar: str | None = None
    problem_en: str | None = None
    problem_ar: str | None = None
    solution_en: str | None = None
    solution_ar: str | None = None
    features_en: list[str] | None = None
    features_ar: list[str] | None = None
    architecture_en: str | None = None
    architecture_ar: str | None = None
    challenges_en: str | None = None
    challenges_ar: str | None = None
    implemented_solutions_en: str | None = None
    implemented_solutions_ar: str | None = None
    results_en: str | None = None
    results_ar: str | None = None
    team_members_en: str | None = None
    team_members_ar: str | None = None
    development_duration_en: str | None = None
    development_duration_ar: str | None = None
    ownership_type: Literal["personal", "client", "university", "team"] | None = None
    team_type: str | None = None
    publication_status: Literal["draft", "published", "archived"] | None = None
    sort_order: int | None = Field(None, ge=0)
    is_featured: bool | None = None
    is_active: bool | None = None

    @field_validator("cover_url", "github_url", "live_url", "demo_url", mode="before")
    @classmethod
    def safe_url(cls, value: str | None) -> str | None:
        return _https_url(value)


class ServiceIn(PortfolioModel):
    slug: str = Field(min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title_en: str = Field(min_length=1, max_length=240)
    title_ar: str = Field(min_length=1, max_length=240)
    description_en: str = Field(min_length=1, max_length=15000)
    description_ar: str = Field(min_length=1, max_length=15000)
    related_skills: list[str] = Field(min_length=1, max_length=50)
    short_description_en: str | None = None
    short_description_ar: str | None = None
    cover_image_url: str | None = None
    cover_image_public_id: str | None = None
    introduction_video_url: str | None = None
    icon: str = "Sparkles"
    category: str | None = None
    scope_en: str | None = None
    scope_ar: str | None = None
    included_items_en: list[str] = Field(default_factory=list)
    included_items_ar: list[str] = Field(default_factory=list)
    excluded_items_en: list[str] = Field(default_factory=list)
    excluded_items_ar: list[str] = Field(default_factory=list)
    client_requirements_en: list[str] = Field(default_factory=list)
    client_requirements_ar: list[str] = Field(default_factory=list)
    deliverables_en: list[str] = Field(default_factory=list)
    deliverables_ar: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    is_featured: bool = False
    sort_order: int = Field(0, ge=0)
    publication_status: Literal["draft", "published", "archived"] = "draft"
    availability_status: Literal["available", "temporarily_unavailable"] = "available"
    is_active: bool = True

    @field_validator("cover_image_url", "introduction_video_url", mode="before")
    @classmethod
    def safe_url(cls, value: str | None) -> str | None:
        return _https_url(value)


class ServicePatch(PortfolioModel):
    slug: str | None = None
    title_en: str | None = None
    title_ar: str | None = None
    description_en: str | None = None
    description_ar: str | None = None
    related_skills: list[str] | None = None
    short_description_en: str | None = None
    short_description_ar: str | None = None
    cover_image_url: str | None = None
    cover_image_public_id: str | None = None
    introduction_video_url: str | None = None
    icon: str | None = None
    category: str | None = None
    scope_en: str | None = None
    scope_ar: str | None = None
    included_items_en: list[str] | None = None
    included_items_ar: list[str] | None = None
    excluded_items_en: list[str] | None = None
    excluded_items_ar: list[str] | None = None
    client_requirements_en: list[str] | None = None
    client_requirements_ar: list[str] | None = None
    deliverables_en: list[str] | None = None
    deliverables_ar: list[str] | None = None
    technologies: list[str] | None = None
    is_featured: bool | None = None
    sort_order: int | None = Field(None, ge=0)
    publication_status: Literal["draft", "published", "archived"] | None = None
    availability_status: Literal["available", "temporarily_unavailable"] | None = None
    is_active: bool | None = None

    @field_validator("cover_image_url", "introduction_video_url", mode="before")
    @classmethod
    def safe_url(cls, value: str | None) -> str | None:
        return _https_url(value)


class PackageIn(PortfolioModel):
    package_type: Literal["basic", "standard", "premium"]
    name_en: str = Field(min_length=1, max_length=160)
    name_ar: str = Field(min_length=1, max_length=160)
    short_description_en: str | None = None
    short_description_ar: str | None = None
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: str = Field("USD", min_length=3, max_length=10)
    delivery_days: int = Field(gt=0, le=3650)
    revisions: int | None = Field(None, ge=0, le=1000)
    unlimited_revisions: bool = False
    included_deliverables_en: list[str] = Field(min_length=1)
    included_deliverables_ar: list[str] = Field(default_factory=list)
    excluded_items_en: list[str] = Field(default_factory=list)
    excluded_items_ar: list[str] = Field(default_factory=list)
    client_requirements_en: list[str] = Field(default_factory=list)
    client_requirements_ar: list[str] = Field(default_factory=list)
    additional_notes_en: str | None = None
    additional_notes_ar: str | None = None
    cta_label_en: str | None = None
    cta_label_ar: str | None = None
    is_active: bool = True
    is_recommended: bool = False
    display_order: int = Field(0, ge=0)


class PackagePatch(PackageIn):
    pass


class FeatureValueIn(PortfolioModel):
    package_id: UUID
    value_boolean: bool | None = None
    value_number: Decimal | None = None
    value_text_en: str | None = None
    value_text_ar: str | None = None


class FeatureIn(PortfolioModel):
    name_en: str = Field(min_length=1, max_length=200)
    name_ar: str = Field(min_length=1, max_length=200)
    value_type: Literal["boolean", "number", "text"]
    sort_order: int = Field(0, ge=0)
    is_active: bool = True
    values: list[FeatureValueIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def values_match_type(self) -> "FeatureIn":
        field = {"boolean": "value_boolean", "number": "value_number", "text": "value_text_en"}[self.value_type]
        if any(getattr(value, field) is None for value in self.values):
            raise ValueError(f"Every package value must provide {field}")
        return self


class FAQIn(PortfolioModel):
    question_en: str = Field(min_length=2, max_length=1000)
    question_ar: str = Field(min_length=2, max_length=1000)
    answer_en: str = Field(min_length=2, max_length=5000)
    answer_ar: str = Field(min_length=2, max_length=5000)
    sort_order: int = Field(0, ge=0)
    is_active: bool = True


class RelatedProjectIn(PortfolioModel):
    project_id: UUID
    sort_order: int = Field(0, ge=0)


class ReorderIn(PortfolioModel):
    ids: list[UUID] = Field(min_length=1, max_length=500)


class ExternalMediaIn(PortfolioModel):
    url: str = Field(min_length=10, max_length=1000)
    title_en: str | None = None
    title_ar: str | None = None
    caption_en: str | None = None
    caption_ar: str | None = None

    @field_validator("url")
    @classmethod
    def supported_video_url(cls, value: str) -> str:
        lowered = value.lower()
        if not lowered.startswith("https://") or not any(
            host in lowered for host in ("youtube.com/", "youtu.be/", "vimeo.com/")
        ):
            raise ValueError("Only HTTPS YouTube or Vimeo URLs are supported")
        return value


class MediaPatch(PortfolioModel):
    title_en: str | None = None
    title_ar: str | None = None
    alt_text_en: str | None = None
    alt_text_ar: str | None = None
    caption_en: str | None = None
    caption_ar: str | None = None
    sort_order: int | None = Field(None, ge=0)


class PackageRequestIn(PortfolioModel):
    client_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    company_name: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=80)
    whatsapp: str | None = Field(None, max_length=100)
    telegram: str | None = Field(None, max_length=100)
    preferred_contact_method: Literal["email", "phone", "whatsapp", "telegram"] = "email"
    service_id: UUID | None = None
    package_id: UUID | None = None
    displayed_price: Decimal | None = None
    currency: str | None = None
    delivery_days: int | None = None
    project_title: str = Field(min_length=3, max_length=240)
    project_description: str = Field(min_length=20, max_length=10000)
    expected_deliverables: str | None = Field(None, max_length=5000)
    preferred_start_date: date | None = None
    reference_project_id: UUID | None = None
    consent: bool
    turnstile_token: str = ""
    website: str = ""

    @field_validator("consent")
    @classmethod
    def consent_required(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Consent is required")
        return value


class ProfilePatch(PortfolioModel):
    name_en: str | None = None
    name_ar: str | None = None
    title_en: str | None = None
    title_ar: str | None = None
    statement_en: str | None = None
    statement_ar: str | None = None
    about_en: str | None = None
    about_ar: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    whatsapp: str | None = None
    telegram: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    upwork_url: str | None = None
    cv_url: str | None = None
    location_en: str | None = None
    location_ar: str | None = None
    availability_status: str | None = None
    hero_heading_en: str | None = None
    hero_heading_ar: str | None = None
    hero_subheading_en: str | None = None
    hero_subheading_ar: str | None = None
    hero_cta_en: str | None = None
    hero_cta_ar: str | None = None
    contact_cta_en: str | None = None
    contact_cta_ar: str | None = None
    profile_image_alt_en: str | None = None
    profile_image_alt_ar: str | None = None
    profile_image_position: str | None = None

    @field_validator("github_url", "linkedin_url", "upwork_url", "cv_url", mode="before")
    @classmethod
    def safe_url(cls, value: str | None) -> str | None:
        return _https_url(value)
