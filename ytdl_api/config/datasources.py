from confz import BaseConfig
from pydantic import root_validator

from ..datasource import DetaDB, IDataSource


class DetaBaseDataSourceConfig(BaseConfig):
    """
    Deta Base DB datasource config.
    """

    key: str
    base: str

    def get_datasource(self) -> IDataSource:
        return DetaDB(self.key, self.base)

    def __hash__(self):  # make hashable BaseModel subclass  # pragma: no cover
        attrs = tuple(attr if not isinstance(attr, list) else ",".join(attr) for attr in self.__dict__.values())
        return hash((type(self),) + attrs)


class DataSourceConfig(BaseConfig):
    """
    Datasource config.
    """

    deta: DetaBaseDataSourceConfig | None = None

    def get_datasource(self) -> IDataSource:
        return self.deta.get_datasource()

    @root_validator
    def validate_datasources(cls, values):
        if not any(values.values()):
            raise ValueError("No datasource config provided.")
        return values

    def __hash__(self):  # make hashable BaseModel subclass  # pragma: no cover
        attrs = tuple(hash(attr) for attr in self.__dict__.values())
        return hash((type(self),) + attrs)
