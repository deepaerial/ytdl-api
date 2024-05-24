import inspect
from pathlib import Path
from typing import Generator

import pytest
from confz import EnvSource

from ytdl_api.config import REPO_PATH, Settings
from ytdl_api.constants import DownloadStatus, MediaFormat
from ytdl_api.schemas.models import Download
from ytdl_api.storage import DetaDriveStorage
from ytdl_api.utils import get_datetime_now

from ..utils import get_example_download_instance


@pytest.fixture()
def mocked_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Settings, None, None]:
    # ignoring datasource config as in this test it's not needed
    monkeypatch.setenv("DATASOURCE__DETA_KEY", "*****")
    monkeypatch.setenv("DATASOURCE__DETA_BASE", "*****")
    data_source = EnvSource(
        allow_all=True,
        deny=["title", "description", "version"],
        file=(REPO_PATH / ".env.test").resolve(),
        nested_separator="__",
    )
    with Settings.change_config_sources(data_source):
        yield Settings()  # type: ignore


@pytest.fixture()
def deta_storage(mocked_settings: Settings) -> DetaDriveStorage:
    return mocked_settings.storage.get_storage()


@pytest.fixture()
def clear_drive(fake_media_file_path: Path, deta_storage: DetaDriveStorage):
    deta_storage.drive.delete(fake_media_file_path.name)


@pytest.fixture()
def example_download() -> Download:
    return get_example_download_instance(
        client_id="xxxxxxx",
        media_format=MediaFormat.MP4,
        filesize=1024,
        status=DownloadStatus.FINISHED,
        progress=0,
        when_started_download=get_datetime_now(),
    )


def test_deta_storage(
    deta_storage: DetaDriveStorage,
    example_download: Download,
    fake_media_file_path: Path,
    clear_drive: None,
):
    storage_file_name = deta_storage.save_download_from_file(example_download, fake_media_file_path)
    assert storage_file_name is not None
    file_bytes = deta_storage.get_download(storage_file_name)
    assert inspect.isgenerator(file_bytes)
    deta_storage.remove_download(storage_file_name)
    file_bytes = deta_storage.get_download(storage_file_name)
    assert file_bytes is None


def test_deta_storage_delete_many(
    deta_storage: DetaDriveStorage,
    example_download: Download,
    fake_media_file_path: Path,
    clear_drive: None,
):
    storage_file_name = deta_storage.save_download_from_file(example_download, fake_media_file_path)
    assert storage_file_name is not None
    deta_storage.remove_download_batch([storage_file_name])
    no_bytes = deta_storage.get_download(storage_file_name)
    assert no_bytes is None
