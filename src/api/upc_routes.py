from __future__ import annotations

import math
import datetime
import tomllib
from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response
from aiohttplimiter import Limiter, default_keyfunc
from handlers.local import get_local

from asyncpg.exceptions import UniqueViolationError
from utils.get_item import get_upc
from utils.upc import convert_upce, validate_upca
from utils.item import Item

if TYPE_CHECKING:
  from utils.extra_request import Request

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  exempt_ips = config["srv"]["ratelimit_exempt"]

limiter = Limiter(default_keyfunc, exempt_ips)

routes = web.RouteTableDef()

@routes.get("/upc/{upc:\d+}")
@limiter.limit("30/minute")
async def get_upc_aiohttp(request: Request) -> Response:
  
  upc = request.match_info["upc"]
  converted = False
  if len(str(upc)) == 8:
    converted=True
    upc = convert_upce(upc)

  if not validate_upca(upc):
    return web.Response(status=400,body=f"Invalid UPC-A.;Converted:{converted}")

  item = await get_upc(request.pool, request.session, upc)
  if item:
    return web.json_response(item.dump)
  else:
    timestamp = math.floor(datetime.datetime.utcnow().timestamp())
    try:
      await request.conn.execute("""INSERT INTO Misses (UPC, Converted, Date) VALUES ($1, $2, $3);""", upc, converted, timestamp)
    except UniqueViolationError:
      pass # This doesn't matter.
    return web.Response(status=404)

@routes.get("/upc/list/")
@limiter.limit("30/minute")
async def get_upc_list(request: Request) -> Response:
  query = request.query

  try:
    offset = int(query.get("offset","0"))
  except ValueError:
    return Response(status=400,text="offset must be integer!")
  try:
    limit = int(query.get("limit","50"))
  except ValueError:
    return Response(status=400,text="limit must be integer!")

  item_records = await request.conn.fetch("SELECT * FROM Items LIMIT $1 OFFSET $2;", limit, offset)
  items = [Item.from_record(record).dump for record in item_records]
  count_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Items;")
  count = count_record.get("count")

  out = {
    "total": count,
    "returned": len(items),
    "items": items
  }

  return web.json_response(out)
  
@routes.post("/upc/")
@limiter.limit("10/minute")
async def post_upc(request: Request) -> Response:
  if not request.app.config["api"]["uploading"]["enabled"]:
    return web.Response(status=403,text="Uploading disabled.")

  data: dict = await request.json()
  if "upc" not in data:
    return web.Response(status=400,body="upc not passed")
  upc = data["upc"]
  converted = False
  if len(str(upc)) == 8:
    converted=True
    upc = convert_upce(upc)
  if not validate_upca(upc):
    return web.Response(status=400,body=f"Invalid UPC-A.;Converted:{converted}")
  
  local_item = await get_local(request.conn, data["upc"])
  if local_item:
    await request.conn.execute(
      """
        INSERT INTO
          Items (upc, name, quantity, quantityunit)
        VALUES
          ($1, $2, $3, $4)
        ON CONFLICT (upc)
        DO
          UPDATE SET
            name = $2,
            quantity = $3,
            quantityunit = $4;
        """,
      data["upc"],
      data.get("name", local_item.name),
      data.get("quantity", local_item.quantity),
      data.get("quantity_unit", local_item.quantity_unit)
    )
    return web.Response(status=200)
  else:
    await request.conn.execute(
      """
        INSERT INTO
          Items (upc, name, quantity, quantityunit)
        VALUES
          ($1, $2, $3, $4)
        ON CONFLICT (upc)
        DO
          UPDATE SET
            name = $2,
            quantity = $3,
            quantityunit = $4;
        """,
      data["upc"],
      data.get("name", None),
      data.get("quantity", None),
      data.get("quantity_unit", None)
    )
    return web.Response(status=200)

@routes.get("/validate/{upc:.*}")
async def get_validate(request: web.Request) -> web.Response:
  upc = request.match_info["upc"]
  converted = False
  try:
    if len(str(upc)) == 8:
      converted=True
      upc = convert_upce(upc)
    valid = validate_upca(upc)
  except Exception:
    valid = False

  packet = {
    "ok": valid,
    "converted": converted
  }

  return web.json_response(packet)

@routes.get("/upc/misses/")
async def get_upc_misses(request: Request) -> Response:
  query = request.query

  try:
    offset = int(query.get("offset","0"))
  except ValueError:
    return Response(status=400,text="offset must be integer!")
  try:
    limit = int(query.get("limit","50"))
  except ValueError:
    return Response(status=400,text="limit must be integer!")

  miss_records = await request.conn.fetch("SELECT * FROM Misses LIMIT $1 OFFSET $2;", limit, offset)
  misses = [
    {
      "upc": record.get("upc"),
      "converted": record.get("converted"),
      "date": datetime.datetime.fromtimestamp(record.get("date",0)).strftime("%Y/%m/%d-%H:%M:%S")
    } for record in miss_records
  ]
  count_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Misses;")
  count = count_record.get("count")

  out = {
    "total": count,
    "returned": len(misses),
    "misses": misses
  }

  return web.json_response(out)

async def setup(app: web.Application) -> None:
  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)