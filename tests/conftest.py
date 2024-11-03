import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator, Iterable

import pytest
from confz import DataSource
from fastapi.testclient import TestClient

from ytdl_api.config import Settings
from ytdl_api.datasource import IDataSource, InMemoryDB
from ytdl_api.dependencies import get_database, get_downloader, get_settings
from ytdl_api.queue import NotificationQueue
from ytdl_api.schemas.models import Download
from ytdl_api.schemas.requests import DownloadParams
from ytdl_api.storage import LocalFileStorage
from ytdl_api.utils import get_unique_id

from .utils import FakeDownloader, FakerForDownloads

FIXTURES_JSON_FILE_PATH = (Path(__file__).parent / "fixtures.json").resolve()


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
def settings(fake_media_path: Path) -> Iterable[Settings]:
    data_source = DataSource(
        data={
            "debug": True,
            "allow_origins": ["*"],
            "downloader": "dummy",
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


@pytest.fixture()
def faker_for_downloads(fake_media_path: Path) -> FakerForDownloads:
    return FakerForDownloads(fake_media_path).load_from_fixtures_file(FIXTURES_JSON_FILE_PATH)


@pytest.fixture
def app_client(settings: Settings, datasource: InMemoryDB, faker_for_downloads: FakerForDownloads) -> TestClient:
    app = settings.init_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_database] = lambda: datasource
    app.dependency_overrides[get_downloader] = lambda: FakeDownloader(faker_for_downloads=faker_for_downloads)
    return TestClient(app)


@pytest.fixture()
def mock_download_params(faker_for_downloads: FakerForDownloads) -> DownloadParams:
    return faker_for_downloads.random_download_params()


@pytest.fixture()
def mock_persisted_download(
    uid: str, faker_for_downloads: FakerForDownloads, datasource: IDataSource
) -> Generator[Download, None, None]:
    download = faker_for_downloads.random_started_download(client_id=uid)
    datasource.put_download(download)
    yield download


@pytest.fixture()
def mocked_downloaded_media(
    uid: str,
    faker_for_downloads: FakerForDownloads,
    datasource: IDataSource,
) -> Generator[Download, None, None]:
    download = faker_for_downloads.random_finished_download(client_id=uid)
    datasource.put_download(download)
    yield download


@pytest.fixture()
def mocked_downloaded_media_no_file(
    uid: str,
    faker_for_downloads: FakerForDownloads,
    datasource: IDataSource,
) -> Generator[Download, None, None]:
    download = faker_for_downloads.random_finished_download(client_id=uid, make_file=False)
    datasource.put_download(download)
    yield download


@pytest.fixture()
def mocked_failed_media_file(
    uid: str,
    faker_for_downloads: FakerForDownloads,
    datasource: IDataSource,
) -> Generator[Download, None, None]:
    download = faker_for_downloads.random_failed_download(client_id=uid)
    datasource.put_download(download)
    yield download


@pytest.fixture
def mocked_downloading_media_file(
    uid: str,
    faker_for_downloads: FakerForDownloads,
    datasource: IDataSource,
) -> Generator[Download, None, None]:
    download = faker_for_downloads.random_downloading_download(client_id=uid)
    datasource.put_download(download)
    yield download
