import pytest
import asyncio
from fastapi.testclient import TestClient
from src.main import main  # adjust based on your actual app import
from src.dependencies.context import context_dependency
from src.config import settings


@pytest.fixture(scope="function")
def client():
    with TestClient(main) as test_client:
        yield test_client
