from pydantic import parse_obj_as
from datetime import datetime
from ytdl_api.constants import DownloadStatus, MediaFormat
from ytdl_api.schemas.models import Download

EXAMPLE_VIDEO_PREVIEW = {
    "url": "https://www.youtube.com/watch?v=NcBjx_eyvxc",
    "title": "Madeira | Cinematic FPV",
    "duration": 224,
    "thumbnailUrl": "https://i.ytimg.com/vi/NcBjx_eyvxc/hq720.jpg?sqp=-oaymwEXCNUGEOADIAQqCwjVARCqCBh4INgESFo&rs=AOn4CLBaSe3Sk63UjfwWlEhviOSxrq6TEg",
    "audioStreams": [
        {"id": "251", "mimetype": "audio/webm", "bitrate": "160kbps"},
        {"id": "250", "mimetype": "audio/webm", "bitrate": "70kbps"},
        {"id": "249", "mimetype": "audio/webm", "bitrate": "50kbps"},
        {"id": "140", "mimetype": "audio/mp4", "bitrate": "128kbps"},
        {"id": "139", "mimetype": "audio/mp4", "bitrate": "48kbps"},
    ],
    "videoStreams": [
        {"id": "278", "mimetype": "video/webm", "resolution": "144p"},
        {"id": "160", "mimetype": "video/mp4", "resolution": "144p"},
        {"id": "242", "mimetype": "video/webm", "resolution": "240p"},
        {"id": "133", "mimetype": "video/mp4", "resolution": "240p"},
        {"id": "243", "mimetype": "video/webm", "resolution": "360p"},
        {"id": "134", "mimetype": "video/mp4", "resolution": "360p"},
        {"id": "244", "mimetype": "video/webm", "resolution": "480p"},
        {"id": "135", "mimetype": "video/mp4", "resolution": "480p"},
        {"id": "247", "mimetype": "video/webm", "resolution": "720p"},
        {"id": "136", "mimetype": "video/mp4", "resolution": "720p"},
        {"id": "248", "mimetype": "video/webm", "resolution": "1080p"},
        {"id": "137", "mimetype": "video/mp4", "resolution": "1080p"},
        {"id": "271", "mimetype": "video/webm", "resolution": "1440p"},
        {"id": "313", "mimetype": "video/webm", "resolution": "2160p"},
    ],
    "mediaFormats": ["mp4", "mp3", "wav"],
}


def get_example_download_instance(
    client_id: str,
    media_format: MediaFormat = MediaFormat.MP4,
    duration: int = 10000,
    filesize: int = 10000,
    status: DownloadStatus = DownloadStatus.STARTED,
    file_path: str | None = None,
    progress: int = 0,
    when_started_download: datetime | None = None,
) -> Download:
    download_data = {
        **EXAMPLE_VIDEO_PREVIEW,
        "client_id": client_id,
        "media_format": media_format,
        "duration": duration,
        "filesize": filesize,
        "status": status,
        "file_path": file_path,
        "progress": progress,
        "when_started_download": when_started_download,
    }
    return parse_obj_as(Download, download_data)
