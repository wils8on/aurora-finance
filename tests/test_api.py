"""Testes de integração HTTP da primeira API do Aurora Finance."""

from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from api.config import ApiSettings, Environment
from api.dependencies import get_current_user, get_session
from api.main import create_app
from models import (
    Account,
    AccountType,
    Category,
    CategoryType,
    Subcategory,
    User,
)


@pytest.fixture
def api_context(test_engine):
    session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with session_factory() as seed:
        user = User(name="Aurora", email="api@example.com")
        other_user = User(name="Outro", email="other-api@example.com")
        account = Account(
            user=user,
            name="Principal",
            institution="Banco Aurora",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("100.00"),
        )
        other_account = Account(
            user=other_user,
            name="Externa",
            account_type=AccountType.DIGITAL,
            initial_balance=Decimal("200.00"),
        )
        category = Category(user=user, name="Moradia", type=CategoryType.EXPENSE)
        other_category = Category(
            user=other_user,
            name="Externa",
            type=CategoryType.EXPENSE,
        )
        subcategory = Subcategory(category=category, name="Aluguel")
        seed.add_all([user, other_user])
        seed.commit()
        ids = {
            "user": user.id,
            "other_user": other_user.id,
            "account": account.id,
            "other_account": other_account.id,
            "category": category.id,
            "other_category": other_category.id,
            "subcategory": subcategory.id,
        }

    settings = ApiSettings(
        environment=Environment.TEST,
        cors_origins=("http://localhost:5173",),
    )
    app = create_app(settings)

    def override_session(request: Request) -> Generator[Session, None, None]:
        session = session_factory()
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

    def load_user(user_id: int) -> User:
        with session_factory() as session:
            user = session.get(User, user_id)
            assert user is not None
            session.expunge(user)
            return user

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user] = lambda: load_user(ids["user"])

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, app, ids, load_user


def test_health_returns_ok(api_context) -> None:
    client, _app, _ids, _load_user = api_context

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_openapi_exposes_the_current_api_scope(api_context) -> None:
    client, _app, _ids, _load_user = api_context

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert set(response.json()["paths"]) == {
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
        "/api/v1/accounts",
        "/api/v1/categories",
        "/api/v1/categories/{category_id}/subcategories",
        "/api/v1/transactions",
        "/api/v1/transactions/settled",
        "/api/v1/transactions/{transaction_id}",
        "/api/v1/transactions/{transaction_id}/settlements",
        "/api/v1/transactions/{transaction_id}/cancellation",
        "/api/v1/transaction-summaries",
    }


def test_list_accounts_only_returns_current_user_accounts(api_context) -> None:
    client, _app, _ids, _load_user = api_context

    response = client.get("/api/v1/accounts")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Principal"]


def test_create_account_and_serialize_money_as_string(api_context) -> None:
    client, _app, _ids, _load_user = api_context

    response = client.post(
        "/api/v1/accounts",
        json={
            "name": "Reserva",
            "institution": "Banco Aurora",
            "account_type": "SAVINGS",
            "initial_balance": "1234.56",
            "initial_balance_date": "2026-09-23",
        },
    )

    assert response.status_code == 201
    assert response.json()["initial_balance"] == "1234.56"
    assert response.json()["account_type"] == "SAVINGS"


