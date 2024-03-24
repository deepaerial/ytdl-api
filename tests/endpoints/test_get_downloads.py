from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from ytdl_api.schemas.models import Download


def test_get_downloads(uid: str, app_client: TestClient, mock_persisted_download: Download):
    response = app_client.get("/api/downloads", cookies={"uid": uid})
    assert response.status_code == 200
    json_response = response.json()
    assert "downloads" in json_response
    assert len(json_response) == 1
    assert json_response["downloads"][0]["title"] == mock_persisted_download.title
    assert json_response["downloads"][0]["url"] == mock_persisted_download.url
    assert json_response["downloads"][0]["mediaId"] == mock_persisted_download.media_id
    assert "filesizeHr" in json_response["downloads"][0]
    assert (
        datetime.fromisoformat(json_response["downloads"][0]["whenSubmitted"]) == mock_persisted_download.when_submitted
    )


@pytest.mark.skip(
    "Fails in Github Actions for unknown reason due to bug https://github.com/tiangolo/fastapi/discussions/11341"
)
def test_get_downloads_no_cookie(app_client: TestClient):
    response = app_client.get("/api/downloads")
    assert response.status_code == 403
    assert response.json()["detail"] == "No cookie provided :("
