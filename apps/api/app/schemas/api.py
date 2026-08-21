from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=200)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=200)


class ContactIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    subject: str = Field(min_length=3, max_length=240)
    message: str = Field(min_length=20, max_length=5000)
    preferred_contact: Literal["email", "phone", "whatsapp", "telegram"]
    consent: bool
    turnstile_token: str = Field("", max_length=2048)
    website: str = Field("", max_length=200)

    @field_validator("consent")
    @classmethod
    def consent_required(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Consent is required")
        return value


class ProjectRequestIn(BaseModel):
    client_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    company: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=80)
    telegram: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=120)
    requested_service: str = Field(min_length=2, max_length=180)
    project_title: str = Field(min_length=3, max_length=240)
    description: str = Field(min_length=40, max_length=10000)
    deliverables: str = Field(min_length=3, max_length=5000)
    budget_range: str = Field(min_length=2, max_length=100)
    timeline: str = Field(min_length=2, max_length=100)
    preferred_start_date: date | None = None
    preferred_contact: Literal["email", "phone", "whatsapp", "telegram"]
    consent: bool
    turnstile_token: str = Field("", max_length=2048)
    website: str = Field("", max_length=200)

    @field_validator("consent")
    @classmethod
    def consent_required(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Consent is required")
        return value


class AdminPatch(BaseModel):
    data: dict[str, Any]


class StatusPatch(BaseModel):
    status: Literal[
        "new", "reviewing", "contacted", "in_discussion", "accepted", "rejected", "archived"
    ]
    internal_notes: str | None = Field(None, max_length=10000)
