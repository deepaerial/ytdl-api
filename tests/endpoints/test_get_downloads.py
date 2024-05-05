from datetime import datetime

from fastapi.testclient import TestClient

from ytdl_api.schemas.models import Download


def test_get_downloads(uid: str, app_client: TestClient, mock_persisted_download: Download):
    response = app_client.get("/api/downloads", cookies={"uid": uid})
    assert response.status_code == 200
    json_response = response.json()
    assert "downloads" in json_response
    assert len(json_response) == 1
    download = json_response["downloads"][0]
    assert download["title"] == mock_persisted_download.title
    assert download["url"] == mock_persisted_download.url
    assert download["mediaId"] == mock_persisted_download.media_id
    assert "filesizeHr" in download
    assert datetime.fromisoformat(download["whenSubmitted"]) == mock_persisted_download.when_submitted
