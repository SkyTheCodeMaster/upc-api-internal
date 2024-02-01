from __future__ import annotations

import asyncio
import datetime
import logging
import tomllib
from typing import TYPE_CHECKING

import aiofiles

if TYPE_CHECKING:
  from aiohttp import ClientSession
  from asyncpg import Connection

LOG = logging.getLogger(__name__)

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  URL: str = config["backup"]["url"]
  API_KEY: str = config["backup"]["api_key"]
  BACKUP_COMMAND: str = config["backup"]["backup_command"]
  PG_URL: str = config["postgres"]["url"]
  PG_PASS: str = config["postgres"]["password"]
  BACKUP_COMMAND: str = BACKUP_COMMAND.format(url=PG_URL, password=PG_PASS)

async def file_sender(file_name=None):
  async with aiofiles.open(file_name, 'rb') as f:
    chunk = await f.read(64*1024)
    while chunk:
      yield chunk
      chunk = await f.read(64*1024)

async def backup_task(cs: ClientSession, conn: Connection) -> str|False:
  "Backup the items db as a CSV to the paste server."
  # we need to get the items first into a csv.
  try:
    proc = await asyncio.subprocess.create_subprocess_shell(BACKUP_COMMAND)
    await proc.communicate() # This supposedly waits for the process to finish.
    # Now we have our CSV file to POST to the paste server.
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d_%H:%M")
    query = {
      "title": f"UPC Backup {current_date}",
      "visibility": 2,
      "folder": "UPC Backups",
      "syntax": "plaintext"
    }
    headers = {
      "Authorization": API_KEY
    }

    async with cs.post(URL, params=query, headers=headers, data=file_sender(file_name="/tmp/upc_database_export.csv")) as resp:
      if resp.status == 200:
        paste_id = await resp.text()
        # good, now we should push this ID into the database.
        await conn.execute("INSERT INTO Backups (PasteID, Date) VALUES ($1, $2);", paste_id, int(now.timestamp()))
        LOG.info("Completed backup")
        return paste_id
      else:
        LOG.error("Failed to upload database backup!")
        LOG.error(f"HTTP{resp.status}: {await resp.text()}")
  except Exception:
    LOG.exception("Backup failed!")
    return False