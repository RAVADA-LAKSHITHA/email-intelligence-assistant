import os
import tempfile
import uuid
from pathlib import Path

# These MUST be set before the app is imported. Environment variables override
# backend/.env, so the tests never touch your real database or real services.
_TEST_DB = Path(tempfile.gettempdir()) / "email_assistant_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["SECRET_KEY"] = "test-secret-key-for-tests-only-0123456789"
os.environ["COOKIE_SECURE"] = "False"

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.models import User, Email
from app.services.session import create_session_token

# Safety guard: refuse to run against anything except the temporary test database.
assert engine.url.get_backend_name() == "sqlite" and "email_assistant_test" in (
    engine.url.database or ""
), "Refusing to run tests against a real database"


@pytest.fixture(autouse=True)
def fresh_database():
    """Every test starts with empty tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session", autouse=True)
def remove_test_database_file():
    yield
    engine.dispose()
    _TEST_DB.unlink(missing_ok=True)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """A pretend browser that talks to the app."""
    return TestClient(app)


@pytest.fixture()
def make_user(db):
    def _make(email="user@example.com"):
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture()
def make_email(db):
    def _make(user, **fields):
        data = {
            "gmail_id": uuid.uuid4().hex,
            "thread_id": "thread",
            "subject": "Hello",
            "sender": "friend@example.com",
            "snippet": "",
            "body": "Hi there",
            "category": "Work",
            "summary": "A short summary",
            "has_action_item": False,
        }
        data.update(fields)
        email = Email(user_id=user.id, **data)
        db.add(email)
        db.commit()
        db.refresh(email)
        return email

    return _make


@pytest.fixture()
def login(client):
    """Makes the pretend browser logged in as the given user."""

    def _login(user):
        client.cookies.set("session", create_session_token(user.id))

    return _login