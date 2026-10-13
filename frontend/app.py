import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import api
from api import ApiError
from graph_view import create_graph_html

st.set_page_config(
    page_title="AKSAN INTELLIGENCE - Hybrid RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

SUPPORTED_TYPES = [
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "html", "htm", "txt", "md", "csv",
    "png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp",
]


def fmt_bytes(n: float) -> str:
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def show_error(exc: ApiError):
    st.error(exc.detail)


# ============================================================
# LOGIN
# ============================================================

def login_page():

    st.title("🧠 AKSAN INTELLIGENCE")
    st.caption("Secure Hybrid RAG · Vector Search + Knowledge Graph")

    if st.session_state.pop("flash", None):
        st.warning("Session expired. Please sign in.")

    try:
        allow_signup = api.get("/auth/config")["allow_signup"]
    except ApiError as exc:
        st.error(exc.detail)
        st.stop()

    _, centre, _ = st.columns([1, 2, 1])

    with centre:
        tabs = st.tabs(
            ["Sign in", "Create account"] if allow_signup else ["Sign in"]
        )

        with tabs[0]:
            with st.form("login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Sign in", type="primary", width="stretch"
                )

            if submitted:
                try:
                    data = api.post(
                        "/auth/login",
                        json={"username": username, "password": password},
                    )
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.rerun()
                except ApiError as exc:
                    show_error(exc)

        if allow_signup:
            with tabs[1]:
                with st.form("register"):
                    new_user = st.text_input("Choose a username")
                    new_pass = st.text_input(
                        "Choose a password", type="password",
                        help="At least 8 characters with letters and numbers.",
                    )
                    confirm = st.text_input(
                        "Confirm password", type="password"
                    )
                    created = st.form_submit_button(
                        "Create account", width="stretch"
                    )

                if created:
                    if new_pass != confirm:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            api.post(
                                "/auth/register",
                                json={"username": new_user,
                                      "password": new_pass},
                            )
                            st.success("Account created. Please sign in.")
                        except ApiError as exc:
                            show_error(exc)


# ============================================================
# USER PAGES
# ============================================================

def load_documents():
    return api.get("/documents")


def dashboard_page():

    st.header("📊 Dashboard")

    data = load_documents()
    docs = data["documents"]
    used, quota = data["storage_used_bytes"], data["quota_bytes"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documents", len(docs))
    c2.metric("Storage used", fmt_bytes(used))
    c3.metric("Text chunks", sum(d["chunks"] or 0 for d in docs))
    c4.metric(
        "Graph entities", sum(d["entities"] or 0 for d in docs)
    )

    st.progress(
        min(used / quota, 1.0) if quota else 0.0,
        text=f"Storage: {fmt_bytes(used)} of {fmt_bytes(quota)}",
    )

    if not docs:
        st.info("No documents yet. Open **My Documents** to upload files.")
        return

    left, right = st.columns([1, 2])

    df = pd.DataFrame(docs)

    with left:
        st.subheader("By file type")
        st.bar_chart(df.groupby("file_type").size())

    with right:
        st.subheader("Recent uploads")
        st.dataframe(
            df[["filename", "file_type", "size_bytes", "chunks",
                "created_at"]].head(10),
            hide_index=True,
            width="stretch",
        )


def documents_page():

    st.header("📁 My Documents")

    info = api.get("/documents/supported-types")

    st.subheader("Upload")
    files = st.file_uploader(
        f"Add one or more files (max {info['max_file_mb']} MB each)",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.get('upload_round', 0)}",
    )

    if files and st.button(
        f"🚀 Ingest {len(files)} file(s)", type="primary"
    ):
        with st.spinner("Reading files, building vector index and graph…"):
            try:
                result = api.post(
                    "/documents/upload",
                    files=[
                        ("files", (f.name, f.getvalue(), f.type))
                        for f in files
                    ],
                    timeout=1800,
                )
            except ApiError as exc:
                show_error(exc)
                result = None

        if result:
            for item in result["results"]:
                if item["status"] == "completed":
                    st.success(
                        f"✅ {item['filename']} — {item['chunks']} chunks, "
                        f"{item['entities']} entities"
                    )
                    if item.get("warning"):
                        st.warning(item["warning"])
                else:
                    st.error(f"❌ {item['filename']}: {item['error']}")

            st.session_state.upload_round = (
                st.session_state.get("upload_round", 0) + 1
            )

    st.divider()
    st.subheader("Library")

    data = load_documents()

    if not data["documents"]:
        st.info("Your library is empty.")
        return

    st.caption(
        f"{fmt_bytes(data['storage_used_bytes'])} of "
        f"{fmt_bytes(data['quota_bytes'])} used"
    )

    for doc in data["documents"]:
        with st.expander(
            f"{doc['filename']} · {doc['file_type']} · "
            f"{fmt_bytes(doc['size_bytes'])}"
        ):
            st.caption(
                f"Uploaded {doc['created_at'][:19]} · "
                f"{doc['characters']:,} characters · "
                f"{doc['chunks']} chunks · {doc['entities']} entities · "
                f"{doc['relationships']} relationships"
            )
            if doc.get("error"):
                st.warning(doc["error"])

            a, b, c = st.columns(3)

            if a.button("👁 Preview text", key=f"pv{doc['id']}"):
                text = api.get(f"/documents/{doc['id']}/text")["text"]
                st.text_area(
                    "Extracted text", text[:20000], height=250,
                    key=f"txt{doc['id']}",
                )

            try:
                raw = api.call(
                    "GET", f"/documents/{doc['id']}/download"
                ).content
                b.download_button(
                    "⬇ Download", raw, file_name=doc["filename"],
                    key=f"dl{doc['id']}",
                )
            except ApiError:
                b.caption("file unavailable")

            if c.button("🗑 Delete", key=f"rm{doc['id']}"):
                api.delete(f"/documents/{doc['id']}")
                st.rerun()


def chat_page():

    st.header("💬 Hybrid RAG Chat")

    docs = load_documents()["documents"]

    if not docs:
        st.info("Upload documents first.")
        return

    labels = {d["id"]: d["filename"] for d in docs}

    selected = st.multiselect(
        "Documents to search (empty = all)",
        options=list(labels),
        format_func=labels.get,
    )
    top_k = st.slider("Results per source", 1, 10, 5)

    history = st.session_state.setdefault("chat_history", [])

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                st.caption("Sources: " + ", ".join(msg["sources"]))

    question = st.chat_input("Ask a question about your documents…")

    if not question:
        return

    history.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching vectors + knowledge graph…"):
            try:
                reply = api.post(
                    "/chat",
                    json={"query": question,
                          "document_ids": selected or None,
                          "top_k": top_k},
                    timeout=180,
                )
                answer, sources = reply["answer"], reply["sources"]
                st.markdown(answer)
                if sources:
                    st.caption("Sources: " + ", ".join(sources))
                st.caption(
                    f"Vector hits: {reply['vector_result_count']} · "
                    f"Graph hits: {reply['graph_result_count']}"
                )
            except ApiError as exc:
                answer, sources = f"⚠️ {exc.detail}", []
                st.error(answer)

    history.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )


