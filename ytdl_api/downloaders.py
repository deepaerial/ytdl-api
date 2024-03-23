import asyncio
import tempfile
from abc import ABC, abstractmethod
from functools import partial
from pathlib import Path
from typing import Literal, Optional

import ffmpeg
from pytube import StreamQuery, YouTube
from yt_dlp import YoutubeDL

from .callbacks import (
    OnDownloadFinishedCallback,
    OnDownloadStateChangedCallback,
    OnErrorCallback,
    noop_callback,
)
from .schemas.models import AudioStream, Download, VideoStream
from .schemas.responses import VideoInfoResponse
from .types import YoutubeURL


class IDownloader(ABC):
    """
    Base interface for media downloader class.
    """

    def __init__(
        self,
        on_download_started_callback: Optional[OnDownloadStateChangedCallback] = None,
        on_progress_callback: Optional[OnDownloadStateChangedCallback] = None,
        on_converting_callback: Optional[OnDownloadStateChangedCallback] = None,
        on_finish_callback: Optional[OnDownloadFinishedCallback] = None,
        on_error_callback: Optional[OnErrorCallback] = None,
    ):
        self.on_download_callback_start = on_download_started_callback or noop_callback
        self.on_progress_callback = on_progress_callback or noop_callback
        self.on_converting_callback = on_converting_callback or noop_callback
        self.on_finish_callback = on_finish_callback or noop_callback
        self.on_error_callback = on_error_callback or noop_callback

    @abstractmethod
    def get_video_info(self, url: YoutubeURL | str) -> VideoInfoResponse:  # pragma: no cover
        """
        Abstract method for retrieving information about media resource.
        """
        raise NotImplementedError()

    @abstractmethod
    def download(self, download: Download) -> bool:  # pragma: no cover
        """
        Abstract method for downloading media given download parameters.
        """
        raise NotImplementedError()


