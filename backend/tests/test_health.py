"""Тесты каркаса: health и корневой маршрут."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"]


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["app"]


def test_openapi_has_health() -> None:
    schema = app.openapi()
    assert "/health" in schema["paths"]