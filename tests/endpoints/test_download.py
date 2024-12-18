from fastapi.testclient import TestClient
from pytest_mock.plugin import MockerFixture

from ytdl_api.datasource import IDataSource
from ytdl_api.schemas.models import Download
from ytdl_api.schemas.requests import DownloadParams


def test_submit_download(app_client: TestClient, uid: str, mock_download_params: DownloadParams, mocker: MockerFixture):
    app_client.cookies = {"uid": uid}
    # Mocking BackgroundTasks because we don't actually want to start process of downloading video
    mocker.patch("ytdl_api.endpoints.BackgroundTasks.add_task")
    response = app_client.put("/api/download", json=mock_download_params.model_dump())
    assert response.status_code == 201
    json_response = response.json()
    assert json_response.get("mediaId") is not None
    assert json_response.get("whenSubmitted") is not None


def test_download_file_endpoint(app_client: TestClient, mocked_downloaded_media: Download, datasource: IDataSource):
    app_client.cookies = {"uid": mocked_downloaded_media.client_id}
    response = app_client.get(
        "/api/download",
        params={
            "mediaId": mocked_downloaded_media.media_id,
        },
    )
    assert response.status_code == 200
    download = datasource.get_download(mocked_downloaded_media.client_id, mocked_downloaded_media.media_id)
    assert download is not None
    assert download.status == "downloaded"
    assert download.when_file_downloaded is not None


def test_download_file_but_non_exisiting_media_id(app_client: TestClient, mocked_downloaded_media: Download):
    app_client.cookies = {"uid": mocked_downloaded_media.client_id}
    response = app_client.get(
        "/api/download",
        params={
            "mediaId": "*****",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Download not found"


def test_download_file_but_non_existing_client_id(app_client: TestClient, mocked_downloaded_media: Download):
    app_client.cookies = {"uid": "******"}
    response = app_client.get(
        "/api/download",
        params={"mediaId": mocked_downloaded_media.media_id},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Download not found"


def test_download_file_but_download_not_finished(
    app_client: TestClient, mock_persisted_download: Download, datasource: IDataSource
):
    app_client.cookies = {"uid": mock_persisted_download.client_id}
    response = app_client.get(
        "/api/download",
        params={
            "mediaId": mock_persisted_download.media_id,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "File not downloaded yet"
    download = datasource.get_download(mock_persisted_download.client_id, mock_persisted_download.media_id)
    assert download is not None


def test_download_file_but_no_file_present(app_client: TestClient, mocked_downloaded_media_no_file: Download):
    app_client.cookies = {"uid": mocked_downloaded_media_no_file.client_id}
    response = app_client.get(
        "/api/download",
        params={"mediaId": mocked_downloaded_media_no_file.media_id},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Download is finished but file not found"
