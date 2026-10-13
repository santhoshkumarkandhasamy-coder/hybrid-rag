from tests.conftest import login


def test_requires_authentication(client):
    assert client.get("/documents").status_code == 401
    assert client.get("/admin/stats").status_code == 401
    assert client.get(
        "/documents", headers={"Authorization": "Bearer junk"}
    ).status_code == 401


def test_login_and_me(client, admin):
    me = client.get("/auth/me", headers=admin).json()
    assert me["username"] == "admin" and me["role"] == "admin"
    assert "password_hash" not in me


def test_bad_password_and_lockout(client):
    for _ in range(3):
        r = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert r.status_code == 401
    # Locked even with the right password
    r = client.post(
        "/auth/login",
        json={"username": "admin", "password": "AdminPass123"},
    )
    assert r.status_code == 429


def test_signup_disabled_by_default_then_toggle(client, admin):
    assert client.get("/auth/config").json() == {"allow_signup": False}
    body = {"username": "newbie", "password": "Passw0rd123"}
    assert client.post("/auth/register", json=body).status_code == 403

    client.put("/admin/settings", json={"allow_signup": True}, headers=admin)
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409
    headers = login(client, "newbie", "Passw0rd123")
    assert client.get("/auth/me", headers=headers).json()["role"] == "user"


def test_weak_password_rejected(client, admin):
    r = client.post(
        "/admin/users",
        json={"username": "bob", "password": "short"},
        headers=admin,
    )
    assert r.status_code == 400


def test_non_admin_forbidden(client, make_user):
    user = make_user("alice")
    assert client.get("/admin/users", headers=user).status_code == 403
    assert client.get("/admin/audit", headers=user).status_code == 403
    assert client.post(
        "/admin/users",
        json={"username": "x" * 5, "password": "Passw0rd123"},
        headers=user,
    ).status_code == 403


def test_disable_user_revokes_token(client, admin, make_user):
    user = make_user("alice")
    uid = next(
        u["id"]
        for u in client.get("/admin/users", headers=admin).json()["users"]
        if u["username"] == "alice"
    )
    client.patch(f"/admin/users/{uid}", json={"is_active": False},
                 headers=admin)
    assert client.get("/auth/me", headers=user).status_code == 401
    r = client.post(
        "/auth/login",
        json={"username": "alice", "password": "Passw0rd123"},
    )
    assert r.status_code == 403


def test_password_change_invalidates_old_token(client, make_user):
    user = make_user("alice")
    r = client.post(
        "/auth/change-password",
        json={"current_password": "Passw0rd123",
              "new_password": "NewPassw0rd456"},
        headers=user,
    )
    assert r.status_code == 200
    assert client.get("/auth/me", headers=user).status_code == 401
    fresh = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/auth/me", headers=fresh).status_code == 200


def test_last_admin_protected(client, admin):
    me = client.get("/auth/me", headers=admin).json()
    assert client.delete(
        f"/admin/users/{me['id']}", headers=admin
    ).status_code == 400
    assert client.patch(
        f"/admin/users/{me['id']}", json={"role": "user"}, headers=admin
    ).status_code == 400


def test_audit_log_records_events(client, admin, make_user):
    make_user("alice")
    events = client.get("/admin/audit", headers=admin).json()["events"]
    actions = {e["action"] for e in events}
    assert {"login.success", "admin.user.create"} <= actions


def test_stats(client, admin, make_user):
    make_user("alice")
    stats = client.get("/admin/stats", headers=admin).json()
    assert stats["users"]["total"] == 2
