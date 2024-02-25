import inspect
import random
from pathlib import Path
from typing import Generator

import pytest
from confz import EnvSource

from ytdl_api.config import REPO_PATH, Settings
from ytdl_api.constants import DownloadStatus, MediaFormat
from ytdl_api.datasource import IDataSource
from ytdl_api.dependencies import get_downloader
from ytdl_api.downloaders import YTDLPDownloader
from ytdl_api.queue import NotificationQueue
from ytdl_api.schemas.models import Download, YoutubeURL
from ytdl_api.schemas.responses import VideoInfoResponse
from ytdl_api.storage import LocalFileStorage

from ..utils import EXAMPLE_VIDEO_PREVIEW, get_example_download_instance


@pytest.fixture()
def settings(
    fake_media_path: Path,
    deta_testbase: str,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Settings, None, None]:
    monkeypatch.setenv("DOWNLOADER", "yt-dlp")
    monkeypatch.setenv("DATASOURCE__DETA_BASE", deta_testbase)
    monkeypatch.setenv("STORAGE__PATH", fake_media_path.as_posix())
    data_source = EnvSource(
        allow_all=True,
        deny=["title", "description", "version"],
        file=(REPO_PATH / ".env.test").resolve(),
        nested_separator="__",
    )
    with Settings.change_config_sources(data_source):
        yield Settings()  # type: ignore


@pytest.fixture()
def mock_persisted_download(
    uid: str, datasource: IDataSource
) -> Generator[Download, None, None]:
    download = get_example_download_instance(
        client_id=uid,
        media_format=MediaFormat.MP4,
        status=DownloadStatus.STARTED,
        when_started_download=None,
    )
    download.audio_stream_id = random.choice(EXAMPLE_VIDEO_PREVIEW["audioStreams"])["id"]  # type: ignore
    download.video_stream_id = random.choice(EXAMPLE_VIDEO_PREVIEW["videoStreams"])["id"]  # type: ignore
    datasource.put_download(download)
    yield download


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
    assert video_info.thumbnail_url.startswith("https://i.ytimg.com/")
    assert video_info.title is not None
    assert isinstance(video_info.audio_streams, list)
    assert isinstance(video_info.video_streams, list)


def test_download_video(
    settings: Settings,
    mock_persisted_download: Download,
    notification_queue: NotificationQueue,
    fake_local_storage: LocalFileStorage,
    datasource: IDataSource,
):
    """
    Test functionality responsible for downloading video.
    """
    downloader = get_downloader(
        settings, datasource, notification_queue, fake_local_storage
    )
    succeeded = downloader.download(mock_persisted_download)
    assert succeeded is True
    file_bytes = fake_local_storage.get_download(
        mock_persisted_download.storage_filename
    )
    assert inspect.isgenerator(file_bytes)


def test_download_video_failed(
    settings: Settings,
    mock_persisted_download: Download,
    notification_queue: NotificationQueue,
    fake_local_storage: LocalFileStorage,
    datasource: IDataSource,
):
    """
    Test if download fails correctly.
    """
    mock_persisted_download.url = "https://www.youtube.com/watch?v=1234567890"
    downloader = get_downloader(
        settings, datasource, notification_queue, fake_local_storage
    )
    succeeded = downloader.download(mock_persisted_download)
    assert succeeded is False
    file_bytes = fake_local_storage.get_download(
        mock_persisted_download.storage_filename
    )
    assert file_bytes is None


def test_download_audio(
    settings: Settings,
    mock_persisted_download: Download,
    notification_queue: NotificationQueue,
    fake_local_storage: LocalFileStorage,
    datasource: IDataSource,
):
    """
    Test if audio download works correctly.
    """
    mock_persisted_download.media_format = MediaFormat.MP3
    downloader = get_downloader(
        settings, datasource, notification_queue, fake_local_storage
    )
    succeeded = downloader.download(mock_persisted_download)
    assert succeeded is True
    file_bytes = fake_local_storage.get_download(
        mock_persisted_download.storage_filename
    )
    assert file_bytes is not None
