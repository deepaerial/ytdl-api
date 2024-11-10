import inspect

import pytest

from ytdl_api.constants import MediaFormat
from ytdl_api.datasource import IDataSource
from ytdl_api.dependencies import get_ytdlp_downloader
from ytdl_api.downloaders import YTDLPDownloader
from ytdl_api.queue import NotificationQueue
from ytdl_api.schemas.models import Download, YoutubeURL
from ytdl_api.schemas.responses import VideoInfoResponse
from ytdl_api.storage import LocalFileStorage


@pytest.fixture()
def downloader(
    datasource: IDataSource,
    notification_queue: NotificationQueue,
    fake_local_storage: LocalFileStorage,
) -> YTDLPDownloader:
    return get_ytdlp_downloader(datasource, notification_queue, fake_local_storage)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=NcBjx_eyvxc",
        "https://www.youtube.com/watch?v=TNhaISOUy6Q",
    ],
)
def test_get_video_info(url: YoutubeURL):
    """
    Test functionality responsible for fetching video info.
    """
    downloader = YTDLPDownloader()
    video_info = downloader.get_video_info(url)
    assert isinstance(video_info, VideoInfoResponse)
    assert video_info.url == url
    assert video_info.duration is not None
    assert str(video_info.thumbnail_url).startswith("https://i.ytimg.com/")
    assert video_info.title is not None
    assert isinstance(video_info.audio_streams, list)
    assert isinstance(video_info.video_streams, list)


def test_download_video(
    mock_persisted_download: Download,
    downloader: YTDLPDownloader,
    fake_local_storage: LocalFileStorage,
):
    """
    Test functionality responsible for downloading video.
    """
    succeeded = downloader.download(mock_persisted_download)
    assert succeeded is True
    file_bytes = fake_local_storage.get_download(mock_persisted_download.storage_filename)
    assert inspect.isgenerator(file_bytes)


def test_download_video_failed(
    mock_persisted_download: Download,
    downloader: YTDLPDownloader,
    fake_local_storage: LocalFileStorage,
):
    """
    Test if download fails correctly.
    """
    mock_persisted_download.url = "https://www.youtube.com/watch?v=1234567890"
    succeeded = downloader.download(mock_persisted_download)
    assert succeeded is False
    file_bytes = fake_local_storage.get_download(mock_persisted_download.storage_filename)
    assert file_bytes is None


def test_download_audio(
    mock_persisted_download: Download,
    downloader: YTDLPDownloader,
    fake_local_storage: LocalFileStorage,
):
    """
    Test if audio download works correctly.
    """
    mock_persisted_download.media_format = MediaFormat.MP3
    succeeded = downloader.download(mock_persisted_download)
    assert succeeded is True
    file_bytes = fake_local_storage.get_download(mock_persisted_download.storage_filename)
    assert file_bytes is not None
