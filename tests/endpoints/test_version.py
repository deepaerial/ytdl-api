import pkg_resources
from fastapi.testclient import TestClient


def test_version_endpoint(app_client: TestClient):
    """
    Test endpoint that returns information about API version.
    """
    response = app_client.get("/api/version")
    json_response = response.json()
    assert response.status_code == 200
    assert "apiVersion" in json_response
    expected_api_version = pkg_resources.get_distribution("ytdl_api").version
    assert json_response["apiVersion"] == expected_api_version
