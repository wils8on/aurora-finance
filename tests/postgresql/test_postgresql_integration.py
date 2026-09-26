"""Gate financeiro, temporal e de autenticação em PostgreSQL real."""

from collections.abc import Generator
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import Request
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
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
    Settlement,
    TransactionType,
    User,
)
from services import (
    AuthService,
    ConflictError,
    DatePerspective,
    FixedClock,
    TransactionFilters,
    TransactionQueryService,
    TransactionService,
    provision_user,
)
from services.auth_service import token_hash
from services.clock import OPERATIONAL_TIMEZONE

pytestmark = pytest.mark.postgresql
ORIGIN = "http://localhost:5173"
PASSWORD = "frase-secreta-postgresql"


def _filters(user_id: int, perspective: DatePerspective, start: date, end: date):
    return TransactionFilters(
        user_id=user_id,
        perspective=perspective,
        start_date=start,
        end_date=end,
    )


def test_migrated_postgresql_schema_uses_expected_types_constraints_and_indexes(
    postgres_engine,
) -> None:
    inspector = inspect(postgres_engine)
    assert set(inspector.get_table_names()) == {
        "accounts",
        "alembic_version",
        "auth_sessions",
        "categories",
        "settlements",
        "subcategories",
        "transactions",
        "users",
    }

    transaction_columns = {
        column["name"]: column for column in inspector.get_columns("transactions")
    }
    settlement_columns = {
        column["name"]: column for column in inspector.get_columns("settlements")
    }
    session_columns = {
        column["name"]: column for column in inspector.get_columns("auth_sessions")
    }
    assert (transaction_columns["amount"]["type"].precision, transaction_columns["amount"]["type"].scale) == (18, 2)
    assert (settlement_columns["amount"]["type"].precision, settlement_columns["amount"]["type"].scale) == (18, 2)
    assert settlement_columns["settled_at"]["type"].timezone is True
    assert session_columns["expires_at"]["type"].timezone is True
    assert session_columns["revoked_at"]["nullable"] is True
    assert session_columns["token_hash"]["nullable"] is False
    assert any(item["name"] == "uq_auth_sessions_token_hash" for item in inspector.get_unique_constraints("auth_sessions"))
    assert any(item["name"] == "ix_auth_sessions_user_expires_at" for item in inspector.get_indexes("auth_sessions"))
    assert any(item["name"] == "ix_transactions_user_competence_date" for item in inspector.get_indexes("transactions"))
    assert any(item["name"] == "ix_settlements_account_settled_at" for item in inspector.get_indexes("settlements"))
    assert {item["constrained_columns"][0] for item in inspector.get_foreign_keys("settlements")} == {"account_id", "transaction_id"}

    with postgres_engine.connect() as connection:
        assert connection.scalar(text("show timezone"))


