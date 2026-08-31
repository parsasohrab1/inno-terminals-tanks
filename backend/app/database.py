"""Database engine + session management (SQLModel / SQLAlchemy)."""
from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=_connect_args,
    pool_pre_ping=True,
)


def init_db() -> None:
    """Create tables. In production this is replaced by Alembic migrations."""
    import app.models  # noqa: F401  (register metadata)

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
