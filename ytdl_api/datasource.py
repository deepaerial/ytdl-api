import datetime
from abc import ABC, abstractmethod

from pydantic import TypeAdapter
from supabase import create_client
from tinydb import Query, TinyDB, where
from tinydb.storages import MemoryStorage

from .constants import DownloadStatus
from .schemas.models import Download, DownloadStatusInfo
from .utils import get_datetime_now


class IDataSource(ABC):
    """
    Abstract interface that provides abstract methods for accessing and manipulating data
    from database.
    """

    @abstractmethod
    def fetch_available_downloads(self, client_id: str) -> list[Download]:  # pragma: no cover
        """
        Abstract method that returns list of clients non-deleted downloads from data source.
        """
        raise NotImplementedError()

    @abstractmethod
    def fetch_downloads_till_datetime(self, till_when: datetime.datetime) -> list[Download]:  # pragma: no cover
        """
        Abstract method that returns list of downloads from data source till specific datetime.
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

    @abstractmethod
    def delete_download_batch(self, downloads: list[Download]):  # pragma: no cover
        """
        Abstract method for deleting multiple downloads from database.
        """
        raise NotImplementedError()


class InMemoryDB(IDataSource):
    """
    Simple in-memory database implementation.
    """

    def __init__(
        self,
    ):
        self.db = TinyDB(storage=MemoryStorage)
        self.db.default_table_name = "downloads"

    def fetch_available_downloads(self, client_id: str) -> list[Download]:
        return self.db.search((Query()["client_id"] == client_id) & (Query()["status"] != DownloadStatus.DELETED))

    def fetch_downloads_till_datetime(self, till_when: datetime.datetime) -> list[Download]:
        downloads = self.db.search(Query()["when_submitted"] <= till_when)
        return TypeAdapter(list[Download]).validate_python(downloads)

    def put_download(self, download: Download):
        self.db.insert(download.model_dump())

    def get_download(self, client_id: str, media_id: str) -> Download | None:
        q = Query()
        download = self.db.get(
            (q["client_id"] == client_id) & (q["media_id"] == media_id) & (q["status"] != DownloadStatus.DELETED)
        )
        return Download(**download) if download else None

    def update_download(self, download: Download):
        self.db.update(download.model_dump(), Query()["media_id"] == download.media_id)

    def update_download_progress(self, progress_obj: DownloadStatusInfo):
        self.db.update(progress_obj.model_dump(), (Query()["media_id"] == progress_obj.key))

    def delete_download(
        self,
        download: Download,
        when_deleted: datetime.datetime | None = None,
    ):
        when_deleted = when_deleted or get_datetime_now()
        self.db.update(
            {"status": DownloadStatus.DELETED, "when_deleted": when_deleted},
            (Query()["media_id"] == download.media_id),
        )

    def mark_as_downloaded(
        self,
        download: Download,
        when_file_downloaded: datetime.datetime | None = None,
    ):
        when_file_downloaded = when_file_downloaded or get_datetime_now()
        self.db.update(
            {"status": DownloadStatus.DOWNLOADED, "when_file_downloaded": when_file_downloaded},
            (Query()["media_id"] == download.media_id),
        )

    def clear_downloads(self):
        self.db.truncate()

    def mark_as_failed(self, download: Download, when_failed: datetime.datetime | None = None):
        when_failed = when_failed or get_datetime_now()
        self.db.update(
            {"status": DownloadStatus.FAILED, "when_failed": when_failed},
            (Query()["media_id"] == download.media_id),
        )

    def delete_download_batch(self, downloads: list[Download]):
        """
        Soft deleting data from database.
        """
        when_deleted = get_datetime_now()
        batch = [
            (
                {"status": DownloadStatus.DELETED, "when_deleted": when_deleted},
                where("media_id") == download.media_id,
            )
            for download in downloads
        ]
        self.db.update_multiple(batch)


class SupabaseDB(IDataSource):
    """
    DAO interface implementation for Supabase: https://supabase.io/
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)

    def fetch_downloads_by_client_id(self, client_id: str) -> list[Download]:
        response = (
            self.supabase.table("downloads")
            .select("*")
            .eq("client_id", client_id)
            .ne("status", DownloadStatus.DELETED)
            .order_by("when_submitted", ascending=False)
            .execute()
        )
        downloads = response.get("data", [])
        return parse_obj_as(list[Download], downloads)

    def fetch_downloads_till_datetime(self, till_when: datetime.datetime) -> list[Download]:
        response = (
            self.supabase.table("downloads")
            .select("*")
            .lte("when_submitted", till_when)
            .not_in("status", [DownloadStatus.DELETED, DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING])
            .execute()
        )
        downloads = response.get("data", [])
        return parse_obj_as(list[Download], downloads)

    def put_download(self, download: Download):
        data = download.dict()
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
        self.supabase.table("downloads").upsert(data, on_conflict="deta_db_key")

    def get_download(self, client_id: str, media_id: str) -> Download | None:
        response = (
            self.supabase.table("downloads")
            .select("*")
            .eq("client_id", client_id)
            .eq("media_id", media_id)
            .ne("status", DownloadStatus.DELETED)
            .limit(1)
            .execute()
        )
        download = response.get("data", [None])[0]
        if download is None:
            return None
        return Download(**download)

    def update_download(self, download: Download):
        data = download.dict()
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
        self.supabase.table("downloads").upsert(data, on_conflict="deta_db_key")

    def update_download_progress(self, progress_obj: DownloadStatusInfo):
        media_id = progress_obj.media_id
        status = progress_obj.status
        progress = progress_obj.progress
        self.supabase.table("downloads").update({"status": status, "progress": progress}).eq(
            "media_id", media_id
        ).execute()

    def delete_download(
        self,
        download: Download,
        when_deleted: datetime.datetime | None = None,
    ):
        when_deleted = when_deleted or get_datetime_now()
        when_deleted_iso = when_deleted.isoformat()
        data = {"status": DownloadStatus.DELETED, "when_deleted": when_deleted_iso}
        self.supabase.table("downloads").update(data).eq("deta_db_key", download.deta_db_key).execute()

    def mark_as_downloaded(
        self,
        download: Download,
        when_file_downloaded: datetime.datetime | None = None,
    ):
        when_file_downloaded = when_file_downloaded or get_datetime_now()
        when_file_downloaded_iso = when_file_downloaded.isoformat()
        data = {
            "status": DownloadStatus.DOWNLOADED,
            "when_file_downloaded": when_file_downloaded_iso,
        }
        self.supabase.table("downloads").update(data).eq("deta_db_key", download.deta_db_key).execute()

    def clear_downloads(self):
        self.supabase.table("downloads").delete().execute()

    def mark_as_failed(self, download: Download, when_failed: datetime.datetime | None = None):
        when_failed = when_failed or get_datetime_now()
        when_failed_iso = when_failed.isoformat()
        data = {"status": DownloadStatus.FAILED, "when_failed": when_failed_iso}
        self.supabase.table("downloads").update(data).eq("deta_db_key", download.deta_db_key).execute()

    def delete_download_batch(self, downloads: list[Download]):
        for download in downloads:
            self.delete_download(download)