def graph_page():

    st.header("🕸️ Knowledge Graph")

    docs = load_documents()["documents"]

    if not docs:
        st.info("Upload documents first.")
        return

    labels = {d["id"]: d["filename"] for d in docs}
    doc_id = st.selectbox(
        "Document", list(labels), format_func=labels.get
    )

    try:
        graph = api.get(f"/graph/{doc_id}")
    except ApiError as exc:
        show_error(exc)
        return

    entities = graph.get("entities", [])
    relationships = graph.get("relationships", [])

    a, b = st.columns(2)
    a.metric("Entities", len(entities))
    b.metric("Relationships", len(relationships))

    if entities:
        components.html(
            create_graph_html(graph), height=650, scrolling=True
        )
        t1, t2 = st.tabs(["Entities", "Relationships"])
        t1.dataframe(pd.DataFrame(entities), hide_index=True,
                     width="stretch")
        if relationships:
            t2.dataframe(pd.DataFrame(relationships), hide_index=True,
                         width="stretch")
    else:
        st.info("No graph data for this document.")


def account_page():

    st.header("👤 Account")

    user = st.session_state.user
    st.write(f"**Username:** {user['username']}")
    st.write(f"**Role:** {user['role']}")
    st.write(f"**Storage quota:** {user['quota_mb']} MB")

    st.subheader("Change password")

    with st.form("pw"):
        current = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        go = st.form_submit_button("Update password")

    if go:
        if new != confirm:
            st.error("Passwords do not match.")
        else:
            try:
                data = api.post(
                    "/auth/change-password",
                    json={"current_password": current,
                          "new_password": new},
                )
                st.session_state.token = data["access_token"]
                st.success("Password updated.")
            except ApiError as exc:
                show_error(exc)


# ============================================================
# ADMIN CONTROL PANEL
# ============================================================

