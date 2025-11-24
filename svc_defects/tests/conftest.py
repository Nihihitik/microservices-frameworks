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
    from svc_defects.db.database import get_db  # type: ignore
    from svc_defects.main import app  # type: ignore
    from svc_defects.models.defects import Base  # type: ignore
    import svc_defects.models.comments  # noqa: F401
    import svc_defects.models.attachments  # noqa: F401
    import svc_defects.models.defect_history  # noqa: F401
    from svc_defects.api import deps as defects_deps  # type: ignore
except ModuleNotFoundError:
    from db.database import get_db
    from main import app
    from models.defects import Base
    import models.comments  # noqa: F401
    import models.attachments  # noqa: F401
    import models.defect_history  # noqa: F401
    from api import deps as defects_deps

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_svc_defects.db"
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
    """Ensure dependency overrides do not leak between tests."""
    yield
    app.dependency_overrides.pop(defects_deps.get_current_user_from_token, None)
