"""Shared pytest fixtures for the BankOS API."""

# Standard library
import os

# Configure the environment before importing any application module.
os.environ["DATABASE_URL"] = "sqlite:///./data/test_bankos.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-enough-entropy"
os.environ["RATE_LIMIT_AUTH_PER_MINUTE"] = "1000"
os.environ["RATE_LIMIT_FINANCIAL_PER_MINUTE"] = "1000"
os.environ["RATE_LIMIT_IP_PER_MINUTE"] = "10000"

# Third-party
import pytest
from fastapi.testclient import TestClient

# Project imports
from app.db.session import engine
from app.main import app
from app.models import Base


@pytest.fixture()
def client() -> TestClient:
    """Return a client backed by a freshly created database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
