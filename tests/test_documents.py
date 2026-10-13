import io

from tests.conftest import login


def upload(client, headers, name, content, ctype="text/plain"):
    return client.post(
        "/documents/upload",
        files=[("files", (name, io.BytesIO(content), ctype))],
        headers=headers,
    )


def test_multi_file_upload_and_listing(client, make_user):
    user = make_user("alice")
    r = client.post(
        "/documents/upload",
        files=[
            ("files", ("a.txt", b"Alpha document text", "text/plain")),
            ("files", ("b.html", b"<html><body><p>Beta</p></body></html>",
                       "text/html")),
            ("files", ("c.exe", b"MZ", "application/octet-stream")),
        ],
        headers=user,
    )
    results = r.json()["results"]
    assert [x["status"] for x in results] == [
        "completed", "completed", "failed"
    ]
    assert results[0]["warning"] is None

    listing = client.get("/documents", headers=user).json()
    assert len(listing["documents"]) == 2
    assert listing["storage_used_bytes"] > 0


def test_users_are_isolated(client, make_user):
    alice = make_user("alice")
    bob = make_user("bobby")
    doc = upload(client, alice, "a.txt", b"secret").json()["results"][0]
    doc_id = doc["document_id"]

    assert client.get("/documents", headers=bob).json()["documents"] == []
    for path in ("text", "download"):
        assert client.get(
            f"/documents/{doc_id}/{path}", headers=bob
        ).status_code == 404
    assert client.delete(
        f"/documents/{doc_id}", headers=bob
    ).status_code == 404
    assert client.get(f"/graph/{doc_id}", headers=bob).status_code == 404
    assert client.post(
        "/chat", json={"query": "hi", "document_ids": [doc_id]},
        headers=bob,
    ).status_code == 404
    # no docs of his own
    assert client.post(
        "/chat", json={"query": "hi"}, headers=bob
    ).status_code == 400

    text = client.get(f"/documents/{doc_id}/text", headers=alice).json()
    assert text["text"] == "secret"


def test_admin_cannot_read_content_but_can_delete(client, admin, make_user):
    alice = make_user("alice")
    doc_id = upload(client, alice, "a.txt", b"private").json()[
        "results"][0]["document_id"]

    assert client.get(
        f"/documents/{doc_id}/text", headers=admin
    ).status_code == 404
    assert len(client.get(
        "/admin/documents", headers=admin).json()["documents"]) == 1
    assert client.delete(
        f"/admin/documents/{doc_id}", headers=admin
    ).status_code == 200
    assert client.get("/documents", headers=alice).json()["documents"] == []


def test_quota_enforced(client, make_user):
    alice = make_user("alice", quota_mb=1)
    big = b"x" * (700 * 1024)
    assert upload(client, alice, "1.txt", big).json()["results"][0][
        "status"] == "completed"
    second = upload(client, alice, "2.txt", big).json()["results"][0]
    assert second["status"] == "failed" and "quota" in second["error"]


def test_file_size_limit(client, make_user):
    alice = make_user("alice")
    r = upload(client, alice, "huge.txt", b"x" * (2 * 1024 * 1024))
    assert "limit" in r.json()["results"][0]["error"]


def test_delete_removes_files(client, make_user, tmp_path):
    alice = make_user("alice")
    doc_id = upload(client, alice, "a.txt", b"bye").json()["results"][0][
        "document_id"]
    assert list((tmp_path / "uploads").rglob("a.txt"))
    client.delete(f"/documents/{doc_id}", headers=alice)
    assert not list((tmp_path / "uploads").rglob("a.txt"))


def test_path_traversal_filename_sanitised(client, make_user, tmp_path):
    alice = make_user("alice")
    r = upload(client, alice, "../../evil.txt", b"x").json()["results"][0]
    assert r["filename"] == "evil.txt"
    assert not (tmp_path.parent / "evil.txt").exists()


def test_offline_chat_and_graph(client, make_user):
    alice = make_user("alice")
    text = (
        b"Acme Corp was founded by Jane Smith in Berlin. "
        b"Acme Corp builds Widget Pro for Siemens AG. "
        b"The weather is mild in spring."
    )
    doc = upload(client, alice, "notes.txt", text).json()["results"][0]
    assert doc["entities"] > 0 and doc["relationships"] > 0

    graph = client.get(f"/graph/{doc['document_id']}", headers=alice).json()
    names = {e["name"] for e in graph["entities"]}
    assert "Acme Corp" in names and "Jane Smith" in names

    reply = client.post(
        "/chat", json={"query": "Who founded Acme Corp?"}, headers=alice
    )
    assert reply.status_code == 200, reply.text
    body = reply.json()
    assert "Jane Smith" in body["answer"]
    assert body["sources"] == ["notes.txt"]


def test_graph_removed_with_document(client, make_user):
    alice = make_user("alice")
    doc_id = upload(client, alice, "a.txt",
                    b"Acme Corp hired Jane Smith.").json()["results"][0][
        "document_id"]
    client.delete(f"/documents/{doc_id}", headers=alice)
    from backend.core.db import get_conn
    with get_conn() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM graph_entities").fetchone()[0] == 0


def test_offline_overview_and_names_not_split(client, make_user):
    alice = make_user("alice")
    text = (
        b"ESWARA RAO DUDDU\nChartered Accountant\n\nEXPERIENCE\n"
        b"Executed end-to-end securitisation transactions.\n\nEDUCATION\n"
        b"Qualified CA in 2012.\n"
    )
    doc = upload(client, alice, "resume.txt", text).json()["results"][0]
    graph = client.get(f"/graph/{doc['document_id']}", headers=alice).json()
    names = {e["name"] for e in graph["entities"]}
    assert "ESWARA RAO DUDDU" in names
    assert "RAO" not in names and "ESWARA" not in names

    reply = client.post(
        "/chat", json={"query": "tell about this resume"}, headers=alice
    ).json()
    assert "ESWARA RAO DUDDU" in reply["answer"]
    assert "EXPERIENCE" in reply["answer"]
    assert reply["sources"] == ["resume.txt"]


def test_ollama_answer_and_fallback(client, make_user, monkeypatch):
    alice = make_user("alice")
    upload(client, alice, "r.txt", b"Jane Smith is a chartered accountant.")

    from backend.core import config
    import requests

    monkeypatch.setattr(config, "USE_OLLAMA", True)
    monkeypatch.setattr(config, "OLLAMA_MODEL", "llama3.2")

    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": "Jane is a CA."}}

    monkeypatch.setattr(requests, "post", lambda *a, **k: Resp())
    r = client.post("/chat", json={"query": "who is Jane Smith"}, headers=alice)
    assert r.json()["answer"] == "Jane is a CA."

    def boom(*a, **k):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", boom)
    r = client.post("/chat", json={"query": "who is Jane Smith"}, headers=alice)
    assert r.status_code == 200 and "Jane Smith" in r.json()["answer"]


def test_offline_synonyms_where_studied(client, make_user):
    alice = make_user("alice")
    text = (
        b"[Page 1]\nESWARA RAO DUDDU\nChartered Accountant\n"
        b"[Page 2]\nEDUCATION\nB.Com, Andhra University, 2008\n"
        b"Qualified Chartered Accountant, ICAI, 2012\n"
    )
    upload(client, alice, "resume.txt", text)
    r = client.post(
        "/chat", json={"query": "where he studied"}, headers=alice
    ).json()["answer"]
    assert "Andhra University" in r
    assert "[Page" not in r
