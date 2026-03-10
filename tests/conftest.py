"""
Pytest configuration and fixtures for integration and API tests.

Uses in-memory SQLite. Tables are recreated before each test that needs them.
"""

import os

# Set test config before app is imported (create_app reads these)
os.environ["DATABASE_URI"] = "sqlite:///:memory:"
os.environ["OPENAI_API_KEY"] = ""  # Force mock AI (empty = falsy; load_dotenv won't override)

import pytest
from datetime import date
from decimal import Decimal

from app import create_app
from persistence.sqlite.models import db


class FakeInviteCodeGenerator:
    """Returns predictable codes for testing."""

    def __init__(self, code: str = "TESTCODE"):
        self._code = code

    def generate(self) -> str:
        return self._code


@pytest.fixture
def app():
    """Create Flask app with in-memory SQLite."""
    return create_app()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Flask test client with logged-in user. Use for routes that require auth (e.g. create trip)."""
    with app.app_context():
        from persistence.sqlite.user_repository import create_user, get_user_by_email
        from werkzeug.security import generate_password_hash
        # Create test user if not exists
        user = get_user_by_email("test@example.com")
        if not user:
            create_user("test@example.com", generate_password_hash("testpass123", method="scrypt"))
    client.post("/login", data={"email": "test@example.com", "password": "testpass123"}, follow_redirects=True)
    return client


@pytest.fixture
def app_with_fake_invite(app):
    """App with predictable invite codes. Requires patching at composition root."""
    # The app is already created with RandomInviteCodeGenerator.
    # For integration tests we create trips via API, so we get random codes.
    # We can still use the client - we'll parse invite_code from create response.
    return app


@pytest.fixture
def db_session(app):
    """Provide a clean DB for each test. Yields the app context."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()
