import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("INNO_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")


@pytest.fixture(name="engine")
def engine_fixture():
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    eng = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    import app.database as db

    db.engine = eng
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()
    try:
        os.unlink(path)
    except (PermissionError, FileNotFoundError):
        pass


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture(name="seeded")
def seeded_fixture(engine, session):
    from app.seed import seed_operations, seed_tanks, seed_users

    seed_users(session)
    tanks = seed_tanks(session, n=6)
    seed_operations(session, tanks)
    return tanks


@pytest.fixture(name="client")
def client_fixture(engine, seeded):
    from app.database import get_session
    from app.main import app

    def _get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth_header(client, username="opsmanager", password="demo1234"):
    r = client.post("/api/v1/auth/login-json", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