def admin_page():

    st.header("🛡️ Admin Control Panel")

    overview, users_tab, docs_tab, audit_tab, settings_tab = st.tabs(
        ["Overview", "Users", "All documents", "Audit log", "Settings"]
    )

    with overview:
        stats = api.get("/admin/stats")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Users", stats["users"]["total"])
        c2.metric("Admins", stats["users"]["admins"] or 0)
        c3.metric("Documents", stats["documents"]["total"])
        c4.metric("Storage", fmt_bytes(stats["documents"]["bytes"]))
        c5.metric("Chat queries", stats["chat_queries"])

        left, right = st.columns(2)
        if stats["per_user"]:
            df = pd.DataFrame(stats["per_user"])
            df["used_mb"] = df["bytes"] / 1024 / 1024
            left.subheader("Storage per user (MB)")
            left.bar_chart(df.set_index("username")["used_mb"])
        if stats["by_type"]:
            right.subheader("Documents by type")
            right.bar_chart(
                pd.DataFrame(stats["by_type"]).set_index("file_type")
            )

    with users_tab:
        users = api.get("/admin/users")["users"]

        df = pd.DataFrame(users)
        df["storage"] = df["storage_bytes"].map(fmt_bytes)
        st.dataframe(
            df[["id", "username", "role", "is_active", "documents",
                "storage", "quota_mb", "last_login"]],
            hide_index=True, width="stretch",
        )

        st.subheader("Create user")
        with st.form("create_user", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            name = c1.text_input("Username")
            pw = c2.text_input("Password", type="password")
            role = c3.selectbox("Role", ["user", "admin"])
            quota = c4.number_input("Quota (MB)", 1, 100000, 500)
            if st.form_submit_button("Create"):
                try:
                    api.post(
                        "/admin/users",
                        json={"username": name, "password": pw,
                              "role": role, "quota_mb": int(quota)},
                    )
                    st.success(f"Created {name}.")
                    st.rerun()
                except ApiError as exc:
                    show_error(exc)

        st.subheader("Manage user")
        by_name = {u["username"]: u for u in users}
        target = by_name[st.selectbox("User", list(by_name))]

        with st.form("edit_user"):
            c1, c2, c3 = st.columns(3)
            new_role = c1.selectbox(
                "Role", ["user", "admin"],
                index=0 if target["role"] == "user" else 1,
            )
            active = c2.checkbox("Active", value=target["is_active"])
            new_quota = c3.number_input(
                "Quota (MB)", 1, 100000, int(target["quota_mb"])
            )
            new_pw = st.text_input(
                "Reset password (leave blank to keep)", type="password"
            )
            save = st.form_submit_button("Save changes", type="primary")

        if save:
            body = {"role": new_role, "is_active": active,
                    "quota_mb": int(new_quota)}
            if new_pw:
                body["new_password"] = new_pw
            try:
                api.patch(f"/admin/users/{target['id']}", json=body)
                st.success("User updated.")
                st.rerun()
            except ApiError as exc:
                show_error(exc)

        with st.expander("⚠️ Danger zone"):
            st.write(
                f"Delete **{target['username']}** and all "
                f"{target['documents']} of their documents."
            )
            if st.button("Delete user", key="del_user"):
                try:
                    api.delete(f"/admin/users/{target['id']}")
                    st.rerun()
                except ApiError as exc:
                    show_error(exc)

    with docs_tab:
        docs = api.get("/admin/documents")["documents"]
        st.caption(
            "Admins can see and remove files, but cannot read their content."
        )
        if docs:
            st.dataframe(
                pd.DataFrame(docs)[
                    ["owner", "filename", "file_type", "size_bytes",
                     "chunks", "created_at"]
                ],
                hide_index=True, width="stretch",
            )
            names = {
                d["id"]: f"{d['owner']} / {d['filename']}" for d in docs
            }
            pick = st.selectbox(
                "Remove document", list(names), format_func=names.get
            )
            if st.button("Delete document"):
                api.delete(f"/admin/documents/{pick}")
                st.rerun()
        else:
            st.info("No documents.")

    with audit_tab:
        prefix = st.text_input("Filter by action prefix (e.g. login)")
        events = api.get(
            "/admin/audit", params={"limit": 500, "action": prefix or None}
        )["events"]
        if events:
            st.dataframe(
                pd.DataFrame(events)[
                    ["ts", "username", "action", "detail"]
                ],
                hide_index=True, width="stretch",
            )
        else:
            st.info("No events.")

    with settings_tab:
        stats = api.get("/admin/stats")
        signup = st.toggle(
            "Allow self-registration on the login page",
            value=stats["allow_signup"],
        )
        if signup != stats["allow_signup"]:
            api.put("/admin/settings", json={"allow_signup": signup})
            st.rerun()


# ============================================================
# MAIN
# ============================================================

if not st.session_state.get("token"):
    login_page()
    st.stop()

user = st.session_state.user

PAGES = {
    "📊 Dashboard": dashboard_page,
    "📁 My Documents": documents_page,
    "💬 Chat": chat_page,
    "🕸️ Knowledge Graph": graph_page,
    "👤 Account": account_page,
}

if user["role"] == "admin":
    PAGES["🛡️ Admin Panel"] = admin_page

with st.sidebar:
    st.title("🧠 AKSAN")
    st.write(f"Signed in as **{user['username']}**")
    st.caption(user["role"].capitalize())
    choice = st.radio("Navigate", list(PAGES), label_visibility="collapsed")
    st.divider()
    if st.button("Sign out", width="stretch"):
        st.session_state.clear()
        st.rerun()

try:
    PAGES[choice]()
except ApiError as exc:
    show_error(exc)
