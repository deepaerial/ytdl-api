import urllib.parse
from typing import Annotated, TypedDict

from pydantic import AfterValidator, StringConstraints, WithJsonSchema

YOUTUBE_REGEX = (
    r"^((https?)?:(\/\/))?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)

_YOUTUBE_BASE_URL = "https://www.youtube.com/watch?v={}"


def _get_clear_video_url(url_str: str) -> str:
    url = urllib.parse.urlparse(url_str)
    query_params = urllib.parse.parse_qs(url.query)
    if "list" in query_params.keys():
        video_id = query_params["v"][0]
        return _YOUTUBE_BASE_URL.format(video_id)
    return url_str


YoutubeURL = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=YOUTUBE_REGEX),
    AfterValidator(_get_clear_video_url),
    WithJsonSchema({"type": "string", "pattern": YOUTUBE_REGEX}, mode="serialization"),
]


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
