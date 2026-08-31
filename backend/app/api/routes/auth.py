"""Auth: login (with optional TOTP), profile, MFA enrolment (NFR-3.1)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import client_ip, get_current_user
from app.core import audit
from app.core.security import (
    create_access_token, mfa_provisioning_uri, new_mfa_secret,
    verify_password, verify_totp,
)
from app.config import settings
from app.database import get_session
from app.models.user import Role, User, utcnow

router = APIRouter()

PRIVILEGED = {Role.ADMIN, Role.SAFETY_ENGINEER, Role.OPS_MANAGER}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    mfa_required: bool = False


class LoginBody(BaseModel):
    username: str
    password: str
    totp: str | None = None


def _authenticate(session: Session, username: str, password: str, totp: str | None,
                  ip: str) -> User:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User disabled")

    mfa_ok = True
    if user.mfa_enabled:
        mfa_ok = bool(totp) and verify_totp(user.mfa_secret or "", totp)
    elif settings.require_mfa and user.role in PRIVILEGED:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "MFA enrolment required for this role")

    if not mfa_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing TOTP code")

    user.last_login_at = utcnow()
    session.add(user)
    audit.record(session, username=user.username, role=user.role.value,
                 action="login", target="auth", ip=ip)
    return user


@router.post("/login", response_model=TokenOut)
def login_form(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    # OAuth2 form: TOTP may be appended as "password:totp" or sent via /login-json
    pw, _, totp = form.password.partition(":")
    user = _authenticate(session, form.username, pw, totp or None, client_ip(request))
    token = create_access_token(user.username, user.role.value, {"mfa": user.mfa_enabled})
    return TokenOut(access_token=token, role=user.role.value, mfa_required=user.mfa_enabled)


@router.post("/login-json", response_model=TokenOut)
def login_json(request: Request, body: LoginBody, session: Session = Depends(get_session)):
    user = _authenticate(session, body.username, body.password, body.totp, client_ip(request))
    token = create_access_token(user.username, user.role.value, {"mfa": user.mfa_enabled})
    return TokenOut(access_token=token, role=user.role.value, mfa_required=user.mfa_enabled)


class Me(BaseModel):
    username: str
    full_name: str
    email: str
    role: str
    mfa_enabled: bool


@router.get("/me", response_model=Me)
def me(user: User = Depends(get_current_user)):
    return Me(username=user.username, full_name=user.full_name, email=user.email,
              role=user.role.value, mfa_enabled=user.mfa_enabled)


class MfaSetup(BaseModel):
    secret: str
    otpauth_uri: str


@router.post("/mfa/enroll", response_model=MfaSetup)
def mfa_enroll(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    secret = new_mfa_secret()
    user.mfa_secret = secret
    session.add(user)
    session.commit()
    return MfaSetup(secret=secret, otpauth_uri=mfa_provisioning_uri(secret, user.username))


class MfaVerify(BaseModel):
    totp: str


@router.post("/mfa/activate")
def mfa_activate(body: MfaVerify, request: Request,
                 user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not user.mfa_secret or not verify_totp(user.mfa_secret, body.totp):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid TOTP code")
    user.mfa_enabled = True
    session.add(user)
    audit.record(session, username=user.username, role=user.role.value,
                 action="mfa.activate", target="auth", ip=client_ip(request))
    session.commit()
    return {"mfa_enabled": True}
