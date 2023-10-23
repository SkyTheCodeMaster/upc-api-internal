from __future__ import annotations

from typing import TYPE_CHECKING

from utils.item import Item

if TYPE_CHECKING:
  from typing import Union

  from asyncpg import Connection

async def get_local(conn: Connection, upc: Union[str,int]) -> False|Item:
  record = await conn.fetchrow("SELECT * FROM Items WHERE upc=$1;", upc)
  if not record:
    return False
  return Item.from_record(record)