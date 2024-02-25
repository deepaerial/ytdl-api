import inspect
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from confz import EnvSource
from pydantic import parse_obj_as

from ytdl_api.config import REPO_PATH, Settings
from ytdl_api.constants import DownloadStatus, MediaFormat
from ytdl_api.schemas.models import Download
from ytdl_api.storage import DetaDriveStorage


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


EXAMPLE_VIDEO_PREVIEW = {
    "url": "https://www.youtube.com/watch?v=NcBjx_eyvxc",
    "title": "Madeira | Cinematic FPV",
    "duration": 224,
    "thumbnailUrl": "https://i.ytimg.com/vi/NcBjx_eyvxc/sddefault.jpg",
    "audioStreams": [
        {"id": "251", "mimetype": "audio/webm", "bitrate": "160kbps"},
        {"id": "250", "mimetype": "audio/webm", "bitrate": "70kbps"},
        {"id": "249", "mimetype": "audio/webm", "bitrate": "50kbps"},
        {"id": "140", "mimetype": "audio/mp4", "bitrate": "128kbps"},
        {"id": "139", "mimetype": "audio/mp4", "bitrate": "48kbps"},
    ],
    "videoStreams": [
        {"id": "394", "mimetype": "video/mp4", "resolution": "144p"},
        {"id": "278", "mimetype": "video/webm", "resolution": "144p"},
        {"id": "160", "mimetype": "video/mp4", "resolution": "144p"},
        {"id": "395", "mimetype": "video/mp4", "resolution": "240p"},
        {"id": "242", "mimetype": "video/webm", "resolution": "240p"},
        {"id": "133", "mimetype": "video/mp4", "resolution": "240p"},
        {"id": "396", "mimetype": "video/mp4", "resolution": "360p"},
        {"id": "243", "mimetype": "video/webm", "resolution": "360p"},
        {"id": "134", "mimetype": "video/mp4", "resolution": "360p"},
        {"id": "397", "mimetype": "video/mp4", "resolution": "480p"},
        {"id": "244", "mimetype": "video/webm", "resolution": "480p"},
        {"id": "135", "mimetype": "video/mp4", "resolution": "480p"},
        {"id": "398", "mimetype": "video/mp4", "resolution": "720p"},
        {"id": "247", "mimetype": "video/webm", "resolution": "720p"},
        {"id": "136", "mimetype": "video/mp4", "resolution": "720p"},
        {"id": "399", "mimetype": "video/mp4", "resolution": "1080p"},
        {"id": "248", "mimetype": "video/webm", "resolution": "1080p"},
        {"id": "137", "mimetype": "video/mp4", "resolution": "1080p"},
        {"id": "400", "mimetype": "video/mp4", "resolution": "1440p"},
        {"id": "271", "mimetype": "video/webm", "resolution": "1440p"},
        {"id": "401", "mimetype": "video/mp4", "resolution": "2160p"},
        {"id": "313", "mimetype": "video/webm", "resolution": "2160p"},
    ],
    "mediaFormats": ["mp4", "mp3", "wav"],
}


@pytest.fixture()
def example_download() -> Download:
    download_data = {
        **EXAMPLE_VIDEO_PREVIEW,
        "client_id": "xxxxxxx",
        "media_format": MediaFormat.MP4,
        "filesize": 1024,
        "status": DownloadStatus.FINISHED,
        "progress": 0,
        "when_started_download": datetime.utcnow(),
    }
    download = parse_obj_as(Download, download_data)
    return download


def test_deta_storage(
    deta_storage: DetaDriveStorage,
    example_download: Download,
    fake_media_file_path: Path,
    clear_drive: None,
):
    storage_file_name = deta_storage.save_download_from_file(
        example_download, fake_media_file_path
    )
    assert storage_file_name is not None
    file_bytes = deta_storage.get_download(storage_file_name)
    assert inspect.isgenerator(file_bytes)
    deta_storage.remove_download(storage_file_name)
    file_bytes = deta_storage.get_download(storage_file_name)
    assert file_bytes is None