def test_postgresql_auth_sessions_csrf_logout_expiry_and_ownership(postgres_engine) -> None:
    factory = sessionmaker(bind=postgres_engine, expire_on_commit=False)
    with factory.begin() as seed:
        user_a = provision_user(seed, name="Postgres A", email="pg-a@example.com", password=PASSWORD)
        user_b = provision_user(seed, name="Postgres B", email="pg-b@example.com", password=PASSWORD)
        account_b = Account(user=user_b, name="Privada B", account_type=AccountType.CHECKING)
        category_b = Category(user=user_b, name="Privada B", type=CategoryType.EXPENSE)
        seed.add_all([account_b, category_b])
        seed.flush()
        transaction_b = TransactionService(seed).create_transaction(
            user_id=user_b.id,
            category_id=category_b.id,
            transaction_type=TransactionType.EXPENSE,
            description="Transaction privada B",
            amount=Decimal("20.00"),
            competence_date=date(2026, 9, 1),
        )
        user_a_id, account_b_id, category_b_id, transaction_b_id = (
            user_a.id,
            account_b.id,
            category_b.id,
            transaction_b.id,
        )

    app = create_app(ApiSettings(environment=Environment.TEST, cors_origins=(ORIGIN,)))

    def override_session(request: Request) -> Generator[Session, None, None]:
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

    app.dependency_overrides[get_session] = override_session
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/api/v1/accounts").status_code == 401
        invalid = client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"email": "pg-a@example.com", "password": "senha-incorreta"},
        )
        assert invalid.status_code == 401
        login = client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"email": "pg-a@example.com", "password": PASSWORD},
        )
        assert login.status_code == 200
        body = login.json()
        csrf = body["csrf_token"]
        assert body["user"]["id"] == user_a_id
        assert "password" not in login.text.lower()
        assert client.get("/api/v1/auth/me").status_code == 200
        assert client.get("/api/v1/accounts").json() == []
        assert client.get(f"/api/v1/transactions/{transaction_b_id}").status_code == 404

        assert client.post(
            "/api/v1/accounts",
            json={"name": "Sem CSRF", "account_type": "CHECKING", "initial_balance": "0.00"},
        ).status_code == 403
        headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
        assert client.post(
            f"/api/v1/transactions/{transaction_b_id}/cancellation",
            headers=headers,
            json={"reason": "tentativa"},
        ).status_code == 404
        assert client.post(
            f"/api/v1/transactions/{transaction_b_id}/settlements",
            headers=headers,
            json={
                "account_id": account_b_id,
                "amount": "1.00",
                "settled_at": "2026-09-01T12:00:00Z",
                "notes": None,
            },
        ).status_code == 404
        assert client.post(
            "/api/v1/transactions",
            headers=headers,
            json={
                "transaction_type": "EXPENSE",
                "description": "Tentativa B",
                "amount": "10.00",
                "competence_date": "2026-09-01",
                "due_date": None,
                "category_id": category_b_id,
                "subcategory_id": None,
                "notes": None,
            },
        ).status_code == 404

        created_category = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"name": "Categoria A", "type": "EXPENSE"},
        ).json()
        created_transaction = client.post(
            "/api/v1/transactions",
            headers=headers,
            json={
                "transaction_type": "EXPENSE",
                "description": "Despesa A",
                "amount": "10.00",
                "competence_date": "2026-09-01",
                "due_date": None,
                "category_id": created_category["id"],
                "subcategory_id": None,
                "notes": None,
            },
        ).json()
        assert client.post(
            f"/api/v1/transactions/{created_transaction['id']}/settlements",
            headers=headers,
            json={
                "account_id": account_b_id,
                "amount": "10.00",
                "settled_at": "2026-09-01T12:00:00Z",
                "notes": None,
            },
        ).status_code == 404

        raw_cookie = client.cookies.get("aurora_session")
        assert raw_cookie
        with factory() as verification:
            record = verification.scalar(
                select(AuthSession).where(AuthSession.user_id == user_a_id)
            )
            assert record is not None
            assert record.token_hash == token_hash(raw_cookie)
            assert record.token_hash != raw_cookie
            assert len(record.token_hash) == 64
            assert record.expires_at.tzinfo is not None
            persisted_user = verification.get(User, user_a_id)
            assert persisted_user is not None
            assert persisted_user.password_hash.startswith("$argon2id$")
            assert persisted_user.password_hash != PASSWORD

        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 401

        expired_token = "postgres-expired-session"
        with factory.begin() as session:
            session.add(
                AuthSession(
                    user_id=user_a_id,
                    token_hash=token_hash(expired_token),
                    csrf_token="expired-csrf",
                    expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
                )
            )
        client.cookies.set("aurora_session", expired_token, path="/api/v1")
        assert client.get("/api/v1/auth/me").json()["error"]["code"] == "SESSION_EXPIRED"


