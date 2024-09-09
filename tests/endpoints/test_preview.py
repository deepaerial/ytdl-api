import pytest
from fastapi.testclient import TestClient
from pytest_mock.plugin import MockerFixture

from ytdl_api.schemas.responses import VideoInfoResponse

from ..utils import EXAMPLE_VIDEO_PREVIEW


def test_get_preview(
    app_client: TestClient,
    mocker: MockerFixture,
):
    # TODO: Should probably create some mock factory for this
    get_video_info_patch = mocker.patch("ytdl_api.downloaders.PytubeDownloader.get_video_info")
    get_video_info_patch.return_value = VideoInfoResponse(
        **EXAMPLE_VIDEO_PREVIEW,
    )
    response = app_client.get("/api/preview", params={"url": EXAMPLE_VIDEO_PREVIEW["url"]})
    assert response.status_code == 200
    json_response = response.json()
    assert all(
        field in json_response
        for field in [
            "url",
            "title",
            "thumbnailUrl",
            "duration",
            "mediaFormats",
            "audioStreams",
            "videoStreams",
        ]
    )


def test_get_preview_422(app_client: TestClient):
    response = app_client.get("/api/preview", params={"url": "https://www.youcube.com/watch?v=9TJx7QTrTyo"})
    assert response.status_code == 422
    json_response = response.json()
    assert json_response["detail"][0]["msg"] == "Bad youtube video link provided."


def test_get_preview_private_video(app_client: TestClient):
    response = app_client.get("/api/preview", params={"url": "https://www.youtube.com/watch?v=mCk1ChMlqt0"})
    assert response.status_code == 403
    json_response = response.json()
    assert "is a private video" in json_response["detail"]
