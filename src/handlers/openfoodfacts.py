from __future__ import annotations

from typing import TYPE_CHECKING

from utils.item import Item

if TYPE_CHECKING:
  from typing import Union

  from aiohttp import ClientSession

async def get_openfoodfacts(cs: ClientSession, upc: Union[str,int]) -> False|Item:
  url = f"https://world.openfoodfacts.net/api/v2/product/{upc}"

  async with cs.get(url) as resp:
    # We need to process the raw html. Yikes lol

    data = await resp.json()
    if data.get("status",0) != 1:
      return False

    product_info = data.get("product")
    product_name = product_info.get("product_name")
  

    i = Item(
      upc = upc,
      name = product_name
    )

    return i