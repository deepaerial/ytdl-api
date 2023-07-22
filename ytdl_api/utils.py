import uuid
import re
import logging

LOGGER = logging.getLogger()

PROGRESS_PATTERN = re.compile(r"(\d+.?\d+)?%")


def get_unique_id() -> str:
    return uuid.uuid4().hex


def extract_percentage_progress(progress_string: str) -> int:
    """
    Extracts percentage progress from string.
    """

    return round(float(PROGRESS_PATTERN.search(progress_string).group(1)))
