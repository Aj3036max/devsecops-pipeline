import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app({"TESTING": True}).test_client()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json == {"status": "ok"}


def test_security_headers_present(client):
    h = client.get("/health").headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in h["Content-Security-Policy"]
    assert "Strict-Transport-Security" in h


def test_create_get_delete_note(client):
    r = client.post("/api/notes", json={"title": "Audit", "body": "Vérifier IAM"})
    assert r.status_code == 201
    note_id = r.json["id"]
    assert client.get(f"/api/notes/{note_id}").json["title"] == "Audit"
    assert client.delete(f"/api/notes/{note_id}").status_code == 204
    assert client.get(f"/api/notes/{note_id}").status_code == 404


@pytest.mark.parametrize("payload", [{}, {"title": ""}, {"title": "x" * 500}, {"title": "ok", "body": 123}, ["list"]])
def test_input_validation(client, payload):
    r = client.post("/api/notes", json=payload)
    assert r.status_code == 400
    assert "error" in r.json


def test_rejects_non_json(client):
    assert client.post("/api/notes", data="title=x").status_code == 415


def test_rejects_oversized_request(client):
    r = client.post("/api/notes", data="x" * 20_000, content_type="application/json")
    assert r.status_code == 413


def test_errors_do_not_leak_internals(client):
    r = client.get("/api/notes/does-not-exist")
    assert r.status_code == 404
    assert "Traceback" not in r.get_data(as_text=True)
