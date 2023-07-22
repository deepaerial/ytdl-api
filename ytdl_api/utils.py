import uuid
import logging

LOGGER = logging.getLogger()


def get_unique_id() -> str:
    return uuid.uuid4().hex
