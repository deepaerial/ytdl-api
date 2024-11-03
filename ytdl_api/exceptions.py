from http.client import RemoteDisconnected
from logging import Logger

from fastapi.requests import Request
from pytube.exceptions import AgeRestrictedError, RegexMatchError, VideoPrivate
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_500_INTERNAL_SERVER_ERROR
from yt_dlp.utils import DownloadError


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


ERROR_HANDLERS = (
    (RemoteDisconnected, on_remote_disconnected),
    (AgeRestrictedError, on_pytube_agerestricted_error),
    (RegexMatchError, on_pytube_regexmatch_error),
    (VideoPrivate, on_pytube_videoprivate_error),
    (DownloadError, yt_dlp_exception_handler),
    (Exception, on_default_exception_handler),
)
