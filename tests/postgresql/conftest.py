"""Infraestrutura opt-in para integração com PostgreSQL real e descartável."""

from collections.abc import Generator
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker


def _postgres_admin_url() -> str:
    value = os.getenv("AURORA_TEST_POSTGRES_URL", "").strip()
    if not value:
        pytest.skip(
            "Defina AURORA_TEST_POSTGRES_URL para executar a suíte PostgreSQL real.",
            allow_module_level=True,
        )
    url = make_url(value)
    if url.get_backend_name() != "postgresql":
        raise pytest.UsageError("AURORA_TEST_POSTGRES_URL deve apontar para PostgreSQL.")
    return value


ADMIN_URL = _postgres_admin_url()
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def postgres_database_url() -> Generator[str, None, None]:
    database_name = f"aurora_test_{uuid4().hex}"
    admin_engine = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    target_url = make_url(ADMIN_URL).set(database=database_name).render_as_string(
        hide_password=False
    )
    quoted_name = f'"{database_name}"'
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE {quoted_name}"))

        environment = os.environ.copy()
        environment["DATABASE_URL"] = target_url
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "alembic", "check"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
        )
        yield target_url
    finally:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f"DROP DATABASE IF EXISTS {quoted_name}"))
        admin_engine.dispose()


@pytest.fixture(scope="session")
def postgres_engine(postgres_database_url: str) -> Generator[Engine, None, None]:
    engine = create_engine(postgres_database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def postgres_session(postgres_engine: Engine) -> Generator[Session, None, None]:
    factory = sessionmaker(bind=postgres_engine, expire_on_commit=False)
    with factory() as session:
        try:
            yield session
        finally:
            session.rollback()
