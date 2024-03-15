from __future__ import annotations

import logging
import tomllib
from typing import TYPE_CHECKING

from utils.item import Item

if TYPE_CHECKING:
  from typing import Union

  from aiohttp import ClientSession

LOG = logging.getLogger(__name__)

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  KEY = config["data-source"] ["upcdatabaseorg"]["key"]

async def get_upcdatabaseorg(cs: ClientSession, upc: Union[str,int]) -> False|Item:
  headers = {
    "Authorization": f"Bearer {KEY}"
  }
  url = f"https://api.upcdatabase.org/product/{upc}"

  async with cs.get(url, headers=headers) as resp:
    data = await resp.json()

    name = data.get("title", None)
    if name is None:
      return False

    i = Item(
      upc=str(upc),
      name=name
    )
    return i