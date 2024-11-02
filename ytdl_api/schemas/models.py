import datetime

from pydantic import AnyHttpUrl, Field

from ..constants import DownloadStatus, MediaFormat
from ..types import YoutubeURL
from ..utils import get_datetime_now, get_unique_id
from .base import BaseModel_


class BaseStream(BaseModel_):
    id: str = Field(..., description="Stream ID", example="123")
    mimetype: str = Field(..., description="Stream mime-type", example="audio/webm")


class VideoStream(BaseStream):
    resolution: str = Field(..., description="Video resolution", example="1080p")


class AudioStream(BaseStream):
    bitrate: str = Field(..., description="Audio average bitrate", example="160kbps")


class Download(BaseModel_):
    client_id: str = Field(..., description="Client ID")
    media_id: str = Field(description="Download id", default_factory=get_unique_id)
    title: str = Field(..., description="Video title")
    url: YoutubeURL = Field(..., description="URL of video")
    video_streams: list[VideoStream] = Field(description="List of video streams", default_factory=list)
    audio_streams: list[AudioStream] = Field(description="List of audio streams", default_factory=list)
    video_stream_id: str | None = Field(None, description="Video stream ID (downloaded)")
    audio_stream_id: str | None = Field(None, description="Audio stream ID (downloaded)")
    media_format: MediaFormat = Field(
        None,
        description="Video or audio (when extracting) format of file",
    )
    duration: int = Field(..., description="Video duration (in milliseconds)")
    filesize: int = Field(None, description="Video/audio filesize (in bytes)")
    filesize_hr: str = Field(None, description="Video/audio filesize (human-readable)")
    thumbnail_url: AnyHttpUrl | str = Field(..., description="Video thumbnail")
    status: DownloadStatus = Field(DownloadStatus.STARTED, description="Download status")
    file_path: str | None = Field(None, description="Path to file")
    progress: int = Field(0, description="Download progress in %")
    when_submitted: datetime.datetime = Field(
        default_factory=get_datetime_now,
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
    when_failed: datetime.datetime | None = Field(
        None, description="Date & time in UTC when error occured during download."
    )

    @property
    def key(self) -> str:
        """
        Key used for PK in database.
        """
        return self.media_id

    @property
    def storage_filename(self) -> str:
        """
        File name used when storing download in file storage.
        """
        return f"{self.media_id}.{self.media_format}"

    @property
    def filename(self) -> str:
        """
        File name with extension
        """
        return f"{self.title}.{self.media_format}"


class DownloadStatusInfo(BaseModel_):
    key: str = Field(..., description="Unique key used in database.")
    title: str = Field(..., description="Video/audio title")
    filesize_hr: str | None = Field(None, description="Video/audio file size in human-readable format")
    client_id: str = Field(..., description="Id of client")
    media_id: str = Field(..., description="Id of downloaded media")
    status: DownloadStatus = Field(..., description="Download status", example=DownloadStatus.DOWNLOADING)
    progress: int | None = Field(
        None,
        description="Download progress of a file in case status is 'downloading'",
        example=10,
    )
