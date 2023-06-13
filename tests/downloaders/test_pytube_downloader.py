from datetime import datetime
from pathlib import Path

import pytest

from ytdl_api.constants import DownloadStatus
from ytdl_api.datasource import DetaDB
from ytdl_api.dependencies import get_downloader
from ytdl_api.queue import NotificationQueue
from ytdl_api.schemas.models import Download
from ytdl_api.storage import LocalFileStorage


@pytest.fixture()
def local_storage(fake_media_path: Path) -> LocalFileStorage:
    return LocalFileStorage(fake_media_path)


@pytest.fixture
def notification_queue() -> NotificationQueue:
    return NotificationQueue()


def test_video_download(
    mock_persisted_download: Download,
    local_storage: LocalFileStorage,
    datasource: DetaDB,
    notification_queue: NotificationQueue,
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
    pytube_downloader = get_downloader(datasource, notification_queue, local_storage)
    pytube_downloader.download(mock_persisted_download)
    finished_download = datasource.get_download(
        mock_persisted_download.client_id, mock_persisted_download.media_id
    )
    assert finished_download.status == DownloadStatus.FINISHED
    assert isinstance(finished_download.when_download_finished, datetime)
    assert finished_download.file_path is not None
    assert finished_download.audio_stream_id == "251"
    assert finished_download.video_stream_id == "278"
    downloaded_file_bytes = local_storage.get_download(finished_download.file_path)
    assert isinstance(downloaded_file_bytes, bytes)
