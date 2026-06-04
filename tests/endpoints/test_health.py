from fastapi.testclient import TestClient


def test_health_endpoint(app_client: TestClient):
    response = app_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
