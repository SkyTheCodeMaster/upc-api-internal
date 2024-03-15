from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from utils.item import Item

"GO UPC BANS AFTER 100 QUERIES"

if TYPE_CHECKING:
  from typing import Union
  from bs4 import Tag

  from aiohttp import ClientSession

async def get_goupc(cs: ClientSession, upc: Union[str,int]) -> False|Item:
  url = f"https://go-upc.com/search?q={upc}"

  async with cs.get(url) as resp:
    # We need to process the raw html. Yikes lol

    html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    if "Sorry, we were not able to find a product for" in soup.get_text():
      return False

    # Extract all the table rows
    name: Tag = soup.find_all("h1", {"class":"product-name"})[0]

    i = Item(
      upc = upc,
      name = name.get_text()
    )

    return i