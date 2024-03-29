import logging
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import humanize

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
