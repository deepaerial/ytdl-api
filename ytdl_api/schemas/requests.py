import re

from pydantic import Field, field_validator, model_validator

from ..constants import MediaFormat
from ..types import YOUTUBE_REGEX, YoutubeURL
from .base import BaseModel_


class DownloadParams(BaseModel_):
    url: YoutubeURL = Field(
        ...,
        description="URL to video",
        examples=["https://www.youtube.com/watch?v=B8WgNGN0IVA"],
    )
    video_stream_id: str | None = Field(None, description="Video stream ID", examples=["133"])
    audio_stream_id: str | None = Field(None, description="Audio stream ID", examples=["118"])
    media_format: MediaFormat = Field(
        ...,
        description="Video or audio (when extracting) format of file",
    )

    @model_validator(mode="after")
    @classmethod
    def validate_stream_ids(cls, obj: "DownloadParams"):
        video_stream_id, audio_stream_id = (
            obj.video_stream_id,
            obj.audio_stream_id,
        )
        if not any((video_stream_id, audio_stream_id)):
            raise ValueError("Video or/and audio stream id should be specified for download.")
        return obj

    @field_validator("url")
    @classmethod
    def is_url_allowed(cls, url):
        url_patterns = (YOUTUBE_REGEX,)
        if not any(re.compile(p).match(url) for p in url_patterns):
            raise ValueError("Domain is not allowed")
        return url
