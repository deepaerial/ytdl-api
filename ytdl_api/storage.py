import abc
import shutil
from pathlib import Path
from typing import Iterator

from .schemas.models import Download


class IStorage(abc.ABC):
    """
    Base interface for storage class that manages downloaded file.
    """

    @abc.abstractmethod
    def save_download_from_file(self, download: Download, path: Path) -> str:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_download(self, storage_file_name: str) -> Iterator[bytes] | None:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def remove_download(self, storage_file_name: str):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def remove_download_batch(self, storage_file_names: list[str]):  # pragma: no cover
        raise NotImplementedError


def _read_file_at_chunks(file: Path) -> Iterator[bytes]:
    with file.open(mode="rb") as f:
        yield from f


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

    def get_download(self, storage_file_name: str) -> Iterator[bytes] | None:
        download_file = self.dowloads_dir / Path(storage_file_name)
        if not download_file.exists():
            return None
        return _read_file_at_chunks(download_file)

    def remove_download(self, storage_file_name: str):
        download_file = self.dowloads_dir / Path(storage_file_name)
        if download_file.exists():
            download_file.unlink()
        else:
            raise FileNotFoundError(f"File {download_file.as_posix()} does not exist.")

    def remove_download_batch(self, storage_file_names: list[str]):
        for storage_file_name in storage_file_names:
            self.remove_download(storage_file_name)
