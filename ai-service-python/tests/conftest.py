import pytest
from fastapi.testclient import TestClient

import app.main as main_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main_module, "get_embedding_model", lambda: None)
    monkeypatch.setattr(main_module, "warmup_retriever", lambda: None)

    with TestClient(main_module.app) as test_client:
        yield test_client