"""Autenticação própria com Argon2id e sessões opacas server-side."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest
from secrets import token_urlsafe

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models import AuthSession, User
from services.clock import Clock, SystemClock
from services.errors import AuthenticationError, ConflictError, ValidationError

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 256
_password_hasher = PasswordHasher()


@dataclass(frozen=True)
class CreatedSession:
    record: AuthSession
    token: str


def token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValidationError(
            f"A senha deve possuir entre {MIN_PASSWORD_LENGTH} e {MAX_PASSWORD_LENGTH} caracteres.",
            code="PASSWORD_LENGTH_INVALID",
            field="password",
        )
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def provision_user(
    session: Session, *, name: str, email: str, password: str
) -> User:
    normalized_email = email.strip().lower()
    if not normalized_email or "@" not in normalized_email:
        raise ValidationError("Email inválido.", code="EMAIL_INVALID", field="email")
    clean_name = name.strip()
    if not clean_name:
        raise ValidationError("Nome é obrigatório.", code="NAME_REQUIRED", field="name")
    existing = session.scalar(select(User).where(User.email == normalized_email))
    if existing is not None and existing.password_hash is not None:
        raise ConflictError("Usuário já provisionado.", code="USER_ALREADY_PROVISIONED")
    user = existing or User(name=clean_name, email=normalized_email)
    user.name = clean_name
    user.password_hash = hash_password(password)
    user.is_active = True
    session.add(user)
    session.flush()
    return user


class AuthService:
    def __init__(self, session: Session, *, clock: Clock | None = None) -> None:
        self.session = session
        self.clock = clock or SystemClock()

    def authenticate(self, email: str, password: str) -> User:
        user = self.session.scalar(
            select(User).where(User.email == email.strip().lower(), User.is_active.is_(True))
        )
        if user is None or user.password_hash is None or not verify_password(user.password_hash, password):
            raise AuthenticationError(
                "Email ou senha inválidos.", code="INVALID_CREDENTIALS"
            )
        return user

    def create_session(self, user: User, *, lifetime_hours: int) -> CreatedSession:
        raw_token = token_urlsafe(32)
        now = self._utc_now()
        record = AuthSession(
            user_id=user.id,
            token_hash=token_hash(raw_token),
            csrf_token=token_urlsafe(32),
            expires_at=now + timedelta(hours=lifetime_hours),
        )
        self.session.add(record)
        self.session.flush()
        return CreatedSession(record, raw_token)

    def resolve_session(self, raw_token: str | None) -> AuthSession:
        if not raw_token:
            raise AuthenticationError("Autenticação necessária.")
        record = self.session.scalar(
            select(AuthSession)
            .where(AuthSession.token_hash == token_hash(raw_token))
            .options(joinedload(AuthSession.user))
        )
        if record is None or record.revoked_at is not None or not record.user.is_active:
            raise AuthenticationError("Sessão inválida.", code="SESSION_INVALID")
        expires_at = record.expires_at
        if expires_at.tzinfo is None or expires_at.utcoffset() is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= self._utc_now():
            raise AuthenticationError("Sessão expirada.", code="SESSION_EXPIRED")
        return record

    def require_csrf(self, record: AuthSession, provided: str | None) -> None:
        if not provided or not compare_digest(record.csrf_token, provided):
            raise AuthenticationError(
                "Token CSRF ausente ou inválido.", code="CSRF_INVALID"
            )

    def revoke(self, record: AuthSession) -> None:
        record.revoked_at = self._utc_now()
        self.session.flush()

    def _utc_now(self) -> datetime:
        return self.clock.now().astimezone(timezone.utc)
