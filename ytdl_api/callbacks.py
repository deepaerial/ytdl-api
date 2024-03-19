from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Callable, Coroutine

import ffmpeg

from .constants import DownloadStatus
from .datasource import IDataSource
from .queue import NotificationQueue
from .schemas.models import Download, DownloadStatusInfo
from .storage import IStorage
from .types import DownloadDataInfo
from .utils import extract_percentage_progress, get_file_size


async def noop_callback(*args, **kwargs):  # pragma: no cover
    """
    Empty on downaload progess callback. Use as default/placeholder callback for
    - on start downaload event
    - on download progress event
    - on start converting event
    - on download finish event
    """
    pass


async def on_download_start_callback(
    download: Download,
    datasource: IDataSource,
    queue: NotificationQueue,
):
    download.status = DownloadStatus.DOWNLOADING
    download.when_started_download = datetime.utcnow()
    datasource.update_download(download)
    await queue.put(
        download.client_id,
        DownloadStatusInfo(
            title=download.title,
            client_id=download.client_id,
            media_id=download.media_id,
            status=DownloadStatus.DOWNLOADING,
            progress=0,
        ),
    )


async def on_pytube_progress_callback(
    download: Download,
    datasource: IDataSource,
    queue: NotificationQueue,
    *args,
    **kwargs,
):
    """
    Callback which will be used in Pytube's progress update callback
    """
    download_proress = DownloadStatusInfo(
        title=download.title,
        client_id=download.client_id,
        media_id=download.media_id,
        status=DownloadStatus.DOWNLOADING,
        progress=-1,
    )
    datasource.update_download_progress(download_proress)
    return await queue.put(download.client_id, download_proress)


async def on_ytdlp_progress_callback(progress: DownloadDataInfo, **kwargs):
    """
    Callback which will be used in Pytube's progress update callback
    """
    download: Download = kwargs["download"]
    datasource: IDataSource = kwargs["datasource"]
    queue: NotificationQueue = kwargs["queue"]
    progress = extract_percentage_progress(progress.get("_percent_str"))
    download_proress = DownloadStatusInfo(
        title=download.title,
        client_id=download.client_id,
        media_id=download.media_id,
        status=DownloadStatus.DOWNLOADING,
        progress=progress,
    )
    datasource.update_download_progress(download_proress)
    return await queue.put(download.client_id, download_proress)


async def on_start_converting(
    download: Download,
    datasource: IDataSource,
    queue: NotificationQueue,
):
    """
    Callback called once ffmpeg media format converting process is initiated.
    """
    progress = -1
    download.status = DownloadStatus.CONVERTING
    download.progress = progress
    datasource.put_download(download)
    await queue.put(
        download.client_id,
        DownloadStatusInfo(
            title=download.title,
            client_id=download.client_id,
            media_id=download.media_id,
            status=download.status,
            progress=progress,
        ),
    )


async def on_finish_callback(
    download: Download,
    download_tmp_path: Path,
    datasource: IDataSource,
    queue: NotificationQueue,
    storage: IStorage,
    logger: Logger,
):
    """
    Callback which is executed once ffmpeg finished converting files.
    """
    file_posix_path = download_tmp_path.as_posix()
    file_size_bytes, file_size_hr = get_file_size(download_tmp_path)
    logger.debug(f"Uploading downloaded file {file_posix_path} to storage." f" File size: {file_size_hr}")
    try:
        in_storage_filename = storage.save_download_from_file(download, download_tmp_path)
        logger.debug(f"File {file_posix_path} uploaded...")
    except Exception as e:
        logger.error("Failed to save download file to storage.")
        await on_error_callback(
            download=download,
            exception=e,
            datasource=datasource,
            queue=queue,
            logger=logger,
        )
        return
    status = DownloadStatus.FINISHED
    download.file_path = in_storage_filename
    download.status = status
    download.progress = 100
    download.filesize = file_size_bytes
    download.filesize_hr = file_size_hr
    download.when_download_finished = datetime.utcnow()
    datasource.update_download(download)
    logger.debug(f'Download status for ({download.media_id}): {download.filename} updated to "{status}"')
    await queue.put(
        download.client_id,
        DownloadStatusInfo(
            title=download.title,
            filesize_hr=file_size_hr,
            client_id=download.client_id,
            media_id=download.media_id,
            status=status,
            progress=download.progress,
        ),
    )


async def on_error_callback(
    download: Download,
    exception: Exception,
    datasource: IDataSource,
    queue: NotificationQueue,
    logger: Logger,
):
    """
    Callback that is called when exception occured while downloading or converting media file.
    """
    if isinstance(exception, ffmpeg.Error):
        logger.error(exception.stderr)
    logger.exception(exception)
    datasource.mark_as_failed(download)
    await queue.put(
        download.client_id,
        download_progress=DownloadStatusInfo(
            title=download.title,
            client_id=download.client_id,
            media_id=download.media_id,
            status=DownloadStatus.FAILED,
        ),
    )


OnDownloadStateChangedCallback = Callable[
    [Download],
    Coroutine[Any, Any, Any],
]

OnDownloadFinishedCallback = Callable[[Download, Path], Coroutine[Any, Any, Any]]
OnErrorCallback = Callable[[Download, Exception], Coroutine[Any, Any, Any]]