def test_postgresql_financial_oracle_timezone_multiple_settlements_and_constraints(
    postgres_session: Session,
) -> None:
    user = provision_user(
        postgres_session,
        name="Oráculo PostgreSQL",
        email="oracle-pg@example.com",
        password=PASSWORD,
    )
    account = Account(user=user, name="Principal", account_type=AccountType.CHECKING)
    income = Category(user=user, name="Receitas", type=CategoryType.INCOME)
    expense = Category(user=user, name="Despesas", type=CategoryType.EXPENSE)
    postgres_session.add_all([account, income, expense])
    postgres_session.flush()
    service = TransactionService(postgres_session)

    income_main = service.create_transaction(
        user_id=user.id,
        category_id=income.id,
        transaction_type=TransactionType.INCOME,
        description="Receita setembro",
        amount=Decimal("3000.00"),
        competence_date=date(2026, 9, 1),
        due_date=date(2026, 9, 10),
    )
    expense_main = service.create_transaction(
        user_id=user.id,
        category_id=expense.id,
        transaction_type=TransactionType.EXPENSE,
        description="Despesa setembro",
        amount=Decimal("1600.00"),
        competence_date=date(2026, 9, 1),
        due_date=date(2026, 9, 10),
    )
    service.add_settlement(
        transaction_id=income_main.id,
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("2000.00"),
        settled_at=datetime(2026, 9, 15, 12, tzinfo=timezone.utc),
    )
    service.add_settlement(
        transaction_id=expense_main.id,
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("300.00"),
        settled_at=datetime(2026, 8, 20, 12, tzinfo=timezone.utc),
    )
    service.add_settlement(
        transaction_id=expense_main.id,
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("700.00"),
        settled_at=datetime(2026, 9, 20, 12, tzinfo=timezone.utc),
    )
    historical, historical_settlement = service.create_settled_historical_transaction(
        user_id=user.id,
        category_id=income.id,
        account_id=account.id,
        transaction_type=TransactionType.INCOME,
        description="Receita histórica",
        amount=Decimal("700.00"),
        competence_date=date(2026, 8, 1),
        due_date=date(2026, 8, 10),
        settled_at=datetime(2026, 9, 25, 12, tzinfo=timezone.utc),
    )
    assert historical_settlement.transaction_id == historical.id

    pending_income = service.create_transaction(
        user_id=user.id,
        category_id=income.id,
        transaction_type=TransactionType.INCOME,
        description="Receita pendente futura",
        amount=Decimal("10.00"),
        competence_date=date(2026, 10, 1),
    )
    pending_expense = service.create_transaction(
        user_id=user.id,
        category_id=expense.id,
        transaction_type=TransactionType.EXPENSE,
        description="Despesa cancelável futura",
        amount=Decimal("10.00"),
        competence_date=date(2026, 10, 1),
    )
    service.cancel_transaction(transaction_id=pending_expense.id, user_id=user.id)
    assert service.get_derived_status(pending_income.id, user.id).value == "PENDING"
    with pytest.raises(ConflictError, match="exceder"):
        service.add_settlement(
            transaction_id=income_main.id,
            user_id=user.id,
            account_id=account.id,
            amount=Decimal("1000.01"),
            settled_at=datetime(2026, 9, 30, 12, tzinfo=timezone.utc),
        )

    query = TransactionQueryService(
        postgres_session,
        clock=FixedClock(datetime(2026, 10, 1, 12, tzinfo=OPERATIONAL_TIMEZONE)),
    )
    september_start, september_end = date(2026, 9, 1), date(2026, 9, 30)
    competence = query.summarize(
        _filters(user.id, DatePerspective.COMPETENCE, september_start, september_end)
    )
    due = query.summarize(
        _filters(user.id, DatePerspective.DUE, september_start, september_end)
    )
    cash = query.summarize(
        _filters(user.id, DatePerspective.CASH, september_start, september_end)
    )
    assert competence == type(competence)(
        Decimal("3000.00"), Decimal("1600.00"), Decimal("1400.00"),
        Decimal("1000.00"), Decimal("600.00")
    )
    assert (due.primary_1, due.primary_2, due.primary_3) == (
        Decimal("1000.00"), Decimal("600.00"), Decimal("1600.00")
    )
    assert (cash.primary_1, cash.primary_2, cash.primary_3) == (
        Decimal("2700.00"), Decimal("700.00"), Decimal("2000.00")
    )

    split = service.create_transaction(
        user_id=user.id,
        category_id=income.id,
        transaction_type=TransactionType.INCOME,
        description="Liquidação em dois dias operacionais",
        amount=Decimal("90.00"),
        competence_date=date(2026, 9, 22),
    )
    first_instant = datetime(2026, 9, 23, 2, 30, tzinfo=timezone.utc)
    service.add_settlement(
        transaction_id=split.id,
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("30.00"),
        settled_at=first_instant,
    )
    service.add_settlement(
        transaction_id=split.id,
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("60.00"),
        settled_at=datetime(2026, 9, 23, 12, tzinfo=timezone.utc),
    )
    postgres_session.flush()
    postgres_session.expire_all()

    persisted_first = postgres_session.scalar(
        select(Settlement)
        .where(Settlement.transaction_id == split.id)
        .order_by(Settlement.settled_at)
    )
    assert persisted_first is not None
    assert persisted_first.settled_at == first_instant
    assert persisted_first.settled_at.astimezone(OPERATIONAL_TIMEZONE).strftime("%Y-%m-%d %H:%M") == "2026-09-22 23:30"

    day_22 = query.list_transactions(
        _filters(user.id, DatePerspective.CASH, date(2026, 9, 22), date(2026, 9, 22))
    )
    day_23 = query.list_transactions(
        _filters(user.id, DatePerspective.CASH, date(2026, 9, 23), date(2026, 9, 23))
    )
    item_22 = next(item for item in day_22.items if item.id == split.id)
    item_23 = next(item for item in day_23.items if item.id == split.id)
    assert (item_22.reference_date, item_22.period_settled_amount, item_22.settled_amount) == (
        date(2026, 9, 22), Decimal("30.00"), Decimal("90.00")
    )
    assert (item_23.reference_date, item_23.period_settled_amount, item_23.settled_amount) == (
        date(2026, 9, 23), Decimal("60.00"), Decimal("90.00")
    )
    assert sum(item.id == split.id for item in day_22.items) == 1
    assert sum(item.id == split.id for item in day_23.items) == 1

    postgres_session.add(
        Account(
            user_id=user.id,
            name="Principal",
            account_type=AccountType.CHECKING,
        )
    )
    with pytest.raises(IntegrityError):
        postgres_session.flush()


