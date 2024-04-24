from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import aiohttp
import asyncpg

from utils.item import Item

if TYPE_CHECKING:
  from typing import Union

  from asyncpg import Connection

LOG = logging.getLogger()

async def get_local(conn: Connection, upc: Union[str,int]) -> False|Item:
  record = await conn.fetchrow("SELECT * FROM Items WHERE upc=$1;", upc)
  if not record:
    return False
  return Item.from_record(record)

async def get_upc(conn: asyncpg.Connection, upc: str|int) -> False|Item:
  # First we should try to get it from local cache
  item = None
  try:
    conn: asyncpg.Connection
    LOG.info(f"[LOCAL] Getting {upc}...")
    item = await get_local(conn, upc)
  except Exception:
    LOG.exception("Local cache fail!")

  # If not, run through the handlers and try to get it from there.
  if item: 
    return item
  return False