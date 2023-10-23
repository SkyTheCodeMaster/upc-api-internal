from __future__ import annotations

from typing import TYPE_CHECKING

from utils.item import Item

if TYPE_CHECKING:
  from typing import Union

  from aiohttp import ClientSession

async def get_upcitemdb(cs: ClientSession, upc: Union[str,int]) -> False|Item:
  url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={upc}"

  async with cs.get(url) as resp:
    # We need to process the raw html. Yikes lol
    data = await resp.json()
    if data["code"] != "OK" or data["total"] == 0:
      return False
    
    item = data["items"][0]
    name = item["title"]
    i = Item(
      upc = upc,
      name = name
    )

    return i