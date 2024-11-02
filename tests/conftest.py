import os
import random
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator, Iterable

import pytest
from confz import EnvSource, DataSource
from fastapi.testclient import TestClient

from ytdl_api.config import REPO_PATH, Settings
from ytdl_api.constants import DownloadStatus, MediaFormat
from ytdl_api.datasource import IDataSource, InMemoryDB
from ytdl_api.dependencies import get_settings, get_database
from ytdl_api.queue import NotificationQueue
from ytdl_api.schemas.models import Download
from ytdl_api.schemas.requests import DownloadParams
from ytdl_api.storage import LocalFileStorage
from ytdl_api.utils import get_unique_id

from .utils import EXAMPLE_VIDEO_PREVIEW, get_example_download_instance


@pytest.fixture()
def uid() -> str:
    return get_unique_id()


@pytest.fixture
def temp_directory():
    tmp = TemporaryDirectory()
    yield tmp
    tmp.cleanup()


@pytest.fixture
def fake_media_path(temp_directory: TemporaryDirectory) -> Path:
    return Path(temp_directory.name)


@pytest.fixture()
def notification_queue() -> NotificationQueue:
    return NotificationQueue()


@pytest.fixture()
def fake_local_storage(fake_media_path: Path) -> LocalFileStorage:
    return LocalFileStorage(fake_media_path)


@pytest.fixture()
def fake_media_file_path(fake_media_path: Path) -> Path:
    filename = get_unique_id()
    fake_media_file_path = fake_media_path / filename
    with fake_media_file_path.open("wb") as f:
        file_size_in_bytes = 1024
        f.write(os.urandom(file_size_in_bytes))
    return fake_media_file_path


@pytest.fixture()
def settings(fake_media_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterable[Settings]:
    data_source = DataSource(
        data={
            "debug": True,
            "allow_origins": ["*"],
            "downloader": "mock",
            "datasource": {"use_in_memory_db": True},
            "storage": {"path": fake_media_path},
            "disable_docs": True,
        }
    )
    with Settings.change_config_sources(data_source):
        yield Settings()  # type: ignore


@pytest.fixture()
def datasource() -> InMemoryDB:
    return InMemoryDB()


@pytest.fixture
def app_client(settings: Settings, datasource: InMemoryDB) -> TestClient:
    app = settings.init_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_database] = lambda: datasource
    return TestClient(app)


@pytest.fixture()
def mock_download_params() -> DownloadParams:
    return DownloadParams(
        url=EXAMPLE_VIDEO_PREVIEW["url"],  # type: ignore
        video_stream_id=random.choice(EXAMPLE_VIDEO_PREVIEW["videoStreams"])["id"],  # type: ignore
        audio_stream_id=random.choice(EXAMPLE_VIDEO_PREVIEW["audioStreams"])["id"],  # type: ignore
        media_format=MediaFormat.MP4,
    )


@pytest.fixture()
def clear_datasource(datasource: IDataSource):
    yield
    datasource.clear_downloads()


@pytest.fixture()
def mock_persisted_download(uid: str, datasource: IDataSource) -> Generator[Download, None, None]:
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


@pytest.fixture()
def mocked_downloaded_media(
    uid: str, datasource: IDataSource, fake_media_file_path: Path, clear_datasource
) -> Generator[Download, None, None]:
    download = get_example_download_instance(
        client_id=uid,
        media_format=MediaFormat.MP4,
        duration=1000,
        filesize=1024,
        status=DownloadStatus.FINISHED,
        file_path=fake_media_file_path.as_posix(),
        progress=100,
    )
    datasource.put_download(download)
    yield download


@pytest.fixture()
def mocked_downloaded_media_no_file(
    uid: str, datasource: IDataSource, clear_datasource
) -> Generator[Download, None, None]:
    download = get_example_download_instance(
        client_id=uid,
        media_format=MediaFormat.MP4,
        duration=1000,
        filesize=1024,
        status=DownloadStatus.FINISHED,
        file_path=None,
        progress=100,
    )
    datasource.put_download(download)
    yield download


@pytest.fixture()
def mocked_failed_media_file(uid: str, datasource: IDataSource) -> Generator[Download, None, None]:
    download = get_example_download_instance(
        client_id=uid,
        media_format=MediaFormat.MP4,
        duration=1000,
        filesize=1024,
        status=DownloadStatus.FAILED,
        file_path=None,
        progress=100,
    )
    datasource.put_download(download)
    yield download


@pytest.fixture
def mocked_downloading_media_file(uid: str, datasource: IDataSource) -> Generator[Download, None, None]:
    download = get_example_download_instance(
        client_id=uid,
        media_format=MediaFormat.MP4,
        duration=1000,
        filesize=1024,
        status=DownloadStatus.DOWNLOADING,
        file_path=None,
        progress=100,
    )
    datasource.put_download(download)
    yield download
