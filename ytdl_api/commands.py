from datetime import timedelta
from logging import Logger

from .datasource import IDataSource
from .storage import IStorage
from .utils import get_datetime_now


def hard_remove_downloads(storage: IStorage, datasource: IDataSource, expired: timedelta, logger: Logger):
    """
    Remove all expired downloads including media files associated with them. `expired` parameter
    is a timedelta object that specifies how old download has to be to be considered as expired.
    """
    dt_now = get_datetime_now()
    expired_dt = dt_now - expired
    logger.info(f"Fetching expired downloads. Expiration date: {expired_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    downloads = datasource.fetch_downloads_till_datetime(expired_dt)
    logger.info(f"Found {len(downloads)} expired downloads.")
    storage.remove_download_batch([download.storage_filename for download in downloads])
    logger.info("Removed expired downloads from storage.")
    datasource.delete_download_batch(downloads)
    logger.info("Soft deleted expired downloads from database.")
