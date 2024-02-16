from __future__ import annotations

import datetime
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
  backup_count_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Backups;")
  database_size_record = await request.conn.fetchrow("SELECT pg_size_pretty ( pg_database_size ( current_database() ) );")
  
  packet = {
    "items": item_count_record.get("count",-1),
    "backups": backup_count_record.get("count",-1),
    "frontend_version": frontend_version,
    "api_version": api_version,
    "db_size": database_size_record.get("pg_size_pretty","-1 kB")
  }

  return web.json_response(packet)

@routes.get("/database/backups/list/")
async def get_database_backups_list(request: Request) -> Response:
  query = request.query

  try:
    offset = int(query.get("offset","0"))
  except ValueError:
    return Response(status=400,text="offset must be integer!")
  try:
    limit = int(query.get("limit","50"))
  except ValueError:
    return Response(status=400,text="limit must be integer!")

  backup_records = await request.conn.fetch("SELECT * FROM Backups ORDER BY date DESC LIMIT $1 OFFSET $2;", limit, offset)
  backup_count_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Backups;")

  backups_out = [
    {
      "paste": record["pasteid"], 
      "date": datetime.datetime.fromtimestamp(record["date"]).strftime("%Y/%m/%d-%H:%M:%S")
    } for record in backup_records
  ]
  
  packet = {
    "total": backup_count_record.get("count",-1),
    "returned": len(backups_out),
    "backups": backups_out
  }

  return web.json_response(packet)

async def setup(app: web.Application) -> None:
  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)