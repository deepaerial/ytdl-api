from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine

from .constants import DownloadStatus
from .datasource import IDataSource
from .queue import NotificationQueue
from .schemas.models import Download, DownloadProgress
from .storage import IStorage


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
        DownloadProgress(
            client_id=download.client_id,
            media_id=download.media_id,
            status=DownloadStatus.STARTED,
            progress=0,
        ),
    )


async def on_pytube_progress_callback(
    download: Download,
    datasource: IDataSource,
    queue: NotificationQueue,
    *args,
    **kwargs
):
    """
    Callback which will be used in Pytube's progress update callback
    """
    download_proress = DownloadProgress(
        client_id=download.client_id,
        media_id=download.media_id,
        status=DownloadStatus.DOWNLOADING,
        progress=-1,
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
        DownloadProgress(
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
):
    """
    Callback which is executed once ffmpeg finished converting files.
    """
    status = DownloadStatus.FINISHED
    in_storage_filename = storage.save_download_from_file(download, download_tmp_path)
    download.file_path = in_storage_filename
    download.status = status
    download.progress = 100
    download.when_download_finished = datetime.utcnow()
    datasource.update_download(download)
    await queue.put(
        download.client_id,
        DownloadProgress(
            client_id=download.client_id,
            media_id=download.media_id,
            status=status,
            progress=download.progress,
        ),
    )


OnDownloadStateChangedCallback = Callable[
    [Download],
    Coroutine[Any, Any, Any],
]

OnDownloadFinishedCallback = Callable[[Download, Path], Coroutine[Any, Any, Any]]
