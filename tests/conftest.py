import pytest
from fastapi.testclient import TestClient

from app import main
from scripts.generate_dummy_data import generate


@pytest.fixture
def generated_store():
    return generate()


@pytest.fixture
def api_client(monkeypatch, generated_store):
    monkeypatch.setattr(main, "store", generated_store)
    with TestClient(main.app) as client:
        yield client