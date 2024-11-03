from fastapi.testclient import TestClient
from pytest_mock.plugin import MockerFixture

from ytdl_api.schemas.models import Download


def test_retry_failed_download(
    uid: str, app_client: TestClient, mocked_failed_media_file: Download, mocker: MockerFixture
):
    """
    Test if failed download can be retried.
    """
    # Mocking BackgroundTasks because we don't actually want to start process of downloading video
    mocker.patch("ytdl_api.endpoints.BackgroundTasks.add_task")
    response = app_client.put(
        "/api/retry",
        cookies={"uid": uid},
        params={"mediaId": mocked_failed_media_file.media_id},
    )
    assert response.status_code == 200


def test_retry_downloading_download(uid: str, app_client: TestClient, mocked_downloading_media_file: Download):
    """
    Test if downloading media cannot be retried.
    """
    response = app_client.put(
        "/api/retry",
        cookies={"uid": uid},
        params={"mediaId": mocked_downloading_media_file.media_id},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Download cannot be retried"


def test_retry_finished_download(uid: str, app_client: TestClient, mocked_downloaded_media_no_file: Download):
    """
    Test if finished media cannot be retried.
    """
    response = app_client.put(
        "/api/retry",
        cookies={"uid": uid},
        params={"mediaId": mocked_downloaded_media_no_file.media_id},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Download cannot be retried"


def test_retry_started_download(
    uid: str, app_client: TestClient, mock_persisted_download: Download, mocker: MockerFixture
):
    """
    Test if started media can be retried.
    """
    # Mocking BackgroundTasks because we don't actually want to start process of downloading video
    mocker.patch("ytdl_api.endpoints.BackgroundTasks.add_task")
    response = app_client.put(
        "/api/retry",
        cookies={"uid": uid},
        params={"mediaId": mock_persisted_download.media_id},
    )
    assert response.status_code == 200
