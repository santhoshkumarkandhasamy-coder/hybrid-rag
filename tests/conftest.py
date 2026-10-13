import sys
import types

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Fresh app + database per test, heavy ML deps stubbed."""

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "AdminPass123")
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "1")
    monkeypatch.setenv("DEFAULT_USER_QUOTA_MB", "1")
    monkeypatch.setenv("MAX_FAILED_LOGINS", "3")
    for var in ("OPENAI_API_KEY", "OPENAI_CHAT_MODEL", "NEO4J_URI",
                "NEO4J_USERNAME", "NEO4J_PASSWORD"):
        monkeypatch.setenv(var, "")

    for name in list(sys.modules):
        if name.startswith("backend"):
            del sys.modules[name]

    fake = types.ModuleType("backend.ingestion.vector_store")
    saved = {}

    class FakeStore:
        def __init__(self, chunks, metadatas):
            self.items = list(zip(chunks, metadatas or [{}] * len(chunks)))

        def similarity_search_with_score(self, query, k=5):
            words = set(query.lower().split())
            scored = sorted(
                self.items,
                key=lambda it: -len(words & set(it[0].lower().split())),
            )
            doc = types.SimpleNamespace
            return [
                (doc(page_content=c, metadata=m), 0.5) for c, m in scored[:k]
            ]

    fake.create_vector_store = (
        lambda chunks, metadatas=None: FakeStore(chunks, metadatas)
    )
    fake.save_vector_store = (
        lambda store, document_id: saved.__setitem__(document_id, store)
    )
    fake.load_vector_store = lambda document_id: saved[document_id]
    fake.delete_vector_store = lambda document_id: saved.pop(document_id, None)
    monkeypatch.setitem(sys.modules, "backend.ingestion.vector_store", fake)

    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as test_client:
        yield test_client


def login(client, username, password):
    response = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def admin(client):
    return login(client, "admin", "AdminPass123")


@pytest.fixture()
def make_user(client, admin):
    def _make(name, quota_mb=None):
        body = {"username": name, "password": "Passw0rd123"}
        if quota_mb:
            body["quota_mb"] = quota_mb
        assert client.post(
            "/admin/users", json=body, headers=admin
        ).status_code == 201
        return login(client, name, "Passw0rd123")

    return _make
