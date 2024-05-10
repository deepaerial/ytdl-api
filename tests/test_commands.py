import logging
from datetime import timedelta
from unittest.mock import Mock

import pytest

from ytdl_api.commands import hard_remove_downloads
from ytdl_api.datasource import IDataSource
from ytdl_api.schemas.models import Download
from ytdl_api.utils import get_datetime_now

from .utils import get_example_download_instance


@pytest.fixture
def mocked_logger():
    mocked_logger = Mock(spec=logging.Logger)
    mocked_logger.info.return_value = None  # type: ignore
    mocked_logger.error.return_value = None  # type: ignore
    return mocked_logger


@pytest.fixture
def example_expired_downloads(datasource: IDataSource):
    dt_now = get_datetime_now()
    expiration_delta = timedelta(days=7)
    expired_downloads = [
        get_example_download_instance(
            client_id="test",
            media_format="mp4",
            status="downloaded",
            when_submitted=dt_now - expiration_delta - timedelta(days=1),
        ),
        get_example_download_instance(
            client_id="test", media_format="mp4", status="downloaded", when_submitted=dt_now - expiration_delta
        ),
        get_example_download_instance(
            client_id="test",
            media_format="mp4",
            status="downloaded",
            when_submitted=dt_now - timedelta(days=1),
        ),
        get_example_download_instance(
            client_id="test",
            media_format="mp4",
            status="downloaded",
            when_submitted=dt_now,
        ),
    ]
    for download in expired_downloads:
        datasource.put_download(download)
    yield expiration_delta, expired_downloads
    datasource.clear_downloads()


def test_hard_remove_downloads(
    fake_local_storage, datasource, mocked_logger, example_expired_downloads: tuple[timedelta, list[Download]]
):
    expiration_delta, downloads = example_expired_downloads
    client_id = downloads[0].client_id

    assert len(datasource.fetch_downloads_by_client_id(client_id)) == len(downloads)

    # Call the function
    hard_remove_downloads(fake_local_storage, datasource, expiration_delta, mocked_logger)

    mocked_logger.info.assert_called_with("Soft deleted expired downloads from database.")

    assert len(datasource.fetch_downloads_by_client_id(client_id)) == 2
