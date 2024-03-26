from pathlib import Path

from confz import BaseConfig
from pydantic import root_validator, validator

from ..storage import DetaDriveStorage, IStorage, LocalFileStorage


class LocalStorageConfig(BaseConfig):
    """
    Local filesystem storage config.
    """

    path: Path

    @validator("path")
    def validate_path(cls, value):
        media_path = Path(value)
        if not media_path.exists():  # pragma: no cover
            print(f'Media path "{value}" does not exist...Creating...')
            media_path.mkdir(parents=True)
        return value

    def get_storage(self) -> IStorage:
        return LocalFileStorage(self.path)


class DetaDriveStorageConfig(BaseConfig):
    """
    Deta Drive storage config.
    """

    key: str
    drive: str

    def get_storage(self) -> IStorage:
        return DetaDriveStorage(self.key, self.drive)


class StorageConfig(BaseConfig):
    """
    Storage config.
    """

    local: LocalStorageConfig | None = None
    deta: DetaDriveStorageConfig | None = None

    def get_storage(self) -> IStorage:
        if self.deta:
            return self.deta.get_storage()
        return self.local.get_storage()

    @root_validator
    def validate_storages(cls, values):
        if not any(values.values()):
            raise ValueError("No storage config provided.")
        return values

    def __hash__(self):  # make hashable BaseModel subclass  # pragma: no cover
        attrs = tuple(hash(attr) for attr in self.__dict__.values())
        return hash((type(self),) + attrs)
