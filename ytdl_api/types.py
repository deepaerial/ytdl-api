import re
import urllib.parse
from typing import TypedDict

from pydantic import AnyHttpUrl

YOUTUBE_REGEX = re.compile(
    r"^((https?)?:(\/\/))?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)


class YoutubeURL(AnyHttpUrl, str):
    """
    Custom type for Youtube video video URL.
    """

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            # simplified regex here for brevity, see the wikipedia link above
            pattern=YOUTUBE_REGEX.pattern,
        )

    @classmethod
    def validate(cls, v):
        match = YOUTUBE_REGEX.fullmatch(v)
        if not match:
            raise ValueError("Bad youtube video link provided.")
        full_url = match.group(0)
        scheme = match.group(2)
        return cls(url=full_url, scheme=scheme)

    def get_clear_video_url(self) -> "YoutubeURL":
        url = urllib.parse.urlparse(str(self))
        query_params = urllib.parse.parse_qs(url.query)
        if "list" in query_params.keys():
            video_id = query_params["v"][0]
            return YoutubeURL(url=f"https://www.youtube.com/watch?v={video_id}", scheme="https")
        return self


class DownloadDataInfo(TypedDict):
    _eta_str: str | None
    _percent_str: str | None
    _speed_str: str | None
    _total_bytes_str: str | None
    status: str
    filename: str
    tmpfilename: str
    downloaded_bytes: int
    total_bytes: int
    total_bytes_estimate: int | None
    elapsed: int
    eta: int | None
    speed: int | None
    fragment_index: int | None
    fragment_count: int | None
