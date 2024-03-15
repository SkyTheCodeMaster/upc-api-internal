from __future__ import annotations

import logging
import tomllib
from typing import TYPE_CHECKING

from utils.item import Item

"POOR RATELIMIT HANDLING"

if TYPE_CHECKING:
  from typing import Union

  from aiohttp import ClientSession

LOG = logging.getLogger(__name__)

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  app_id = config["data-source"] ["nutritionix"]["app_id"]
  app_key = config["data-source"]["nutritionix"]["app_key"]

async def get_nutritionix(cs: ClientSession, upc: Union[str,int]) -> False|Item:
  headers = {
    "x-app-id": app_id,
    "x-app-key": app_key
  }
  processed = str(upc).removeprefix("0")
  url = f"https://trackapi.nutritionix.com/v2/search/item?upc={processed}"

  async with cs.get(url, headers=headers) as resp:
    data = await resp.json()
    if "message" in data and data["message"] == "resource not found":
      return False
    if "message" in data and data["message"] == "usage limits exceeded":
      LOG.error("[Nutritionix] Usage limits exceeded!")
      return False
    
    food = data["foods"][0]
    i = Item(
      upc=str(upc),
      name=food["food_name"]
    )
    return i