from typing import Optional, List
from functools import partial
from sqlmodel import Field, SQLModel, JSON
from datetime import datetime, UTC
from uuid import UUID


class DownloadDBModel(SQLModel, table=True):
    client_id: str = Field(nullable=False, description="Client ID")
    media_id: UUID = Field(default=None, primary_key=True, description="Download id")
    title: str = Field(nullable=False, description="Video title")
    url: str = Field(nullable=False, description="URL of video")
    video_streams: List = Field(sa_column=JSON, default=[], description="List of video streams")
    audio_streams: List = Field(sa_column=JSON, default=[], description="List of audio streams")
    video_stream_id: Optional[str] = Field(default=None, description="Video stream ID (downloaded)")
    audio_stream_id: Optional[str] = Field(default=None, description="Audio stream ID (downloaded)")
    media_format: str = Field(nullable=False, description="Video or audio (when extracting) format of file")
    duration: int = Field(nullable=False, description="Video duration (in milliseconds)")
    filesize: Optional[int] = Field(default=None, description="Video/audio filesize (in bytes)")
    filesize_hr: Optional[str] = Field(default=None, description="Video/audio filesize (human-readable)")
    thumbnail_url: str = Field(nullable=False, description="Video thumbnail")
    status: str = Field(nullable=False, description="Download status")
    file_path: Optional[str] = Field(default=None, description="Path to file")
    progress: int = Field(default=0, description="Download progress in %")
    when_submitted: datetime = Field(
        default_factory=partial(datetime.now, UTC), description="Date & time in UTC when download was submitted to API."
    )
    when_started_download: Optional[datetime] = Field(
        default=None, description="Date & time in UTC when download started."
    )
    when_download_finished: Optional[datetime] = Field(
        default=None, description="Date & time in UTC when download finished."
    )
    when_file_downloaded: Optional[datetime] = Field(
        default=None, description="Date & time in UTC when file was downloaded."
    )
    when_deleted: Optional[datetime] = Field(
        default=None, description="Date & time in UTC when download was soft-deleted."
    )
    when_failed: Optional[datetime] = Field(
        default=None, description="Date & time in UTC when error occurred during download."
    )
