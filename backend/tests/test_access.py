from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.services.session import create_session_token, read_session_token


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_endpoints_need_login(client):
    for path in ["/api/emails", "/api/emails/stats", "/api/tasks", "/api/auth/me"]:
        response = client.get(path)
        assert response.status_code == 401, path
        assert response.json() == {"detail": "Not logged in"}


def test_email_query_parameter_no_longer_logs_you_in(client, make_user):
    """The old '?email=...' trick must not work any more."""
    user = make_user("victim@example.com")
    response = client.get("/api/emails", params={"email": user.email})
    assert response.status_code == 401


def test_session_token_round_trip():
    token = create_session_token(42)
    assert read_session_token(token) == 42


def test_tampered_token_is_rejected():
    token = create_session_token(42)
    assert read_session_token(token + "x") is None
    assert read_session_token("not-a-token") is None


def test_expired_token_is_rejected():
    expired = jwt.encode(
        {"sub": "42", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    assert read_session_token(expired) is None


def test_token_signed_with_wrong_key_is_rejected():
    forged = jwt.encode(
        {"sub": "42", "exp": datetime.now(timezone.utc) + timedelta(days=1)},
        "some-other-key-that-is-long-enough-123456",
        algorithm="HS256",
    )
    assert read_session_token(forged) is None


def test_me_returns_the_logged_in_user(client, make_user, login):
    login(make_user("me@example.com"))
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"email": "me@example.com"}