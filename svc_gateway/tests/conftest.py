from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

try:
    from svc_gateway.app.main import app  # type: ignore
except ModuleNotFoundError:
    from app.main import app


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as test_client:
        yield test_client
