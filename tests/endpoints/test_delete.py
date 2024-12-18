from fastapi.testclient import TestClient

from ytdl_api.datasource import IDataSource
from ytdl_api.schemas.models import Download


def test_delete_non_existing_download(app_client: TestClient):
    app_client.cookies = {"uid": "-1"}
    response = app_client.delete("/api/delete", params={"mediaId": -1})
    assert response.status_code == 404
    assert response.json()["detail"] == "Download not found"


def test_delete_existing_unfinished_download(app_client: TestClient, mock_persisted_download: Download):
    app_client.cookies = {"uid": mock_persisted_download.client_id}
    response = app_client.delete(
        "/api/delete",
        params={
            "mediaId": mock_persisted_download.media_id,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Media file is not downloaded yet"


def test_delete_existing_downloaded_file(
    app_client: TestClient, mocked_downloaded_media: Download, datasource: IDataSource
):
    app_client.cookies = {"uid": mocked_downloaded_media.client_id}
    response = app_client.delete(
        "/api/delete",
        params={"mediaId": mocked_downloaded_media.media_id},
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "mediaId" in json_response
    assert json_response["mediaId"] == mocked_downloaded_media.media_id
    assert "status" in json_response
    assert json_response["status"] == "deleted"
    download = datasource.get_download(mocked_downloaded_media.client_id, mocked_downloaded_media.media_id)
    assert download is None


def test_delete_failed_to_download_media(
    app_client: TestClient, mocked_failed_media_file: Download, datasource: IDataSource
):
    """
    Test if app allows to remove media download that resulted in error during download.
    """
    app_client.cookies = {"uid": mocked_failed_media_file.client_id}
    response = app_client.delete(
        "/api/delete",
        params={"mediaId": mocked_failed_media_file.media_id},
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "mediaId" in json_response
    assert json_response["mediaId"] == mocked_failed_media_file.media_id
    assert "status" in json_response
    assert json_response["status"] == "deleted"
    download = datasource.get_download(mocked_failed_media_file.client_id, mocked_failed_media_file.media_id)
    assert download is None
