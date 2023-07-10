import asyncio
import typing
from collections import defaultdict

from .schemas.models import DownloadStatusInfo


class NotificationQueue:
    queues: typing.Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

    async def get(self, client_id: str) -> DownloadStatusInfo:
        queue = self.queues[client_id]
        return await queue.get()

    async def put(self, client_id: str, download_progress: DownloadStatusInfo):
        queue = self.queues[client_id]
        return await queue.put(download_progress)