def test_postgresql_fastapi_smoke_from_login_to_summary_and_logout(
    postgres_engine,
) -> None:
    factory = sessionmaker(bind=postgres_engine, expire_on_commit=False)
    with factory.begin() as seed:
        provision_user(
            seed,
            name="Smoke PostgreSQL",
            email="smoke-pg@example.com",
            password=PASSWORD,
        )

    app = create_app(ApiSettings(environment=Environment.TEST, cors_origins=(ORIGIN,)))

    def override_session(request: Request) -> Generator[Session, None, None]:
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

    app.dependency_overrides[get_session] = override_session
    with TestClient(app, raise_server_exceptions=False) as client:
        login = client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"email": "smoke-pg@example.com", "password": PASSWORD},
        )
        assert login.status_code == 200
        headers = {
            "Origin": ORIGIN,
            "X-CSRF-Token": login.json()["csrf_token"],
        }
        account = client.post(
            "/api/v1/accounts",
            headers=headers,
            json={
                "name": "Conta Smoke PG",
                "institution": None,
                "account_type": "CHECKING",
                "initial_balance": "0.00",
                "initial_balance_date": None,
            },
        )
        assert account.status_code == 201
        category = client.post(
            "/api/v1/categories",
            headers=headers,
            json={"name": "Categoria Smoke PG", "type": "INCOME"},
        )
        assert category.status_code == 201
        transaction = client.post(
            "/api/v1/transactions",
            headers=headers,
            json={
                "transaction_type": "INCOME",
                "description": "Movimentação Smoke PG",
                "amount": "90.00",
                "competence_date": "2026-09-22",
                "due_date": "2026-09-22",
                "category_id": category.json()["id"],
                "subcategory_id": None,
                "notes": None,
            },
        )
        assert transaction.status_code == 201
        transaction_id = transaction.json()["id"]
        settlement = client.post(
            f"/api/v1/transactions/{transaction_id}/settlements",
            headers=headers,
            json={
                "account_id": account.json()["id"],
                "amount": "90.00",
                "settled_at": "2026-09-23T02:30:00Z",
                "notes": None,
            },
        )
        assert settlement.status_code == 201
        assert settlement.json()["settlements"][0]["settled_at"] == "2026-09-23T02:30:00Z"

        period = {
            "perspective": "CASH",
            "start_date": "2026-09-22",
            "end_date": "2026-09-22",
        }
        listed = client.get("/api/v1/transactions", params=period)
        summary = client.get("/api/v1/transaction-summaries", params=period)
        assert listed.status_code == 200
        assert listed.json()["items"][0]["reference_date"] == "2026-09-22"
        assert summary.json()["primary_1"] == "90.00"
        assert summary.json()["primary_3"] == "90.00"
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
        assert client.get("/api/v1/accounts").status_code == 401