@pytest.mark.parametrize("invalid", [1234.56, "R$ 1.234,56", "12.345", "NaN"])
def test_invalid_account_money_returns_422(api_context, invalid) -> None:
    client, _app, _ids, _load_user = api_context

    response = client.post(
        "/api/v1/accounts",
        json={
            "name": "Inválida",
            "account_type": "CHECKING",
            "initial_balance": invalid,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"


def test_account_name_conflict_returns_409_with_error_envelope(api_context) -> None:
    client, _app, _ids, _load_user = api_context

    response = client.post(
        "/api/v1/accounts",
        json={
            "name": "Principal",
            "account_type": "CHECKING",
            "initial_balance": "0.00",
        },
    )

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "ACCOUNT_NAME_CONFLICT"
    assert error["message"]
    assert error["field"] == "name"
    assert error["details"] == {}
    assert error["request_id"]
    assert response.headers["X-Request-ID"] == error["request_id"]


def test_user_id_cannot_control_account_ownership(api_context) -> None:
    client, _app, ids, _load_user = api_context

    response = client.post(
        "/api/v1/accounts",
        json={
            "user_id": ids["other_user"],
            "name": "Tentativa",
            "account_type": "CHECKING",
            "initial_balance": "0.00",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "user_id"


def test_list_and_create_categories(api_context) -> None:
    client, _app, _ids, _load_user = api_context

    listed = client.get("/api/v1/categories")
    created = client.post(
        "/api/v1/categories",
        json={"name": "Salário", "type": "INCOME"},
    )

    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()] == ["Moradia"]
    assert created.status_code == 201
    assert created.json()["type"] == "INCOME"


def test_category_conflict_returns_409(api_context) -> None:
    client, _app, _ids, _load_user = api_context

    response = client.post(
        "/api/v1/categories",
        json={"name": "Moradia", "type": "EXPENSE"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CATEGORY_NAME_CONFLICT"


def test_user_does_not_see_other_user_categories(api_context) -> None:
    client, app, ids, load_user = api_context
    app.dependency_overrides[get_current_user] = lambda: load_user(ids["other_user"])

    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Externa"]


def test_list_and_create_subcategories(api_context) -> None:
    client, _app, ids, _load_user = api_context

    listed = client.get(
        f"/api/v1/categories/{ids['category']}/subcategories"
    )
    created = client.post(
        f"/api/v1/categories/{ids['category']}/subcategories",
        json={"name": "Energia"},
    )

    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()] == ["Aluguel"]
    assert created.status_code == 201
    assert created.json()["name"] == "Energia"


@pytest.mark.parametrize("method", ["get", "post"])
def test_missing_category_returns_404_for_subcategories(api_context, method) -> None:
    client, _app, _ids, _load_user = api_context
    request = getattr(client, method)
    kwargs = {"json": {"name": "Energia"}} if method == "post" else {}

    response = request("/api/v1/categories/999999/subcategories", **kwargs)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CATEGORY_NOT_FOUND"


@pytest.mark.parametrize("method", ["get", "post"])
def test_other_user_category_is_hidden(api_context, method) -> None:
    client, _app, ids, _load_user = api_context
    request = getattr(client, method)
    kwargs = {"json": {"name": "Tentativa"}} if method == "post" else {}

    response = request(
        f"/api/v1/categories/{ids['other_category']}/subcategories",
        **kwargs,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CATEGORY_OWNERSHIP_MISMATCH"


def test_subcategory_conflict_returns_409(api_context) -> None:
    client, _app, ids, _load_user = api_context

    response = client.post(
        f"/api/v1/categories/{ids['category']}/subcategories",
        json={"name": "Aluguel"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SUBCATEGORY_NAME_CONFLICT"


def test_unexpected_error_does_not_expose_stack_trace(api_context) -> None:
    client, app, _ids, _load_user = api_context

    def explode() -> None:
        raise RuntimeError("segredo interno")

    app.add_api_route("/api/v1/test-unexpected", explode)
    response = client.get("/api/v1/test-unexpected")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "segredo interno" not in response.text
    assert "traceback" not in response.text.lower()


def test_cors_allows_only_configured_origin(api_context) -> None:
    client, _app, _ids, _load_user = api_context

    allowed = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    denied = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://malicioso.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers


def test_production_requires_secure_authentication_cookie() -> None:
    settings = ApiSettings(
        environment=Environment.PRODUCTION,
        cors_origins=("https://example.github.io",),
    )

    with pytest.raises(RuntimeError, match="Secure"):
        create_app(settings)


def test_samesite_none_requires_secure_cookie() -> None:
    settings = ApiSettings(
        environment=Environment.TEST,
        cors_origins=("https://app.example.com",),
        cookie_samesite="none",
    )

    with pytest.raises(RuntimeError, match="SameSite=None"):
        create_app(settings)


def test_invalid_cookie_samesite_is_rejected() -> None:
    settings = ApiSettings(
        environment=Environment.TEST,
        cors_origins=("http://localhost:5173",),
        cookie_samesite="invalid",
    )

    with pytest.raises(RuntimeError, match="AUTH_COOKIE_SAMESITE"):
        create_app(settings)


def test_cors_wildcard_is_rejected() -> None:
    settings = ApiSettings(
        environment=Environment.TEST,
        cors_origins=("*",),
    )

    with pytest.raises(RuntimeError, match="wildcard"):
        create_app(settings)
