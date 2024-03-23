import datetime

from pydantic import AnyHttpUrl, Field

from ..constants import DownloadStatus, MediaFormat
from ..types import YoutubeURL
from .base import BaseModel_
from .models import AudioStream, VideoStream


class ErrorResponse(BaseModel_):
    detail: str = Field(..., description="Message detail")
    code: str = Field(..., description="Custom error identifying code")


class DownloadResponse(BaseModel_):
    client_id: str = Field(..., description="Client ID.")
    media_id: str = Field(..., description="Download id.")
    title: str = Field(..., description="Video title.")
    url: YoutubeURL = Field(..., description="URL of video.")
    video_streams: list[VideoStream] = Field(description="list of video streams.", default_factory=list)
    audio_streams: list[AudioStream] = Field(description="list of audio streams.", default_factory=list)
    video_stream_id: str | None = Field(None, description="Video stream ID (downloaded).")
    audio_stream_id: str | None = Field(None, description="Audio stream ID (downloaded).")
    media_format: MediaFormat = Field(
        ...,
        description="Video or audio (when extracting) format of file.",
    )
    duration: int = Field(..., description="Video duration (in milliseconds).")
    filesize_hr: str | None = Field(
        None,
        description="Video/audio file size in human-readable format.",
    )
    thumbnail_url: AnyHttpUrl | str = Field(..., description="Video thumbnail.")
    status: DownloadStatus = Field(DownloadStatus.STARTED, description="Download status")
    when_submitted: datetime.datetime = Field(
        ...,
        description="Date & time in UTC when download was submitted to API.",
    )
    when_started_download: datetime.datetime | None = Field(
        None, description="Date & time in UTC when download started."
    )
    when_download_finished: datetime.datetime | None = Field(
        None, description="Date & time in UTC when download finished."
    )
    when_file_downloaded: datetime.datetime | None = Field(
        None, description="Date & time in UTC when file was downloaded."
    )
    when_deleted: datetime.datetime | None = Field(
        None, description="Date & time in UTC when download was soft-deleted."
    )


class DownloadsResponse(BaseModel_):
    downloads: list[DownloadResponse] = Field(
        ...,
        description="list of pending and finished downloads",
    )


class VersionResponse(BaseModel_):
    api_version: str
    downloader: str
    downloader_version: str


class DeleteResponse(BaseModel_):
    media_id: str = Field(..., description="Id of downloaded media")
    status: DownloadStatus = Field(..., description="Download status")
    isAudio: bool = Field(..., description="Is deleted file was audio file")
    title: str = Field(..., description="Deleted media file title")


class VideoInfoResponse(BaseModel_):
    url: YoutubeURL = Field(..., title="URL", description="URL to video")
    title: str = Field(..., description="Video title")
    duration: int = Field(..., description="Video length in seconds")
    thumbnail_url: AnyHttpUrl = Field(..., description="Video thumbnail")
    audio_streams: list[AudioStream] = Field([], description="Available audio streams")
    video_streams: list[VideoStream] = Field([], description="Available video streams")
    media_formats: list[MediaFormat] = Field(list(MediaFormat), description="Available media formats")
