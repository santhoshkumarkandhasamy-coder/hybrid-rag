"""Thin HTTP client for the Hybrid RAG backend."""

import os

import requests
import streamlit as st

BACKEND_URL = os.getenv(
    "BACKEND_URL", "http://127.0.0.1:8000"
).rstrip("/")


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _headers() -> dict:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def call(method: str, path: str, timeout: int = 60, **kwargs):
    """Perform a request; raise ApiError on failure. A 401 on an
    authenticated call ends the session."""

    try:
        response = requests.request(
            method,
            f"{BACKEND_URL}{path}",
            headers=_headers(),
            timeout=timeout,
            **kwargs,
        )
    except requests.exceptions.RequestException as exc:
        raise ApiError(0, f"Backend not reachable: {exc}")

    if response.status_code == 401 and st.session_state.get("token"):
        st.session_state.clear()
        st.session_state["flash"] = "Session expired. Please sign in."
        st.rerun()

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise ApiError(response.status_code, str(detail))

    return response


def get(path, **kw):
    return call("GET", path, **kw).json()


def post(path, **kw):
    return call("POST", path, **kw).json()


def patch(path, **kw):
    return call("PATCH", path, **kw).json()


def put(path, **kw):
    return call("PUT", path, **kw).json()


def delete(path, **kw):
    return call("DELETE", path, **kw).json()
