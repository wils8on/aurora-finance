"""Testes HTTP de Transactions, Settlements e resumos financeiros."""

from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from api.config import ApiSettings, Environment
from api.dependencies import get_current_user, get_session
from api.main import create_app
from models import (
    Account,
    AccountType,
    Category,
    CategoryType,
    Settlement,
    Subcategory,
    Transaction,
    TransactionType,
    User,
)
from services import TransactionService


@pytest.fixture
def financial_api(test_engine):
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with factory() as seed:
        user = User(name="Aurora", email="finance-api@example.com")
        other = User(name="Outro", email="other-finance-api@example.com")
        account = Account(user=user, name="Principal", account_type=AccountType.CHECKING)
        other_account = Account(user=other, name="Externa", account_type=AccountType.CHECKING)
        expense = Category(user=user, name="Moradia", type=CategoryType.EXPENSE)
        income = Category(user=user, name="Salário", type=CategoryType.INCOME)
        other_category = Category(user=other, name="Privada", type=CategoryType.EXPENSE)
        rent = Subcategory(category=expense, name="Aluguel")
        seed.add_all([user, other])
        seed.commit()
        ids = {
            "user": user.id,
            "other": other.id,
            "account": account.id,
            "other_account": other_account.id,
            "expense": expense.id,
            "income": income.id,
            "other_category": other_category.id,
            "rent": rent.id,
        }

    app = create_app(ApiSettings(environment=Environment.TEST, cors_origins=(), dev_user_email=None))

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

    def current_user() -> User:
        with factory() as session:
            value = session.get(User, ids["user"])
            assert value is not None
            session.expunge(value)
            return value

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_current_user] = current_user
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, ids, factory


def transaction_payload(ids, **changes):
    payload = {
        "transaction_type": "EXPENSE",
        "description": "Aluguel setembro",
        "amount": "1000.00",
        "competence_date": "2026-09-01",
        "due_date": "2026-09-10",
        "category_id": ids["expense"],
        "subcategory_id": ids["rent"],
        "notes": "Contrato residencial",
    }
    payload.update(changes)
    return payload


def create_transaction(client, ids, **changes):
    response = client.post("/api/v1/transactions", json=transaction_payload(ids, **changes))
    assert response.status_code == 201, response.text
    return response.json()


def settlement_payload(ids, **changes):
    payload = {
        "account_id": ids["account"],
        "amount": "1000.00",
        "settled_at": "2026-09-10T12:00:00-03:00",
        "notes": "PIX",
    }
    payload.update(changes)
    return payload


def list_url(**params):
    values = {"start_date": "2026-09-01", "end_date": "2026-09-30", **params}
    return "/api/v1/transactions", values


def test_create_pending_transaction_returns_derived_values(financial_api) -> None:
    client, ids, _factory = financial_api
    body = create_transaction(client, ids)
    assert body["persisted_status"] == "ACTIVE"
    assert body["derived_status"] == "PENDING"
    assert (body["amount"], body["settled_amount"], body["remaining_amount"]) == (
        "1000.00", "0.00", "1000.00"
    )
    assert body["category"] == {"id": ids["expense"], "name": "Moradia"}
    assert body["subcategory"] == {"id": ids["rent"], "name": "Aluguel"}


def test_create_income_without_subcategory(financial_api) -> None:
    client, ids, _factory = financial_api
    body = create_transaction(
        client, ids, transaction_type="INCOME", category_id=ids["income"],
        subcategory_id=None, description="Salário", amount="5000.00"
    )
    assert body["transaction_type"] == "INCOME"
    assert body["subcategory"] is None


@pytest.mark.parametrize("invalid", [1000, 10.5, "R$ 1.000,00", "10.123", "NaN", "0.00", "-1.00"])
def test_create_rejects_invalid_money(financial_api, invalid) -> None:
    client, ids, _factory = financial_api
    response = client.post("/api/v1/transactions", json=transaction_payload(ids, amount=invalid))
    assert response.status_code == 422
    assert response.json()["error"]["request_id"]


