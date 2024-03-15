from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from utils.item import Item
from utils.size import split_size

if TYPE_CHECKING:
  from typing import Union

  from aiohttp import ClientSession

async def get_upcdatabase(cs: ClientSession, upc: Union[str,int]) -> False|Item:
  url = f"https://www.upcdatabase.com/item/{upc}"

  async with cs.get(url) as resp:
    # We need to process the raw html. Yikes lol

    html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    if "The UPC you were looking for currently has no record in the database." in soup.get_text():
      return False

    # Extract all the table rows
    rows = soup.find_all("tr")

    # Now we need to sort it out and find the "Description" and "Size/Weight" row
    name = None
    size = None

    for row in rows:
      text = row.getText()
      if "Description" in text:
        name = text.removeprefix("Description")
      elif "Size/Weight" in text:
        size = text.removeprefix("Size/Weight")
      if name is not None and size is not None:
        # We've found both, stop.
        break

    try:
      quantity,quantity_name = split_size(size)
    except Exception:
      quantity,quantity_name = None,None
      
    i = Item(
      upc = upc,
      name = name,
      quantity = quantity,
      quantity_unit = quantity_name
    )

    return i