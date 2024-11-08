import asyncio
import inspect
from datetime import datetime

import ffmpeg
import pytest

from ytdl_api.constants import DownloadStatus
from ytdl_api.datasource import InMemoryDB
from ytdl_api.dependencies import get_pytube_downloader
from ytdl_api.downloaders import PytubeDownloader
from ytdl_api.queue import NotificationQueue
from ytdl_api.schemas.models import Download, DownloadStatusInfo
from ytdl_api.storage import LocalFileStorage


@pytest.fixture()
def downloader(
    datasource: InMemoryDB,
    notification_queue: NotificationQueue,
    fake_local_storage: LocalFileStorage,
) -> PytubeDownloader:
    return get_pytube_downloader(datasource, notification_queue, fake_local_storage)


@pytest.mark.skip(
    reason="Pytube download is not working. Error raised for this test: urllib.error.HTTPError: HTTP Error 400: Bad Request"
)
def test_video_download(
    downloader: PytubeDownloader,
    mock_persisted_download: Download,
    local_storage: LocalFileStorage,
    datasource: InMemoryDB,
):
    """
    Test video download.
    """
    mock_persisted_download.audio_stream_id = "251"
    mock_persisted_download.video_stream_id = "278"
    assert mock_persisted_download.status == DownloadStatus.STARTED
    assert mock_persisted_download.file_path is None
    assert mock_persisted_download.when_started_download is None
    assert mock_persisted_download.when_download_finished is None
    downloader.download(mock_persisted_download)
    finished_download = datasource.get_download(mock_persisted_download.client_id, mock_persisted_download.media_id)
    assert finished_download.status == DownloadStatus.FINISHED
    assert isinstance(finished_download.when_download_finished, datetime)
    assert finished_download.file_path is not None
    assert finished_download.audio_stream_id == "251"
    assert finished_download.video_stream_id == "278"
    downloaded_file_bytes = local_storage.get_download(finished_download.file_path)
    assert inspect.isgenerator(downloaded_file_bytes)


def _raise_ffmpeg_error(*args, **kwargs):
    raise ffmpeg.Error("Error!", "xxxxx", "xxxxx")


def test_video_download_ffmpeg_failed(
    downloader: PytubeDownloader,
    mock_persisted_download: Download,
    datasource: InMemoryDB,
    notification_queue: NotificationQueue,
):
    """
    Test code behaviour when ffmpeg failed.
    """
    # mocking _merge_streams method for PytubeDownloader soi it will raise error
    downloader._merge_streams = _raise_ffmpeg_error
    downloader.download(mock_persisted_download)
    failed_download = datasource.get_download(mock_persisted_download.client_id, mock_persisted_download.media_id)
    assert failed_download.status == DownloadStatus.FAILED
    assert isinstance(failed_download.when_failed, datetime)
    # bad looking loop, but I did not know a better way to get last event
    # from asyncio.Queue which should contain status = 'failed'
    event = None
    while True:
        try:
            event = notification_queue.queues[mock_persisted_download.client_id].get_nowait()
        except asyncio.QueueEmpty:
            assert isinstance(event, DownloadStatusInfo)
            assert event.status == DownloadStatus.FAILED
            assert event.client_id == mock_persisted_download.client_id
            assert event.media_id == mock_persisted_download.media_id
            # in order to break while True loop when needed event was found & tested
            break
