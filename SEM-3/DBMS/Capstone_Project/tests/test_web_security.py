from __future__ import annotations

import re

import pytest

flask = pytest.importorskip("flask")

from app import create_app  # noqa: E402


@pytest.fixture
def web_client():
    app = create_app({"TESTING": True, "SECRET_KEY": "pytest-only-secret"})
    return app.test_client()


def test_login_page_renders_session_csrf_token_and_safe_cookie(web_client):
    response = web_client.get("/login")
    assert response.status_code == 200
    assert re.search(r'name="csrf_token" value="[A-Za-z0-9_-]+"', response.get_data(as_text=True))
    cookie_headers = response.headers.getlist("Set-Cookie")
    assert any("HttpOnly" in value and "SameSite=Lax" in value for value in cookie_headers)


def test_state_changing_request_without_csrf_token_is_rejected(web_client):
    response = web_client.post("/login", data={"username": "admin", "password": "Admin@123"})
    assert response.status_code == 400
