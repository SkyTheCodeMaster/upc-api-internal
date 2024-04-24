from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response
from aiohttplimiter import Limiter, default_keyfunc

if TYPE_CHECKING:
  from utils.extra_request import Request

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  exempt_ips = config["srv"]["ratelimit_exempt"]
  frontend_version = config["pages"]["frontend_version"]
  api_version = config["srv"]["api_version"]

limiter = Limiter(default_keyfunc, exempt_ips)

routes = web.RouteTableDef()

# Return total item count, total backup count.
@routes.get("/database/get/")
async def get_database_get(request: Request) -> Response:
  item_count_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Items;")
  database_size_record = await request.conn.fetchrow("SELECT pg_size_pretty ( pg_database_size ( current_database() ) );")
  
  packet = {
    "items": item_count_record.get("count",-1),
    "frontend_version": frontend_version,
    "api_version": api_version,
    "db_size": database_size_record.get("pg_size_pretty","-1 kB")
  }

  return web.json_response(packet)

async def setup(app: web.Application) -> None:
  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)