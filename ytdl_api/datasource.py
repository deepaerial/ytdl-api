import datetime
import typing
from abc import ABC, abstractmethod

from deta import Deta
from pydantic import parse_obj_as

from .constants import DownloadStatus
from .schemas.models import Download, DownloadStatusInfo


class IDataSource(ABC):
    """
    Abstract interface that provides abstract methods for accessing and manipulating data
    from database.
    """

    @abstractmethod
    def fetch_downloads(self, client_id: str) -> typing.List[Download]:  # pragma: no cover
        """
        Abstract method that returns list of clients downloads from data source.
        """
        raise NotImplementedError()

    @abstractmethod
    def put_download(self, download: Download):  # pragma: no cover
        """
        Abstract method for inserting download instance to data source.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_download(self, client_id: str, media_id: str) -> Download | None:  # pragma: no cover
        """
        Abstract method for fetching download instance from data source
        """
        raise NotImplementedError()

    @abstractmethod
    def update_download(self, download: Download):  # pragma: no cover
        """
        Abstract method for updating download instance from data source
        """
        raise NotImplementedError()

    @abstractmethod
    def update_download_progress(self, progress_obj: DownloadStatusInfo):  # pragma: no cover
        """
        Abstract method that updates progress for media item of specific user/client.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_download(
        self,
        download: Download,
        when_deleted: datetime.datetime | None = None,
    ):  # pragma: no cover
        """
        Abstract method that deletes download.
        """
        raise NotImplementedError()

    @abstractmethod
    def mark_as_downloaded(
        self,
        download: Download,
        when_file_downloaded: datetime.datetime | None = None,
    ):  # pragma: no cover
        """
        Abstract method that marks download as downloaded by user/client.
        """
        raise NotImplementedError()

    @abstractmethod
    def clear_downloads(self):  # pragma: no cover
        """
        Method for clearing all downloads. If intended to be used in specific implementation then it should be
        reimplemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def mark_as_failed(self, download: Download, when_failed: datetime.datetime | None = None):  # pragma: no cover
        """
        Method for setting download status to "failed" for download.
        """
        raise NotImplementedError()


class DetaDB(IDataSource):
    """
    DAO interface implementation for Deta Bases: https://docs.deta.sh/docs/base/sdk
    """

    def __init__(self, deta_project_key: str, base_name: str = "ytdl"):
        deta = Deta(deta_project_key)
        self.base = deta.Base(base_name)

    def fetch_downloads(self, client_id: str) -> typing.List[Download]:
        downloads = self.base.fetch({"client_id": client_id, "status?ne": DownloadStatus.DELETED}).items
        return parse_obj_as(typing.List[Download], downloads)

    def put_download(self, download: Download):
        data = download.dict()
        key = data["media_id"]
        data["when_submitted"] = download.when_submitted.isoformat()
        if download.when_started_download:
            data["when_started_download"] = download.when_started_download.isoformat()
        if download.when_download_finished:
            data["when_download_finished"] = download.when_download_finished.isoformat()
        if download.when_file_downloaded:
            data["when_file_downloaded"] = download.when_file_downloaded.isoformat()
        if download.when_deleted:
            data["when_deleted"] = download.when_deleted.isoformat()
        if download.when_failed:
            data["when_failed"] = download.when_failed.isoformat()
        self.base.put(data, key)

    def get_download(self, client_id: str, media_id: str) -> Download | None:
        data = next(
            iter(
                self.base.fetch(
                    {
                        "client_id": client_id,
                        "media_id": media_id,
                        "status?ne": DownloadStatus.DELETED,
                    }
                ).items
            ),
            None,
        )
        if data is None:
            return data
        download = Download(**data)
        return download

    def update_download(self, download: Download):
        data = download.dict()
        # quick fix for error TypeError: Object of type PosixPath is not JSON serializable
        if download.when_submitted is not None:
            data["when_submitted"] = download.when_submitted.isoformat()
        if download.when_download_finished is not None:
            data["when_download_finished"] = download.when_download_finished.isoformat()
        if download.when_file_downloaded is not None:
            data["when_file_downloaded"] = download.when_file_downloaded.isoformat()
        if download.when_started_download is not None:
            data["when_started_download"] = download.when_started_download.isoformat()
        if download.when_deleted is not None:
            data["when_deleted"] = download.when_deleted.isoformat()
        if download.when_failed:
            data["when_failed"] = download.when_failed.isoformat()
        self.base.update(data, download.media_id)

    def update_download_progress(self, progress_obj: DownloadStatusInfo):
        media_id = progress_obj.media_id
        status = progress_obj.status
        progress = progress_obj.progress
        self.base.update({"status": status, "progress": progress}, media_id)

    def delete_download(
        self,
        download: Download,
        when_deleted: datetime.datetime | None = None,
    ):
        """
        Soft deleting download for now.
        """
        when_deleted = when_deleted or datetime.datetime.now(datetime.UTC)
        when_deleted_iso = when_deleted.isoformat()
        data = {"status": DownloadStatus.DELETED, "when_deleted": when_deleted_iso}
        self.base.update(data, key=download.media_id)

    def mark_as_downloaded(
        self,
        download: Download,
        when_file_downloaded: datetime.datetime | None = None,
    ):
        when_file_downloaded = when_file_downloaded or datetime.datetime.now(datetime.UTC)
        when_file_downloaded_iso = when_file_downloaded.isoformat()
        data = {
            "status": DownloadStatus.DOWNLOADED,
            "when_file_downloaded": when_file_downloaded_iso,
        }
        self.base.update(data, download.media_id)

    def clear_downloads(self):
        all_downloads = self.base.fetch().items
        for download in all_downloads:
            self.base.delete(download["key"])
        self.base.client.close()

    def mark_as_failed(self, download: Download, when_failed: datetime.datetime | None = None):
        when_failed = when_failed or datetime.datetime.now(datetime.UTC)
        when_failed_iso = when_failed.isoformat()
        data = {"status": DownloadStatus.FAILED, "when_failed": when_failed_iso}
        self.base.update(data, download.media_id)
