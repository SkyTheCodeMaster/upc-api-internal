from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
import aiocron

from utils.backup import backup_task

if TYPE_CHECKING:
  from utils.extra_request import Application
  from typing import Callable, Awaitable

def nightly(app: Application) -> Callable[[None,None], Awaitable[None]]:
  async def _inner():
    async with app.pool.acquire() as conn:
      await backup_task(app.cs, conn)

      # Go through each UPC in missed, and if it's included in the main database, remove it.
      app.LOG.info("Checking missing UPCs...")
      missing_upc_records = await conn.fetch("SELECT upc FROM Misses;")
      missing_upcs = [record.get("upc",None) for record in missing_upc_records]
      for missing_upc in missing_upcs:
        record_exists = await conn.fetchrow("SELECT EXISTS( SELECT 1 FROM Items WHERE upc=$1 );", missing_upc)
        exists = record_exists.get("exists")
        if exists:
          try:
            await conn.execute("DELETE FROM Misses WHERE upc=$1;", missing_upc)
            app.LOG.info(f"{missing_upc} was added to the main database! Removing it from misses.")
          except Exception:
            app.LOG.exception(f"Failed to remove {missing_upc} from misses!")

  return _inner


async def setup(app: web.Application) -> None:
  cron = aiocron.crontab("0 0 * * *", func=nightly(app), start=True)
  app.nightly_tasks = cron