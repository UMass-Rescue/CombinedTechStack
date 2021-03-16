from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)
