import abc
import shutil
from pathlib import Path
from typing import Iterator

from deta import Deta

from .schemas.models import Download


class IStorage(abc.ABC):
    """
    Base interface for storage class that manages downloaded file.
    """

    @abc.abstractmethod
    def save_download_from_file(
        self, download: Download, path: Path
    ) -> str:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_download(
        self, storage_file_name: str
    ) -> Iterator[bytes]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def remove_download(self, storage_file_name: str):  # pragma: no cover
        raise NotImplementedError


def _read_file_at_chunks(file: Path, chunk_size: int = 1024) -> Iterator[bytes]:
    with file.open(mode="rb") as f:
        while data := f.read(chunk_size):
            yield data


class LocalFileStorage(IStorage):
    """
    Storage that saves downloaded files to host's filesystem.
    """

    def __init__(self, downloads_dir: Path) -> None:
        self.dowloads_dir = downloads_dir

    def save_download_from_file(self, download: Download, path: Path) -> str:
        dest_path = self.dowloads_dir / download.storage_filename
        shutil.copy(path, dest_path)
        return dest_path.as_posix()

    def get_download(self, storage_file_name: str) -> Iterator[bytes]:
        download_file = self.dowloads_dir / Path(storage_file_name)
        if not download_file.exists():
            return None
        return _read_file_at_chunks(download_file)

    def remove_download(self, storage_file_name: str):
        download_file = Path(storage_file_name)
        if download_file.exists():
            download_file.unlink()


class DetaDriveStorage(IStorage):
    """
    Storage for saving downloaded media files in Deta Drive.
    """

    def __init__(self, deta_project_key: str, drive_name: str) -> None:
        deta = Deta(project_key=deta_project_key)
        self.drive = deta.Drive(drive_name)
        # Amount of chunks read at a time by
        self.chunk_size = 1024  # in bytes

    def save_download_from_file(self, download: Download, path: Path) -> str:
        self.drive.put(download.storage_filename, path=path)
        return download.storage_filename

    def get_download(self, storage_file_name: str) -> Iterator[bytes]:
        file = self.drive.get(storage_file_name)
        if file is None:
            return file
        return file.iter_chunks(self.chunk_size)

    def remove_download(self, storage_file_name: str):
        self.drive.delete(storage_file_name)
