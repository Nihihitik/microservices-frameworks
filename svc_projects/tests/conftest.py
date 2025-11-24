from collections.abc import Generator
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

try:
    from svc_projects.db.database import get_db  # type: ignore
    from svc_projects.main import app  # type: ignore
    from svc_projects.models.projects import Base  # type: ignore
    from svc_projects.api import deps as project_deps  # type: ignore
except ModuleNotFoundError:
    from db.database import get_db
    from main import app
    from models.projects import Base
    from api import deps as project_deps

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_svc_projects.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a clean SQLite session for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session):
    """FastAPI test client with DB dependency overridden."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Ensure per-test dependency overrides are reset."""
    yield
    app.dependency_overrides.pop(project_deps.get_current_user_from_token, None)