def test_create_rejects_category_type_mismatch(financial_api) -> None:
    client, ids, _factory = financial_api
    response = client.post(
        "/api/v1/transactions",
        json=transaction_payload(ids, transaction_type="INCOME"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CATEGORY_TYPE_MISMATCH"


def test_create_hides_foreign_category_as_not_found(financial_api) -> None:
    client, ids, _factory = financial_api
    response = client.post(
        "/api/v1/transactions", json=transaction_payload(ids, category_id=ids["other_category"])
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CATEGORY_OWNERSHIP_MISMATCH"


def test_create_forbids_client_user_id(financial_api) -> None:
    client, ids, _factory = financial_api
    response = client.post(
        "/api/v1/transactions", json=transaction_payload(ids, user_id=ids["other"])
    )
    assert response.status_code == 422


def test_historical_settled_creation_is_integral_and_timezone_aware(financial_api) -> None:
    client, ids, _factory = financial_api
    payload = transaction_payload(ids)
    payload["transaction_notes"] = payload.pop("notes")
    payload["settlement"] = settlement_payload(ids)
    response = client.post("/api/v1/transactions/settled", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["derived_status"] == "SETTLED"
    assert body["remaining_amount"] == "0.00"
    assert body["settlements"][0]["amount"] == "1000.00"
    assert body["settlements"][0]["settled_at"].endswith("Z")


@pytest.mark.parametrize(
    "settlement_change",
    [{"amount": "999.99"}, {"settled_at": "2026-09-10T12:00:00"}, {"amount": 1000}],
)
def test_historical_settled_creation_rejects_invalid_settlement(financial_api, settlement_change) -> None:
    client, ids, _factory = financial_api
    payload = transaction_payload(ids)
    payload["transaction_notes"] = payload.pop("notes")
    payload["settlement"] = settlement_payload(ids, **settlement_change)
    assert client.post("/api/v1/transactions/settled", json=payload).status_code == 422


def test_historical_creation_rolls_back_transaction_on_settlement_failure(financial_api, monkeypatch) -> None:
    client, ids, factory = financial_api
    original = TransactionService.add_settlement

    def fail(*args, **kwargs):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(TransactionService, "add_settlement", fail)
    payload = transaction_payload(ids, description="Deve reverter")
    payload["transaction_notes"] = payload.pop("notes")
    payload["settlement"] = settlement_payload(ids)
    assert client.post("/api/v1/transactions/settled", json=payload).status_code == 500
    monkeypatch.setattr(TransactionService, "add_settlement", original)
    with factory() as session:
        count = session.scalar(select(func.count()).select_from(Transaction))
    assert count == 0


def test_partial_then_complementary_settlement_changes_derived_status(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids)
    partial = client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements",
        json=settlement_payload(ids, amount="400.00"),
    )
    assert partial.status_code == 201
    assert partial.json()["derived_status"] == "PARTIAL"
    assert partial.json()["remaining_amount"] == "600.00"
    complete = client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements",
        json=settlement_payload(ids, amount="600.00", settled_at="2026-09-11T10:00:00Z"),
    )
    assert complete.status_code == 201
    assert complete.json()["derived_status"] == "SETTLED"
    assert len(complete.json()["settlements"]) == 2


def test_settlement_cannot_exceed_remaining(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids)
    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements",
        json=settlement_payload(ids, amount="1000.01"),
    )
    assert response.status_code == 409
    assert response.json()["error"]["details"]["remaining_amount"] == "1000.00"


def test_settlement_rejects_foreign_account(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids)
    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements",
        json=settlement_payload(ids, account_id=ids["other_account"]),
    )
    assert response.status_code == 404


def test_pending_transaction_can_be_cancelled_with_trace(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids)
    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/cancellation", json={"reason": "Duplicada"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["derived_status"] == "CANCELLED"
    assert body["cancellation"]["reason"] == "Duplicada"
    assert body["cancellation"]["cancelled_at"].endswith("Z")


def test_transaction_with_settlement_cannot_be_cancelled(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids)
    client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements",
        json=settlement_payload(ids, amount="1.00"),
    )
    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/cancellation", json={"reason": "Não pode"}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TRANSACTION_HAS_SETTLEMENTS"


def test_cancelled_transaction_cannot_receive_settlement(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids)
    client.post(f"/api/v1/transactions/{transaction['id']}/cancellation", json={})
    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements", json=settlement_payload(ids)
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TRANSACTION_CANCELLED"


def test_detail_and_mutations_do_not_expose_foreign_transaction(financial_api) -> None:
    client, ids, factory = financial_api
    with factory() as session:
        foreign = Transaction(
            user_id=ids["other"], category_id=ids["other_category"],
            transaction_type=TransactionType.EXPENSE, description="Segredo",
            amount=Decimal("10.00"), competence_date=date(2026, 9, 1)
        )
        session.add(foreign)
        session.commit()
        foreign_id = foreign.id
    assert client.get(f"/api/v1/transactions/{foreign_id}").status_code == 404
    assert client.post(
        f"/api/v1/transactions/{foreign_id}/settlements", json=settlement_payload(ids, amount="1.00")
    ).status_code == 404
    assert client.post(
        f"/api/v1/transactions/{foreign_id}/cancellation", json={}
    ).status_code == 404


def test_list_paginates_and_filters_without_foreign_records(financial_api) -> None:
    client, ids, _factory = financial_api
    create_transaction(client, ids, description="Aluguel A")
    create_transaction(client, ids, description="Aluguel B")
    create_transaction(
        client, ids, transaction_type="INCOME", category_id=ids["income"],
        subcategory_id=None, description="Salário", amount="5000.00"
    )
    path, params = list_url(page=1, page_size=1, transaction_type="EXPENSE", search="aluguel")
    body = client.get(path, params=params).json()
    assert len(body["items"]) == 1
    assert body["pagination"] == {"page": 1, "page_size": 1, "total_items": 2, "total_pages": 2}


