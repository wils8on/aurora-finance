"""Testes integrados de autenticação, sessão, CSRF e isolamento financeiro."""

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from api.config import ApiSettings, Environment
from api.dependencies import get_session
from api.main import create_app
from models import (
    Account,
    AccountType,
    AuthSession,
    Category,
    CategoryType,
    Subcategory,
    Transaction,
    TransactionType,
)
from services import ConflictError, provision_user
from services.auth_service import token_hash

ORIGIN = "http://localhost:5173"
PASSWORD = "frase-secreta-longa"


@pytest.fixture
def auth_context(test_engine):
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with factory.begin() as seed:
        user_a = provision_user(
            seed, name="Pessoa A", email="a@example.com", password=PASSWORD
        )
        user_b = provision_user(
            seed, name="Pessoa B", email="b@example.com", password=PASSWORD
        )
        account_a = Account(
            user=user_a, name="Conta A", account_type=AccountType.CHECKING
        )
        account_b = Account(
            user=user_b, name="Conta B", account_type=AccountType.CHECKING
        )
        category_a = Category(
            user=user_a, name="Categoria A", type=CategoryType.EXPENSE
        )
        category_b = Category(
            user=user_b, name="Categoria B", type=CategoryType.EXPENSE
        )
        subcategory_b = Subcategory(category=category_b, name="Subcategoria B")
        transaction_b = Transaction(
            user=user_b,
            transaction_type=TransactionType.EXPENSE,
            description="Privada B",
            amount=Decimal("100.00"),
            competence_date=datetime(2026, 9, 1).date(),
            category=category_b,
            subcategory=subcategory_b,
        )
        seed.add_all(
            [account_a, account_b, category_a, category_b, subcategory_b, transaction_b]
        )
        seed.flush()
        ids = {
            "user_a": user_a.id,
            "account_a": account_a.id,
            "account_b": account_b.id,
            "category_a": category_a.id,
            "category_b": category_b.id,
            "subcategory_b": subcategory_b.id,
            "transaction_b": transaction_b.id,
        }

    settings = ApiSettings(
        environment=Environment.TEST,
        cors_origins=(ORIGIN,),
    )
    app = create_app(settings)

    def session_override(request: Request) -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
            if request.method in {"GET", "HEAD", "OPTIONS"}:
                session.rollback()
            else:
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session] = session_override
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, factory, ids


def login(client: TestClient, email: str = "a@example.com") -> tuple[dict, dict[str, str]]:
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return body, {"Origin": ORIGIN, "X-CSRF-Token": body["csrf_token"]}


def transaction_payload(ids: dict[str, int], **changes) -> dict:
    payload = {
        "transaction_type": "EXPENSE",
        "description": "Despesa A",
        "amount": "50.00",
        "competence_date": "2026-09-01",
        "due_date": None,
        "category_id": ids["category_a"],
        "subcategory_id": None,
        "notes": None,
    }
    payload.update(changes)
    return payload


def test_provisioning_hashes_password_and_rejects_duplicate(session) -> None:
    user = provision_user(
        session, name="Admin", email="ADMIN@example.com", password=PASSWORD
    )
    assert user.email == "admin@example.com"
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$argon2id$")
    session.flush()
    with pytest.raises(ConflictError, match="já provisionado"):
        provision_user(
            session, name="Admin", email="admin@example.com", password=PASSWORD
        )


def test_unauthenticated_auth_me_and_financial_api_return_401(auth_context) -> None:
    client, _factory, _ids = auth_context
    assert client.get("/api/v1/auth/me").status_code == 401
    response = client.get("/api/v1/accounts")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_valid_login_me_and_response_do_not_expose_credentials(auth_context) -> None:
    client, _factory, ids = auth_context
    body, _headers = login(client)
    assert body["user"] == {
        "id": ids["user_a"],
        "name": "Pessoa A",
        "email": "a@example.com",
        "currency": "BRL",
    }
    assert "password" not in str(body).lower()
    assert "httponly" in client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "a@example.com", "password": PASSWORD},
    ).headers["set-cookie"].lower()
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "a@example.com"


def test_invalid_login_has_no_session_and_conceals_reason(auth_context) -> None:
    client, _factory, _ids = auth_context
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "a@example.com", "password": "senha-incorreta"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert "set-cookie" not in response.headers


def test_csrf_and_origin_are_required_for_authenticated_writes(auth_context) -> None:
    client, _factory, _ids = auth_context
    _body, headers = login(client)
    payload = {
        "name": "Nova conta",
        "institution": None,
        "account_type": "CHECKING",
        "initial_balance": "0.00",
        "initial_balance_date": None,
    }
    assert client.post("/api/v1/accounts", json=payload).status_code == 403
    assert client.post(
        "/api/v1/accounts",
        headers={**headers, "Origin": "https://evil.example"},
        json=payload,
    ).status_code == 403
    assert client.post("/api/v1/accounts", headers=headers, json=payload).status_code == 201


def test_logout_revokes_server_session(auth_context) -> None:
    client, factory, _ids = auth_context
    _body, headers = login(client)
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    with factory() as session:
        records = session.scalars(select(AuthSession)).all()
        assert records and records[-1].revoked_at is not None


def test_invalid_and_expired_sessions_return_401(auth_context) -> None:
    client, factory, ids = auth_context
    client.cookies.set("aurora_session", "invalid-token", path="/api/v1")
    assert client.get("/api/v1/auth/me").status_code == 401

    raw_token = "expired-session-token"
    with factory.begin() as session:
        session.add(
            AuthSession(
                user_id=ids["user_a"],
                token_hash=token_hash(raw_token),
                csrf_token="expired-csrf",
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        )
    client.cookies.set("aurora_session", raw_token, path="/api/v1")
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"


def test_authenticated_user_a_cannot_use_or_mutate_user_b_data(auth_context) -> None:
    client, _factory, ids = auth_context
    _body, headers = login(client)

    listed = client.get("/api/v1/accounts")
    assert [item["name"] for item in listed.json()] == ["Conta A"]
    assert client.get(f"/api/v1/transactions/{ids['transaction_b']}").status_code == 404
    assert client.post(
        f"/api/v1/transactions/{ids['transaction_b']}/settlements",
        headers=headers,
        json={
            "account_id": ids["account_a"],
            "amount": "1.00",
            "settled_at": "2026-09-01T12:00:00-03:00",
            "notes": None,
        },
    ).status_code == 404
    assert client.post(
        f"/api/v1/transactions/{ids['transaction_b']}/cancellation",
        headers=headers,
        json={"reason": "tentativa"},
    ).status_code == 404
    assert client.post(
        "/api/v1/transactions",
        headers=headers,
        json=transaction_payload(ids, category_id=ids["category_b"]),
    ).status_code == 404
    assert client.post(
        "/api/v1/transactions",
        headers=headers,
        json=transaction_payload(ids, subcategory_id=ids["subcategory_b"]),
    ).status_code == 404

    created = client.post(
        "/api/v1/transactions", headers=headers, json=transaction_payload(ids)
    )
    assert created.status_code == 201
    assert client.post(
        f"/api/v1/transactions/{created.json()['id']}/settlements",
        headers=headers,
        json={
            "account_id": ids["account_b"],
            "amount": "50.00",
            "settled_at": "2026-09-01T12:00:00-03:00",
            "notes": None,
        },
    ).status_code == 404
