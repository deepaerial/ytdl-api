import asyncio
import logging

import pytest
from _pytest.capture import CaptureFixture
from _pytest.logging import LogCaptureFixture

from ytdl_api.utils import repeat_at


@pytest.fixture
def logger():
    return logging.getLogger("test")


@pytest.mark.asyncio
async def test_repeat_at(capsys: CaptureFixture[str]):
    """
    Simple Test Case for repeat_at
    """

    @repeat_at(cron="* * * * *", max_repetitions=3)
    async def print_hello():
        print("Hello")

    print_hello()
    await asyncio.sleep(1)
    out, err = capsys.readouterr()
    assert err == ""
    assert out == ""


@pytest.mark.asyncio
async def test_repeat_at_with_logger(caplog: LogCaptureFixture, logger: logging.Logger):
    """
    Test Case for repeat_at with logger and raising exception.
    """

    @repeat_at(cron="* * * * *", logger=logger, max_repetitions=3)
    async def print_hello():
        raise Exception("Hello")

    print_hello()
    await asyncio.sleep(60)

    captured_logs = caplog.records

    assert len(captured_logs) > 0
    assert hasattr(captured_logs[0], "exc_text")
    assert 'raise Exception("Hello")' in captured_logs[0].exc_text
