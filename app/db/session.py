"""Database engine and session management."""

# Standard library
from collections.abc import Iterator
from pathlib import Path

# Third-party
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Project imports
from app.core.config import get_settings

settings = get_settings()

_connect_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    if ":///" in settings.database_url:
        database_path = settings.database_url.split(":///", 1)[1]
        if database_path and database_path != ":memory:":
            Path(database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)

engine: Engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: object, connection_record: object) -> None:
    """Turn on foreign key enforcement on every SQLite connection."""
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db() -> Iterator[Session]:
    """Yield a database session and close it after the request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_schema(target_engine: Engine | None = None) -> None:
    """Create every table that does not exist yet."""
    # Project imports
    from app.models import Base

    Base.metadata.create_all(bind=target_engine or engine)
