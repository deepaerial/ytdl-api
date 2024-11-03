import re
from enum import Enum


class DownloaderType(str, Enum):
    PYTUBE = "pytube"
    YTDLP = "yt-dlp"
    DUMMY = "dummy"

    def __str__(self) -> str:  # pragma: no cover
        return self.value


class DownloadStatus(str, Enum):
    STARTED = "started"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    FINISHED = "finished"
    DOWNLOADED = "downloaded"  # by client
    DELETED = "deleted"
    FAILED = "failed"

    def __str__(self) -> str:  # pragma: no cover
        return self.value


class MediaFormat(str, Enum):
    # Video formats
    MP4 = "mp4"
    # Audio formats
    MP3 = "mp3"
    WAV = "wav"

    @property
    def is_audio(self) -> bool:
        return self in [MediaFormat.MP3, MediaFormat.WAV]

    def __str__(self) -> str:  # pragma: no cover
        return self.value


YOUTUBE_URI_REGEX = re.compile(
    r"^((?:https?:)?\/\/)?((?:www|m)\.)?" r"((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)
