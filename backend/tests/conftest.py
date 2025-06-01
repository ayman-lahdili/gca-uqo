import os
import pytest
import pytest_asyncio
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool

from src.main import create_app
from src.factory import Factory
from src.config import Settings, settings

from tests.scripts.initial_data import init_db


@pytest.fixture(scope="function")
def test_settings(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Generator[Settings, None, None]:
    db_path = tmp_path_factory.mktemp("tmp_test_databases") / "test_database.db"
    monkeypatch.setenv("SQLLITE_FILE_NAME", str(db_path))

    yield settings()


@pytest.fixture(scope="function")
def engine(test_settings: Settings) -> Engine:
    return create_engine(
        test_settings.SQLALCHEMY_DATABASE_URI,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="function")
def empty_database(test_settings: Settings, engine: Engine) -> None:
    init_db(test_settings, engine)


@pytest_asyncio.fixture(scope="function")
async def factory(
    test_settings: Settings, engine: Engine, empty_database: None
) -> Factory:
    return await Factory.create(test_settings, engine)


@pytest.fixture(scope="function")
def client(test_settings: Settings):
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client
