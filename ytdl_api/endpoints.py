import asyncio
import mimetypes

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from starlette import status

from . import config, datasource, dependencies, storage
from .constants import DownloadStatus
from .converters import create_download_from_download_params
from .downloaders import IDownloader
from .queue import NotificationQueue
from .schemas import requests, responses
from .types import YoutubeURL
from .utils import get_content_disposition_header_value

router = APIRouter(tags=["base"])

get_uid = dependencies.get_uid_dependency_factory()
get_uid_or_403 = dependencies.get_uid_dependency_factory(raise_error_on_empty=True)


@router.get(
    "/version",
    response_model=responses.VersionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_uid)],
)
async def get_api_version(
    settings: config.Settings = Depends(dependencies.get_settings),
):
    """
    Endpoint for getting info about server API and fetching list of downloaded videos.
    """
    return {
        "api_version": settings.version,
        "downloader": settings.downloader,
        "downloader_version": settings.downloader_version,
    }


@router.get(
    "/downloads",
    response_model=responses.DownloadsResponse,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": responses.ErrorResponse}},
)
async def get_downloads(
    uid: str = Depends(get_uid_or_403),
    datasource: datasource.IDataSource = Depends(dependencies.get_database),
):
    """
    Endpoint for fetching list of downloaded videos for current client/user.
    """
    downloads = datasource.fetch_downloads(uid)
    return {"downloads": downloads}


@router.get(
    "/preview",
    response_model=responses.VideoInfoResponse,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": responses.ErrorResponse}},
)
async def preview(
    url: YoutubeURL,
    downloader: IDownloader = Depends(dependencies.get_downloader),
):
    """
    Endpoint for getting info about video.
    """
    download = downloader.get_video_info(url.get_clear_video_url())
    return download


@router.put(
    "/download",
    response_model=responses.DownloadsResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": responses.ErrorResponse}},
)
async def submit_download(
    download_params: requests.DownloadParams,
    background_tasks: BackgroundTasks,
    uid: str = Depends(get_uid_or_403),
    datasource: datasource.IDataSource = Depends(dependencies.get_database),
    downloader: IDownloader = Depends(dependencies.get_downloader),
):
    """
    Endpoint for fetching video from Youtube and converting it to
    specified format.
    """
    download = create_download_from_download_params(uid, download_params, downloader)
    datasource.put_download(download)
    background_tasks.add_task(downloader.download, download)
    return {"downloads": datasource.fetch_downloads(uid)}


@router.get(
    "/download",
    responses={
        status.HTTP_200_OK: {
            "content": {"application/octet-stream": {}},
            "description": "Downloaded media file",
        },
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {}},
            "model": responses.ErrorResponse,
            "description": "Download not found",
            "example": {"detail": "Download not found"},
        },
    },
)
async def download_file(
    media_id: str = Query(..., alias="mediaId", description="Download id"),
    uid: str = Depends(get_uid_or_403),
    datasource: datasource.IDataSource = Depends(dependencies.get_database),
    storage: storage.IStorage = Depends(dependencies.get_storage),
):
    """
    Endpoint for downloading fetched video from Youtube.
    """
    media_file = datasource.get_download(uid, media_id)
    if media_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download not found")
    if media_file.status not in (DownloadStatus.FINISHED, DownloadStatus.DOWNLOADED):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not downloaded yet")
    if media_file.file_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download is finished but file not found",
        )
    bytes_stream = storage.get_download(media_file.file_path)
    datasource.mark_as_downloaded(media_file)
    return StreamingResponse(
        bytes_stream,
        media_type=mimetypes.guess_type(media_file.filename)[0],
        headers={"content-disposition": get_content_disposition_header_value(media_file.filename)},
    )


@router.get("/download/stream", response_class=EventSourceResponse)
async def fetch_stream(
    request: Request,
    uid: str = Depends(get_uid_or_403),
    event_queue: NotificationQueue = Depends(dependencies.get_notification_queue),
):
    """
    SSE endpoint for recieving download status of media items.
    """

    async def _stream():
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await event_queue.get(uid)
            except asyncio.QueueEmpty:
                continue
            else:
                yield data.json(exclude={"key"}, by_alias=True)

    return EventSourceResponse(_stream())


@router.delete(
    "/delete",
    response_model=responses.DeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {}},
            "model": responses.ErrorResponse,
            "description": "Download not found",
            "example": {"detail": "Download not found"},
        },
        status.HTTP_400_BAD_REQUEST: {
            "content": {"application/json": {}},
            "model": responses.ErrorResponse,
            "description": "Media is not downloaded",
            "example": {"detail": "Media is not downloaded"},
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": responses.ErrorResponse},
    },
)
async def delete_download(
    media_id: str = Query(..., alias="mediaId", description="Download id"),
    uid: str = Depends(get_uid_or_403),
    datasource: datasource.IDataSource = Depends(dependencies.get_database),
    storage: storage.IStorage = Depends(dependencies.get_storage),
):
    """
    Endpoint for deleting downloaded media.
    """
    media_file = datasource.get_download(uid, media_id)
    if media_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download not found")
    if media_file.status not in (
        DownloadStatus.FINISHED,
        DownloadStatus.DOWNLOADED,
        DownloadStatus.FAILED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media file is not downloaded yet",
        )
    datasource.delete_download(media_file)
    if media_file.status != DownloadStatus.FAILED:
        storage.remove_download(media_file.file_path)
    return responses.DeleteResponse(
        media_id=media_file.media_id,
        status=DownloadStatus.DELETED,
        isAudio=media_file.media_format.is_audio,
        title=media_file.title,
    )


@router.put(
    "/retry",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {}},
            "model": responses.ErrorResponse,
            "description": "Download not found",
            "example": {"detail": "Download not found"},
        },
        status.HTTP_400_BAD_REQUEST: {
            "content": {"application/json": {}},
            "model": responses.ErrorResponse,
            "description": "Download cannot be retried",
            "example": {"detail": "Download cannot be retried"},
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": responses.ErrorResponse},
    },
)
async def retry_download(
    background_tasks: BackgroundTasks,
    media_id: str = Query(..., alias="mediaId", description="Download id"),
    uid: str = Depends(get_uid_or_403),
    datasource: datasource.IDataSource = Depends(dependencies.get_database),
    downloader: IDownloader = Depends(dependencies.get_downloader),
):
    """
    Endpoint for retrying donwload of failed media file.
    """
    download = datasource.get_download(uid, media_id)
    if download is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download not found")
    if download.status not in (DownloadStatus.FAILED, DownloadStatus.STARTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Download cannot be retried",
        )
    download.status = DownloadStatus.STARTED
    datasource.update_download(download)
    background_tasks.add_task(downloader.download, download)
    return status.HTTP_200_OK
