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
