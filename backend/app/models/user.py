"""User & RBAC (NFR-3.1: role-based access control + MFA)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, Enum):
    """SRS 2.3 — user classes."""

    OPERATOR = "operator"          # اپراتور اتاق کنترل
    SAFETY_ENGINEER = "safety"     # مهندس ایمنی
    OPS_MANAGER = "opsmanager"     # مدیر عملیات
    TECHNICIAN = "technician"      # تکنسین نگهداری
    EXECUTIVE = "executive"        # مدیر ارشد
    ADMIN = "admin"                # مدیر سیستم


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    full_name: str = ""
    email: str = ""
    hashed_password: str
    role: Role = Role.OPERATOR
    is_active: bool = True

    # MFA (TOTP)
    mfa_secret: str | None = None
    mfa_enabled: bool = False

    created_at: datetime = Field(default_factory=utcnow)
    last_login_at: datetime | None = None