class PytubeDownloader(IDownloader):
    """
    Downloader based on pytube library https://github.com/pytube/pytube
    """

    def get_video_info(self, url: YoutubeURL | str) -> VideoInfoResponse:
        video = YouTube(url)
        streams = video.streams.filter(is_dash=True).desc()
        audio_streams = [
            AudioStream(id=str(stream.itag), bitrate=stream.abr, mimetype=stream.mime_type)
            for stream in streams.filter(only_audio=True)
        ]
        video_streams = [
            VideoStream(
                id=str(stream.itag),
                resolution=stream.resolution,
                mimetype=stream.mime_type,
            )
            for stream in streams.filter(only_video=True)
        ]
        video_info = VideoInfoResponse(
            url=url,
            title=video.title,
            thumbnail_url=video.thumbnail_url,
            audio_streams=audio_streams,
            video_streams=video_streams,
            duration=video.length,
        )
        return video_info

    def __download_stream(
        self,
        directory_to_download_to: Path,
        stream_id: str | None,
        media_id: str,
        streams: StreamQuery,
        downloaded_streams_aggregation: dict,
        stream_type: Literal["audio", "video"],
    ):
        if stream_id is None:
            return
        stream = streams.get_by_itag(stream_id)
        downloaded_stream_file_path = stream.download(
            directory_to_download_to, filename_prefix=f"{stream_id}_{media_id}"
        )
        downloaded_streams_aggregation[stream_type] = Path(downloaded_stream_file_path)

    def _merge_streams(
        self,
        video_stream_posix_path: str,
        audio_stream_posix_path: str,
        merged_streams_posix_path: str,
    ):
        (
            ffmpeg.concat(
                ffmpeg.input(video_stream_posix_path),
                ffmpeg.input(audio_stream_posix_path),
                a=1,
                v=1,
            )
            .output(merged_streams_posix_path)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

    def download(
        self,
        download: Download,
    ) -> bool:
        on_progress_callback = partial(
            self.on_progress_callback,
            download,
        )
        kwargs = {
            "on_progress_callback": lambda stream, chunk, bytes_remaining: asyncio.run(
                on_progress_callback(stream=stream, chunk=chunk, bytes_remaining=bytes_remaining)
            )
        }
        try:
            asyncio.run(self.on_download_callback_start(download))
            streams = YouTube(download.url, **kwargs).streams.filter(is_dash=True).desc()
            downloaded_streams_file_paths: dict[str, Path] = {}
            with tempfile.TemporaryDirectory() as tmpdir:
                directory_to_download_to = Path(tmpdir)
                # Downloading audio stream if chosen
                self.__download_stream(
                    directory_to_download_to,
                    download.audio_stream_id,
                    download.media_id,
                    streams,
                    downloaded_streams_file_paths,
                    "audio",
                )
                # Downloading video stream if chosen
                self.__download_stream(
                    directory_to_download_to,
                    download.video_stream_id,
                    download.media_id,
                    streams,
                    downloaded_streams_file_paths,
                    "video",
                )
                # Converting to chosen format
                asyncio.run(self.on_converting_callback(download))
                converted_file_path = directory_to_download_to / download.storage_filename
                self._merge_streams(
                    downloaded_streams_file_paths["video"].as_posix(),
                    downloaded_streams_file_paths["audio"].as_posix(),
                    converted_file_path.as_posix(),
                )
                # Finshing download process
                asyncio.run(self.on_finish_callback(download, converted_file_path))
                return True
        except Exception as e:
            if self.on_error_callback:
                asyncio.run(self.on_error_callback(download, e))
            return False


class YTDLPDownloader(IDownloader):
    """
    Downloader based on yt-dlp library https://github.com/yt-dlp/yt-dlp
    """

    def get_video_info(self, url: YoutubeURL | str) -> VideoInfoResponse:
        with YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
        streams = info["formats"]
        audio_streams = [
            AudioStream(
                id=stream["format_id"],
                bitrate=f"{round(float(stream['abr']))}kbps",
                mimetype=stream["ext"],
            )
            for stream in streams
            if stream.get("acodec") != "none" and stream.get("vcodec") == "none" and stream.get("abr") is not None
        ]
        video_streams = [
            VideoStream(
                id=stream["format_id"],
                resolution=stream["format_note"],
                mimetype=stream["ext"],
            )
            for stream in streams
            if stream.get("acodec") == "none"
            and stream.get("vcodec") != "none"
            and stream.get("format_note") is not None
        ]
        return VideoInfoResponse(
            url=info["webpage_url"],
            title=info["title"],
            duration=info["duration"],
            thumbnail_url=info["thumbnail"],
            audio_streams=audio_streams,
            video_streams=video_streams,
        )

    def download(self, download: Download):
        on_progress_callback = partial(
            self.on_progress_callback,
            download=download,
        )
        try:
            asyncio.run(self.on_download_callback_start(download))
            with tempfile.TemporaryDirectory() as tmpdir:
                directory_to_download_to = Path(tmpdir)
                download_options = {
                    "progress_hooks": [
                        lambda d: asyncio.run(on_progress_callback(d)),
                    ],
                    "outtmpl": f"{directory_to_download_to.as_posix()}/{download.media_id}.%(ext)s",
                    "nomtime": True,  # do not use modification time fro original video
                }
                if download.media_format.is_audio:
                    download_options["format"] = download.audio_stream_id
                    download_options["postprocessors"] = [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": str(download.media_format),
                        }
                    ]
                else:
                    download_options["format"] = f"{download.video_stream_id}+{download.audio_stream_id}"
                    download_options["merge_output_format"] = download.media_format
                with YoutubeDL(download_options) as ydl:
                    ydl.download([download.url])
                downloaded_file_path = directory_to_download_to / download.storage_filename
                asyncio.run(self.on_finish_callback(download, downloaded_file_path))
                return True
        except Exception as e:
            if self.on_error_callback:
                asyncio.run(self.on_error_callback(download, e))
            return False
