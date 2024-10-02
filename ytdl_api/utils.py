import asyncio
import logging
import re
import subprocess
import uuid
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from urllib.parse import quote

import humanize
from croniter import croniter
from starlette.concurrency import run_in_threadpool

LOGGER = logging.getLogger("uvicorn")

PROGRESS_PATTERN = re.compile(r"(\d+.?\d+)?%")


def get_unique_id() -> str:
    return uuid.uuid4().hex


def get_datetime_now() -> datetime:
    return datetime.now(UTC)


def get_epoch_now() -> int:
    return int(get_datetime_now().timestamp())


def extract_percentage_progress(progress_string: str) -> int:
    """
    Extracts percentage progress from string.
    """

    return round(float(PROGRESS_PATTERN.search(progress_string).group(1)))


def get_file_size(file_path: Path) -> tuple[int, str]:
    """
    Return file in bytes and human readable file size string.
    """
    filesize_in_bytes = file_path.stat().st_size
    return filesize_in_bytes, humanize.naturalsize(filesize_in_bytes)


def get_content_disposition_header_value(filename: str) -> str:
    """
    Helper function to add file name to StreamingResponse response class.
    Copied from starlette.responses.FileResponse __init__ method.
    """
    content_disposition_type: str = "attachment"
    content_disposition_filename = quote(filename)
    if content_disposition_filename != filename:
        content_disposition = "{}; filename*=utf-8''{}".format(content_disposition_type, content_disposition_filename)
    else:
        content_disposition = '{}; filename="{}"'.format(content_disposition_type, filename)
    return content_disposition


def get_sleep_time(cron) -> float:
    """
    This function returns the time delta between now and the next cron execution time.
    Original source code copied from
    https://github.com/priyanshu-panwar/fastapi-utilities/blob/master/fastapi_utilities/repeat/repeat_at.py
    """
    now = get_datetime_now()
    cron = croniter(cron, now)
    return (cron.get_next(datetime) - now).total_seconds()


def repeat_at(
    *,
    cron: str,
    logger: logging.Logger = None,
    raise_exceptions: bool = False,
    max_repetitions: int = None,
):
    """
    Original source code copied from
    https://github.com/priyanshu-panwar/fastapi-utilities/blob/master/fastapi_utilities/repeat/repeat_at.py
    This function returns a decorator that makes a function execute periodically as per the cron expression provided.

    :: Params ::
    ------------
    cron: str
        Cron-style string for periodic execution, eg. '0 0 * * *' every midnight
    logger: logging.Logger (default None)
        Logger object to log exceptions
    raise_exceptions: bool (default False)
        Whether to raise exceptions or log them
    max_repetitions: int (default None)
        Maximum number of times to repeat the function. If None, repeat indefinitely.

    """

    def decorator(func):
        is_coroutine = asyncio.iscoroutinefunction(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            repititions = 0
            if not croniter.is_valid(cron):
                raise ValueError("Invalid cron expression")

            async def loop(*args, **kwargs):
                nonlocal repititions
                while max_repetitions is None or repititions < max_repetitions:
                    try:
                        sleepTime = get_sleep_time(cron)
                        await asyncio.sleep(sleepTime)
                        if is_coroutine:
                            await func(*args, **kwargs)
                        else:
                            await run_in_threadpool(func, *args, **kwargs)
                    except Exception as e:
                        if logger is not None:
                            logger.exception(e)
                        if raise_exceptions:
                            raise e
                    repititions += 1

            asyncio.ensure_future(loop(*args, **kwargs))

        return wrapper

    return decorator


def __run_command(command: str | list[str], shell: bool = True) -> str:
    """
    Runs command and returns stdout.
    """
    return subprocess.run(command, shell=shell, check=True, capture_output=True, text=True).stdout.strip()


def get_po_token_verifier_from_file(po_token_file_path: Path) -> tuple[str, str]:
    """
    Reads visitorData and poToken from given file path and returns them as tuple.
    Code based on [solution](https://github.com/JuanBindez/pytubefix/issues/226#issuecomment-2355688758)
    to [issue](https://github.com/JuanBindez/pytubefix/issues/226)
    """
    po_token = __run_command(f"cat {po_token_file_path} | jq -r '.poToken'")
    visitor_data = __run_command(f"cat {po_token_file_path} | jq -r '.visitorData'")
    return visitor_data, po_token
