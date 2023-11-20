import asyncio
import secrets
import tempfile
from functools import lru_cache, partial
from pathlib import Path
from typing import Generator, Optional

from fastapi import Cookie, Depends, HTTPException, Response, Query
from starlette import status

from . import datasource, downloaders, queue, storage
from .callbacks import (
    on_download_start_callback,
    on_error_callback,
    on_finish_callback,
    on_pytube_progress_callback,
    on_start_converting,
    on_ytdlp_progress_callback,
)
from .config import Settings
from .constants import DownloadStatus, DownloaderType
from .schemas.models import Download
from .utils import LOGGER


# Ignoring get_settings dependency in coverage because it will be
# overridden in unittests.
@lru_cache
def get_settings() -> Settings:  # pragma: no cover
    return Settings()  # type: ignore


@lru_cache
def get_notification_queue() -> queue.NotificationQueue:
    return queue.NotificationQueue()


def get_database(settings: Settings = Depends(get_settings)) -> datasource.IDataSource:
    return settings.datasource.get_datasource()


def get_storage(settings: Settings = Depends(get_settings)) -> storage.IStorage:
    return settings.storage.get_storage()


def get_ytdlp_downloader(
    datasource: datasource.IDataSource,
    event_queue: queue.NotificationQueue,
    storage: storage.IStorage,
):
    on_download_started_hook = asyncio.coroutine(
        partial(on_download_start_callback, datasource=datasource, queue=event_queue)
    )
    on_progress_hook = asyncio.coroutine(
        partial(on_ytdlp_progress_callback, datasource=datasource, queue=event_queue)
    )
    on_finish_hook = asyncio.coroutine(
        partial(
            on_finish_callback,
            datasource=datasource,
            queue=event_queue,
            storage=storage,
            logger=LOGGER,
        )
    )
    on_error_hook = asyncio.coroutine(
        partial(
            on_error_callback,
            datasource=datasource,
            queue=event_queue,
            logger=LOGGER,
        )
    )
    return downloaders.YTDLPDownloader(
        on_download_started_callback=on_download_started_hook,
        on_progress_callback=on_progress_hook,
        on_finish_callback=on_finish_hook,
        on_error_callback=on_error_hook,
    )


def get_downloader(
    settings: Settings = Depends(get_settings),
    datasource: datasource.IDataSource = Depends(get_database),
    event_queue: queue.NotificationQueue = Depends(get_notification_queue),
    storage: storage.IStorage = Depends(get_storage),
) -> downloaders.IDownloader:
    if settings.downloader == DownloaderType.YTDLP:
        return get_ytdlp_downloader(datasource, event_queue, storage)
    on_download_started_hook = asyncio.coroutine(
        partial(on_download_start_callback, datasource=datasource, queue=event_queue)
    )
    on_progress_hook = asyncio.coroutine(
        partial(on_pytube_progress_callback, datasource=datasource, queue=event_queue)
    )
    on_converting_hook = asyncio.coroutine(
        partial(on_start_converting, datasource=datasource, queue=event_queue)
    )
    on_finish_hook = asyncio.coroutine(
        partial(
            on_finish_callback,
            datasource=datasource,
            queue=event_queue,
            storage=storage,
        )
    )
    on_error_hook = asyncio.coroutine(
        partial(
            on_error_callback,
            datasource=datasource,
            queue=event_queue,
            logger=LOGGER,
        )
    )
    return downloaders.PytubeDownloader(
        on_download_started_callback=on_download_started_hook,
        on_progress_callback=on_progress_hook,
        on_converting_callback=on_converting_hook,
        on_finish_callback=on_finish_hook,
        on_error_callback=on_error_hook,
    )


def get_uid_dependency_factory(raise_error_on_empty: bool = False):
    """
    Factory function fore returning dependency that fetches client ID.
    """

    def get_uid(
        response: Response,
        uid: Optional[str] = Cookie(None),
        settings: Settings = Depends(get_settings),
    ):
        """
        Dependency for fetchng user ID from cookie or setting it in cookie if absent.
        """
        if uid is None and raise_error_on_empty:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No cookie provided :("
            )
        elif uid is None and not raise_error_on_empty:
            uid = secrets.token_hex(16)
            response.set_cookie(
                key="uid",
                value=uid,
                samesite=settings.cookie_samesite,
                secure=settings.cookie_secure,
                httponly=settings.cookie_httponly,
            )
        return uid

    return get_uid


def get_download_file(
    media_id: str = Query(..., alias="mediaId", description="Download id"),
    uid: str = Depends(get_uid_dependency_factory(raise_error_on_empty=True)),
    datasource: datasource.IDataSource = Depends(get_database),
    storage: storage.IStorage = Depends(get_storage),
) -> Generator[tuple[Download, Path], None, None]:
    media_file = datasource.get_download(uid, media_id)
    if media_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Download not found"
        )
    if media_file.status not in (DownloadStatus.FINISHED, DownloadStatus.DOWNLOADED):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not downloaded yet"
        )
    if media_file.file_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download is finished but file not found",
        )
    download_bytes = storage.get_download(media_file.file_path)
    if download_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download is finished but file not found",
        )
    with tempfile.NamedTemporaryFile() as download_file:
        download_file.write(download_bytes)
        download_file.seek(0)
        yield media_file, Path(download_file.name)
