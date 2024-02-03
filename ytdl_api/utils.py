import uuid
import re
from pathlib import Path
import humanize
import logging

from urllib.parse import quote


LOGGER = logging.getLogger("uvicorn")

PROGRESS_PATTERN = re.compile(r"(\d+.?\d+)?%")


def get_unique_id() -> str:
    return uuid.uuid4().hex


def extract_percentage_progress(progress_string: str) -> int:
    """
    Extracts percentage progress from string.
    """

    return round(float(PROGRESS_PATTERN.search(progress_string).group(1)))


def get_file_size(file_path: Path) -> (int, str):
    """
    Return file in bytes and human readable file size string.
    """
    filesize_in_bytes = file_path.stat().st_size
    return filesize_in_bytes, humanize.naturalsize(filesize_in_bytes)


def get_content_disposition_header_value(filename: str) -> str:
    """
    Helper function to add file name to StreamingResponse response class.
    Copied from fastapi.responses.FileResponse __init__ method.
    """
    content_disposition_type: str = "attachment"
    content_disposition_filename = quote(filename)
    if content_disposition_filename != filename:
        content_disposition = "{}; filename*=utf-8''{}".format(
            content_disposition_type, content_disposition_filename
        )
    else:
        content_disposition = '{}; filename="{}"'.format(
            content_disposition_type, filename
        )
    return content_disposition
