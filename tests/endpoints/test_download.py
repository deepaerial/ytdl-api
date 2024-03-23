from fastapi.testclient import TestClient
from pytest_mock.plugin import MockerFixture

from ytdl_api.datasource import IDataSource
from ytdl_api.schemas.models import Download
from ytdl_api.schemas.requests import DownloadParams


def test_submit_download(
    app_client: TestClient,
    uid: str,
    mock_download_params: DownloadParams,
    mocker: MockerFixture,
    clear_datasource: None,
):
    # Mocking BackgroundTasks because we don't actually want to start process of downloading video
    mocker.patch("ytdl_api.endpoints.BackgroundTasks.add_task")
    response = app_client.put("/api/download", cookies={"uid": uid}, json=mock_download_params.dict())
    assert response.status_code == 201
    json_response = response.json()
    assert "downloads" in json_response
    download = next(
        (download for download in json_response["downloads"] if download["url"] == mock_download_params.url),
        None,
    )
    assert download is not None
    assert download["whenSubmitted"] is not None
    assert (
        download["whenStartedDownload"] is None
    )  # download process will probably not start right away so this field should be null
    assert download["whenDownloadFinished"] is None
    assert download["whenFileDownloaded"] is None
    assert download["whenDeleted"] is None


def test_download_file_endpoint(app_client: TestClient, mocked_downloaded_media: Download, datasource: IDataSource):
    response = app_client.get(
        "/api/download",
        params={
            "mediaId": mocked_downloaded_media.media_id,
        },
        cookies={"uid": mocked_downloaded_media.client_id},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    download = datasource.get_download(mocked_downloaded_media.client_id, mocked_downloaded_media.media_id)
    assert download is not None
    assert download.status == "downloaded"
    assert download.when_file_downloaded is not None


def test_download_file_but_non_exisiting_media_id(app_client: TestClient, mocked_downloaded_media: Download):
    response = app_client.get(
        "/api/download",
        params={
            "mediaId": "*****",
        },
        cookies={"uid": mocked_downloaded_media.client_id},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Download not found"


def test_download_file_but_non_existing_client_id(app_client: TestClient, mocked_downloaded_media: Download):
    response = app_client.get(
        "/api/download",
        params={"mediaId": mocked_downloaded_media.media_id},
        cookies={"uid": "******"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Download not found"


def test_download_file_but_download_not_finished(
    app_client: TestClient, mock_persisted_download: Download, datasource: IDataSource
):
    response = app_client.get(
        "/api/download",
        params={
            "mediaId": mock_persisted_download.media_id,
        },
        cookies={"uid": mock_persisted_download.client_id},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "File not downloaded yet"
    download = datasource.get_download(mock_persisted_download.client_id, mock_persisted_download.media_id)
    assert download is not None


def test_download_file_but_no_file_present(app_client: TestClient, mocked_downloaded_media_no_file: Download):
    response = app_client.get(
        "/api/download",
        params={"mediaId": mocked_downloaded_media_no_file.media_id},
        cookies={"uid": mocked_downloaded_media_no_file.client_id},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Download is finished but file not found"