def test_list_cancelled_visibility_and_status_filter(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids)
    client.post(f"/api/v1/transactions/{transaction['id']}/cancellation", json={})
    path, params = list_url()
    assert client.get(path, params=params).json()["pagination"]["total_items"] == 0
    params.update(include_cancelled=True, derived_status="CANCELLED")
    assert client.get(path, params=params).json()["items"][0]["derived_status"] == "CANCELLED"


def test_cash_list_counts_one_transaction_once_with_multiple_settlements(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids)
    for amount in ("400.00", "600.00"):
        client.post(
            f"/api/v1/transactions/{transaction['id']}/settlements",
            json=settlement_payload(ids, amount=amount),
        )
    path, params = list_url(perspective="CASH")
    body = client.get(path, params=params).json()
    assert body["pagination"]["total_items"] == 1
    assert body["items"][0]["period_settled_amount"] == "1000.00"


def test_cash_api_uses_sao_paulo_day_for_list_filters_and_summary(financial_api) -> None:
    client, ids, _factory = financial_api
    transaction = create_transaction(client, ids, amount="300.00")
    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements",
        json=settlement_payload(ids, amount="100.00", settled_at="2026-09-23T02:30:00Z"),
    )
    assert response.status_code == 201

    endpoint = "/api/v1/transactions"
    day_22 = {"perspective": "CASH", "start_date": "2026-09-22", "end_date": "2026-09-22"}
    body_22 = client.get(endpoint, params=day_22).json()
    assert body_22["pagination"]["total_items"] == 1
    assert body_22["items"][0]["reference_date"] == "2026-09-22"
    assert body_22["items"][0]["period_settled_amount"] == "100.00"
    assert body_22["items"][0]["settled_amount"] == "100.00"
    summary_22 = client.get("/api/v1/transaction-summaries", params=day_22).json()
    assert (summary_22["primary_2"], summary_22["primary_3"]) == ("100.00", "-100.00")

    day_23 = {"perspective": "CASH", "start_date": "2026-09-23", "end_date": "2026-09-23"}
    assert client.get(endpoint, params=day_23).json()["pagination"]["total_items"] == 0
    assert client.get("/api/v1/transaction-summaries", params=day_23).json()["primary_2"] == "0.00"

    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements",
        json=settlement_payload(ids, amount="200.00", settled_at="2026-09-23T12:00:00Z"),
    )
    assert response.status_code == 201
    body_23 = client.get(endpoint, params=day_23).json()
    assert body_23["pagination"]["total_items"] == 1
    assert body_23["items"][0]["reference_date"] == "2026-09-23"
    assert body_23["items"][0]["period_settled_amount"] == "200.00"
    summary_23 = client.get("/api/v1/transaction-summaries", params=day_23).json()
    assert (summary_23["primary_2"], summary_23["primary_3"]) == ("200.00", "-200.00")


def test_summary_distinguishes_competence_due_and_cash(financial_api) -> None:
    client, ids, _factory = financial_api
    expense = create_transaction(client, ids, amount="1000.00")
    create_transaction(
        client, ids, transaction_type="INCOME", category_id=ids["income"],
        subcategory_id=None, description="Salário", amount="5000.00", due_date="2026-10-05"
    )
    client.post(
        f"/api/v1/transactions/{expense['id']}/settlements",
        json=settlement_payload(ids, amount="400.00"),
    )
    base = {"start_date": "2026-09-01", "end_date": "2026-09-30"}
    competence = client.get("/api/v1/transaction-summaries", params={**base, "perspective": "COMPETENCE"}).json()
    due = client.get("/api/v1/transaction-summaries", params={**base, "perspective": "DUE"}).json()
    cash = client.get("/api/v1/transaction-summaries", params={**base, "perspective": "CASH"}).json()
    assert competence == {
        "perspective": "COMPETENCE", "primary_1": "5000.00", "primary_2": "1000.00",
        "primary_3": "4000.00", "receivable": "5000.00", "payable": "600.00"
    }
    assert due["primary_1"] == "0.00" and due["primary_2"] == "600.00"
    assert cash["primary_1"] == "0.00" and cash["primary_2"] == "400.00" and cash["primary_3"] == "-400.00"


@pytest.mark.parametrize("endpoint", ["/api/v1/transactions", "/api/v1/transaction-summaries"])
def test_period_is_required_and_invalid_ranges_are_rejected(financial_api, endpoint) -> None:
    client, _ids, _factory = financial_api
    assert client.get(endpoint).status_code == 422
    assert client.get(endpoint, params={"start_date": "2026-10-01", "end_date": "2026-09-01"}).status_code == 422


def test_pagination_limit_is_enforced(financial_api) -> None:
    client, _ids, _factory = financial_api
    response = client.get(
        "/api/v1/transactions",
        params={"start_date": "2026-09-01", "end_date": "2026-09-30", "page_size": 101},
    )
    assert response.status_code == 422


def test_database_contains_transaction_and_settlement_after_success(financial_api) -> None:
    client, ids, factory = financial_api
    transaction = create_transaction(client, ids)
    client.post(
        f"/api/v1/transactions/{transaction['id']}/settlements", json=settlement_payload(ids)
    )
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Transaction)) == 1
        assert session.scalar(select(func.count()).select_from(Settlement)) == 1
