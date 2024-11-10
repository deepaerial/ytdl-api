from http.client import RemoteDisconnected
from logging import Logger

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from pytube.exceptions import AgeRestrictedError, RegexMatchError, VideoPrivate
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from yt_dlp.utils import DownloadError

from .types import YOUTUBE_REGEX


def make_internal_error(
    error_code: str = "internal-server-error",
    detail: str = "Remote server encountered problem, please try again...",
    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    return JSONResponse(
        {
            "detail": detail,
            "code": error_code,
        },
        status_code=status_code,
    )


async def on_default_exception_handler(logger: Logger, request: Request, exc: Exception):
    logger.exception(exc)
    return make_internal_error()


async def on_remote_disconnected(logger: Logger, request: Request, exc: RemoteDisconnected):
    logger.exception(exc)
    return make_internal_error("external-service-network-error")


async def on_pytube_agerestricted_error(logger: Logger, request: Request, exc: AgeRestrictedError):
    logger.exception(exc)
    return make_internal_error(
        "age-restricted-content",
        "Content is age restricted. Unable to download",
        HTTP_401_UNAUTHORIZED,
    )


async def on_pytube_regexmatch_error(logger: Logger, request: Request, exc: RegexMatchError):
    logger.exception(exc)
    return make_internal_error(
        "downloader-error",
        "Downloader encountered error. Please try again later or contact administrator",
        HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def on_pytube_videoprivate_error(logger: Logger, request: Request, exc: VideoPrivate):
    logger.exception(exc)
    return make_internal_error(
        "private-video",
        "Video is private. Unable to download",
        HTTP_403_FORBIDDEN,
    )


async def yt_dlp_exception_handler(logger: Logger, request: Request, exc: Exception):
    logger.exception(exc)
    if "Private video" in exc.args[0]:
        return make_internal_error(
            "private-video",
            "Video is private. Unable to download",
            HTTP_403_FORBIDDEN,
        )
    elif "Sign in to confirm you’re not a bot" in exc.args[0]:
        return make_internal_error(
            "bot-verification-error",
            "Bot verification detected. Please try again later or contact administrator",
            HTTP_403_FORBIDDEN,
        )
    return make_internal_error(
        "downloader-error",
        "Downloader encountered error. Please try again later or contact administrator",
        HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def validation_exception_handler(logger: Logger, request: Request, exc: RequestValidationError):
    # Custom exception handling for youtube video link validation just because you
    # cannot specify custom error messages in Pydantic type.
    remapped_errors = []
    for error in exc.errors():
        error_type = error["type"]
        ctx_pattern = error["ctx"].get("pattern")
        if error_type == "string_pattern_mismatch" and ctx_pattern == YOUTUBE_REGEX:
            remapped_errors.append({**error, "msg": "Bad youtube video link provided."})
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": remapped_errors, "body": exc.body}),
    )


ERROR_HANDLERS = (
    (RequestValidationError, validation_exception_handler),
    (RemoteDisconnected, on_remote_disconnected),
    (AgeRestrictedError, on_pytube_agerestricted_error),
    (RegexMatchError, on_pytube_regexmatch_error),
    (VideoPrivate, on_pytube_videoprivate_error),
    (DownloadError, yt_dlp_exception_handler),
    (Exception, on_default_exception_handler),
)
