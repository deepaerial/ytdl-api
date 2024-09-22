import secrets
from functools import lru_cache, partial

from fastapi import Cookie, Depends, HTTPException, Response
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
from .constants import DownloaderType
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
    on_download_started_hook = partial(on_download_start_callback, datasource=datasource, queue=event_queue)
    on_progress_hook = partial(on_ytdlp_progress_callback, datasource=datasource, queue=event_queue)
    on_finish_hook = partial(
        on_finish_callback,
        datasource=datasource,
        queue=event_queue,
        storage=storage,
        logger=LOGGER,
    )
    on_error_hook = partial(
        on_error_callback,
        datasource=datasource,
        queue=event_queue,
        logger=LOGGER,
    )
    return downloaders.YTDLPDownloader(
        on_download_started_callback=on_download_started_hook,
        on_progress_callback=on_progress_hook,
        on_finish_callback=on_finish_hook,
        on_error_callback=on_error_hook,
    )


def get_pytube_downloader(
    datasource: datasource.IDataSource,
    event_queue: queue.NotificationQueue,
    storage: storage.IStorage,
):
    on_download_started_hook = partial(on_download_start_callback, datasource=datasource, queue=event_queue)
    on_progress_hook = partial(on_pytube_progress_callback, datasource=datasource, queue=event_queue)
    on_converting_hook = partial(on_start_converting, datasource=datasource, queue=event_queue)
    on_finish_hook = partial(
        on_finish_callback,
        datasource=datasource,
        queue=event_queue,
        storage=storage,
        logger=LOGGER,
    )
    on_error_hook = partial(
        on_error_callback,
        datasource=datasource,
        queue=event_queue,
        logger=LOGGER,
    )
    return downloaders.PytubeDownloader(
        on_download_started_callback=on_download_started_hook,
        on_progress_callback=on_progress_hook,
        on_converting_callback=on_converting_hook,
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
    return get_pytube_downloader(datasource, event_queue, storage)


def get_uid_dependency_factory(raise_error_on_empty: bool = False):
    """
    Factory function fore returning dependency that fetches client ID.
    """

    def get_uid(
        response: Response,
        uid: str | None = Cookie(None),
        settings: Settings = Depends(get_settings),
    ):
        """
        Dependency for fetchng user ID from cookie or setting it in cookie if absent.
        """
        if uid is None and raise_error_on_empty:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No cookie provided :(")
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
