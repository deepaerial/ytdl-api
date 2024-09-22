from contextlib import asynccontextmanager
from functools import partial
from importlib.metadata import version
from pathlib import Path
from typing import Any, Literal

from confz import BaseConfig, EnvSource
from croniter import croniter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import validator
from starlette.middleware import Middleware

from .constants import DownloaderType
from .datasource import DetaDB, IDataSource
from .storage import IStorage, LocalFileStorage
from .utils import LOGGER

REPO_PATH = (Path(__file__).parent / "..").resolve()
ENV_PATH = (REPO_PATH / ".env").resolve()


class DetaBaseDataSourceConfig(BaseConfig):
    """
    Deta Base DB datasource config.
    """

    deta_key: str
    deta_base: str

    def get_datasource(self) -> IDataSource:
        return DetaDB(self.deta_key, self.deta_base)

    def __hash__(self):  # make hashable BaseModel subclass  # pragma: no cover
        attrs = tuple(attr if not isinstance(attr, list) else ",".join(attr) for attr in self.__dict__.values())
        return hash((type(self),) + attrs)


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


class Settings(BaseConfig):
    """
    Application settings config
    """

    logging_level: Literal["DEBUG", "INFO", "ERROR"] = "DEBUG"
    debug: bool = False
    docs_url: str = "/docs"
    openapi_prefix: str = ""
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = "YTDL API"
    description: str = "API for YTDL backend server."
    version: str = version("ytdl-api")
    disable_docs: bool = False
    allow_origins: list[str] = []
    cookie_samesite: str = "None"
    cookie_secure: bool = True
    cookie_httponly: bool = True

    downloader: DownloaderType = DownloaderType.PYTUBE
    datasource: DetaBaseDataSourceConfig
    storage: LocalStorageConfig

    expiration_period_in_seconds: int = 60 * 60 * 24  # 1 day in seconds
    remove_expired_downloads_task_cron: str = "0 0 * * *"  # every day at midnight

    CONFIG_SOURCES = EnvSource(
        allow_all=True,
        deny=["title", "description", "version"],
        file=ENV_PATH,
        nested_separator="__",
    )

    @property
    def downloader_version(self) -> str:
        if self.downloader == DownloaderType.PYTUBE:
            return version("pytubefix")
        if self.downloader == DownloaderType.MOCK:
            return "mock"
        return version(self.downloader.value)

    @validator("remove_expired_downloads_task_cron", pre=True)
    def validate_remove_expired_downloads_task_cron(cls, value):
        if croniter.is_valid(value):
            return value
        raise ValueError("Invalid cron expression value.")

    @validator("allow_origins", pre=True)
    def validate_allow_origins(cls, value):
        if isinstance(value, str):
            return value.split(",")
        return value

    def init_app(__pydantic_self__) -> FastAPI:
        """
        Generate FastAPI instance.
        """
        kwargs: dict[str, Any] = {
            "debug": __pydantic_self__.debug,
            "docs_url": __pydantic_self__.docs_url,
            "openapi_prefix": __pydantic_self__.openapi_prefix,
            "openapi_url": __pydantic_self__.openapi_url,
            "redoc_url": __pydantic_self__.redoc_url,
            "title": __pydantic_self__.title,
            "description": __pydantic_self__.description,
            "version": __pydantic_self__.version,
            "middleware": [
                Middleware(
                    CORSMiddleware,
                    allow_origins=__pydantic_self__.allow_origins,
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                    expose_headers=["Content-Disposition"],
                ),
            ],
        }
        if __pydantic_self__.disable_docs:
            kwargs.update({"docs_url": None, "openapi_url": None, "redoc_url": None})
        lifespan = __pydantic_self__.__get_lifespan_function__()
        app = FastAPI(**kwargs, lifespan=lifespan)
        __pydantic_self__.__setup_endpoints(app)
        __pydantic_self__.__setup_exception_handlers(app)
        LOGGER.setLevel(__pydantic_self__.logging_level)
        LOGGER.debug(f"API version: {__pydantic_self__.version}")
        return app

    def __setup_endpoints(__pydantic_self__, app: FastAPI):
        from .endpoints import router

        app.include_router(router, prefix="/api")

    def __setup_exception_handlers(__pydantic_self__, app: FastAPI):
        from .exceptions import ERROR_HANDLERS

        for error, handler in ERROR_HANDLERS:
            app.add_exception_handler(error, partial(handler, LOGGER))  # type: ignore

    def __get_lifespan_function__(__pydantic_self__):
        from .commands import remove_expired_downloads_task
        from .utils import repeat_at

        partial_remove_expired_downloads = partial(remove_expired_downloads_task, __pydantic_self__, LOGGER)
        cyclic_remove_expired_downloads_task = repeat_at(
            cron=__pydantic_self__.remove_expired_downloads_task_cron, logger=LOGGER
        )(partial_remove_expired_downloads)

        @asynccontextmanager
        async def lifespan_context(app: FastAPI):  # pragma: no cover
            cyclic_remove_expired_downloads_task()
            yield
            LOGGER.debug("Application shutdown...")

        return lifespan_context

    # In order to avoid TypeError: unhashable type: 'Settings' when overidding
    # dependencies.get_settings in tests.py __hash__ should be implemented
    def __hash__(self):  # make hashable BaseModel subclass  # pragma: no cover
        attrs = tuple(attr if not isinstance(attr, list) else ",".join(attr) for attr in self.__dict__.values())
        return hash((type(self),) + attrs)

    class Config:
        allow_mutation = True
        case_sensitive = False
