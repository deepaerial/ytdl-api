import json
import os
from datetime import datetime
from pathlib import Path
from random import choice

from pytube.exceptions import VideoPrivate
from yt_dlp.utils import DownloadError

from ytdl_api.constants import DownloadStatus, MediaFormat
from ytdl_api.downloaders import IDownloader
from ytdl_api.schemas.models import Download
from ytdl_api.schemas.requests import DownloadParams
from ytdl_api.schemas.responses import VideoInfoResponse
from ytdl_api.types import YoutubeURL
from ytdl_api.utils import get_unique_id


class FakerForDownloads:
    def __init__(self, temporary_directory: Path):
        self.temporary_directory = temporary_directory
        self.fixtures = {}
        self.private_videos = []

    def load_from_fixtures_file(self, fixtures_path: Path):
        with fixtures_path.open("r") as file:
            content = file.read()
            json_content: list[dict] = json.loads(content)
            for video_data in json_content:
                video_id = video_data["url"].split("v=")[1]
                self.fixtures[video_id] = video_data
        return self

    def random_download_params(self) -> DownloadParams:
        video_data = choice(list(self.fixtures.values()))
        return DownloadParams(
            url=video_data["url"],
            video_stream_id=choice(video_data["videoStreams"])["id"],
            audio_stream_id=choice(video_data["audioStreams"])["id"],
            media_format=choice(list(MediaFormat)),
        )

    def random_download(
        self,
        client_id: str,
        duration: int = 10000,
        filesize: int = 10000,
        status: DownloadStatus = DownloadStatus.STARTED,
        progress: int = 0,
        when_submitted: datetime | None = None,
        when_started_download: datetime | None = None,
        when_file_downloaded: datetime | None = None,
        make_fake_file: bool = False,
        select_streams: bool = False,
    ) -> Download:
        media_id = get_unique_id()
        when_submitted = when_submitted or datetime.now()
        video_data = choice(list(self.fixtures.values()))
        download_data = {
            **video_data,
            "media_id": media_id,
            "client_id": client_id,
            "media_format": choice(list(MediaFormat)),
            "duration": duration,
            "filesize": filesize,
            "status": status,
            "progress": progress,
            "when_submitted": when_submitted,
            "when_started_download": when_started_download,
            "when_file_downloaded": when_file_downloaded,
        }
        if make_fake_file:
            file_path = self.temporary_directory / f"{media_id}.mp4"
            with file_path.open("wb") as f:
                file_size_in_bytes = 1024
                f.write(os.urandom(file_size_in_bytes))
            download_data["file_path"] = file_path.as_posix()
        else:
            download_data["file_path"] = None
        if select_streams:
            download_data["video_stream_id"] = choice(video_data["videoStreams"])["id"]
            download_data["audio_stream_id"] = choice(video_data["audioStreams"])["id"]
        download = Download(**download_data)
        return download

    def random_started_download(self, client_id: str, when_submitted: datetime | None = None) -> Download:
        return self.random_download(
            client_id,
            status=DownloadStatus.STARTED,
            select_streams=True,
        )

    def random_finished_download(self, client_id: str, make_file: bool = True) -> Download:
        return self.random_download(
            client_id,
            status=DownloadStatus.FINISHED,
            filesize=1024,
            progress=100,
            make_fake_file=make_file,
            select_streams=True,
        )

    def random_failed_download(self, client_id: str) -> Download:
        return self.random_download(
            client_id, status=DownloadStatus.FAILED, duration=1000, filesize=1024, select_streams=True, progress=57
        )

    def random_downloading_download(self, client_id: str) -> Download:
        return self.random_download(
            client_id, status=DownloadStatus.DOWNLOADING, duration=1000, filesize=1024, select_streams=True, progress=57
        )

    def random_downloaded_media(self, client_id: str, when_submitted: datetime | None = None) -> Download:
        when_submitted = when_submitted or datetime.now()
        return self.random_download(
            client_id,
            status=DownloadStatus.DOWNLOADED,
            duration=1000,
            filesize=1024,
            when_submitted=when_submitted,
            make_fake_file=True,
            select_streams=True,
            progress=100,
        )

    def get_video_info_by_url(self, url: YoutubeURL | str) -> VideoInfoResponse:
        video_id = url.split("v=")[1]
        video_data = self.fixtures[video_id]
        return VideoInfoResponse(
            url=video_data["url"],
            title=video_data["title"],
            thumbnail_url=video_data["thumbnailUrl"],
            duration=video_data["duration"],
            audio_streams=video_data["audioStreams"],
            video_streams=video_data["videoStreams"],
        )


class FakeDownloader(IDownloader):
    def __init__(self, faker_for_downloads: FakerForDownloads):
        self.faker = faker_for_downloads

    def get_video_info(self, url: YoutubeURL | str) -> VideoInfoResponse:  # pragma: no cover
        """
        Abstract method for retrieving information about media resource.
        """
        if url == "https://www.youtube.com/watch?v=mCk1ChMlqt0":
            # TODO: Generally test should be reproducable in a way which is constant, so choosing which
            # "private video" exception to raise is not a good practice. But for now I don't have a better idea.
            privatevideo_exceptions = (
                DownloadError(
                    "[youtube] mCk1ChMlqt0: Private video. Sign in if you've been granted access to this video"
                ),
                VideoPrivate("mCk1ChMlqt0"),
            )
            raise choice(privatevideo_exceptions)
        return self.faker.get_video_info_by_url(url)

    def download(self, download: Download) -> bool:  # pragma: no cover
        """
        Abstract method for downloading media given download parameters.
        """
        return True
