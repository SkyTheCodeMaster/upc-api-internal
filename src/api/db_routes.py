from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response
from aiohttplimiter import Limiter, default_keyfunc
from handlers.local import get_local

from get_item import get_upc
from utils.upc import convert_upce, validate_upca

if TYPE_CHECKING:
  from utils.extra_request import Request

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  exempt_ips = config["srv"]["ratelimit_exempt"]

limiter = Limiter(default_keyfunc, exempt_ips)

routes = web.RouteTableDef()

# Return total item count, total backup count.
@routes.get("/database/get/")
async def get_database_get(request: Request) -> Response:
  item_count_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Items;")
  backup_count_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Backups;")
  
  packet = {
    "items": item_count_record.get("count",-1),
    "backups": backup_count_record.get("count",-1),
  }

  return web.json_response(packet)

def setup() -> web.RouteTableDef:
  return routes