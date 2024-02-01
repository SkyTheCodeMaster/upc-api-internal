from __future__ import annotations

import asyncio
import logging

import aiohttp
import asyncpg

from handlers import upcdatabase_get, nutritionix_get, upcitemdb_get, goupc_get, local_get
from utils.item import Item

LOG = logging.getLogger()

async def get_upc(pool: asyncpg.Pool, cs: aiohttp.ClientSession, upc: str|int, *, local_only: bool = False) -> False|Item:
  handlers = [
    upcdatabase_get,
    nutritionix_get,
    upcitemdb_get,
    goupc_get,
  ]

  # First we should try to get it from local cache
  item = None
  try:
    async with pool.acquire() as conn:
      conn: asyncpg.Connection
      LOG.info(f"[LOCAL] Getting {upc}...")
      item = await local_get(conn, upc)
  except Exception:
    LOG.exception("Local cache fail!")

  # If not, run through the handlers and try to get it from there.
  if item: 
    return item
  if local_only: 
    return False
  for handler in handlers:
    try:
      LOG.info(f"[EXTERNAL] Attempting to get {upc} from {handler.__name__}...")
      async def _get_item():
        item = await handler(cs, upc)
      task = asyncio.create_task(_get_item())
      await asyncio.wait_for(task, timeout=1.0)
      if item: 
        break
    except Exception:
      LOG.exception(f"{handler.__name__} fail!")

  if item:
    # We're gonna try to insert into the database
    try:
      async with pool.acquire() as conn:
        await conn.execute(
          """
            INSERT INTO
              Items (upc, name, quantity, quantityunit)
            VALUES
              ($1, $2, $3, $4)
            ON CONFLICT (upc)
            DO
              UPDATE SET
                name = $2,
                quantity = $3,
                quantityunit = $4;
            """,
          item.upc,
          item.name,
          item.quantity,
          item.quantity_unit
        )
    except Exception:
      LOG.exception("[DB INSERT] Failed!")

    return item
  return False