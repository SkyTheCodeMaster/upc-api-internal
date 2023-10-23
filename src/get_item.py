from __future__ import annotations

import logging

import aiohttp
import asyncpg

from handlers import *
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
      LOG.info(f"[LOCAL] Getting {upc}...")
      item = await local_get(conn, upc)
  except:
    LOG.exception("Local cache fail!")

  # If not, run through the handlers and try to get it from there.
  if item: return item
  if local_only: return False
  for handler in handlers:
    try:
      LOG.info(f"[EXTERNAL] Attempting to get {upc} from {handler.__name__}...")
      item = await handler(cs, upc)
      if item: break
    except:
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
    except:
      LOG.exception("[DB INSERT] Failed!")

    return item
  return False