"""Health check service."""

# Third-party
from sqlalchemy import text
from sqlalchemy.orm import Session


def check_database(session: Session) -> None:
    """Raise when the database cannot answer a trivial query."""
    session.execute(text("SELECT 1"))
