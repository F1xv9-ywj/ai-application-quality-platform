import pytest
from fastapi.testclient import TestClient

from evalforge.app import create_app


@pytest.fixture()
def client() -> TestClient:
    with TestClient(create_app()) as value:
        yield value
