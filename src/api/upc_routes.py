from __future__ import annotations

import tomllib
import urllib.parse
from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response
from aiohttplimiter import Limiter, default_keyfunc

from utils.get_item import get_upc
from utils.item import Item

if TYPE_CHECKING:
  from utils.extra_request import Request

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  exempt_ips = config["srv"]["ratelimit_exempt"]

limiter = Limiter(default_keyfunc, exempt_ips)

routes = web.RouteTableDef()

@routes.get("/upc/{upc:.*}")
@limiter.limit("30/minute")
async def get_upc_aiohttp(request: Request) -> Response:
  print("got request", request)
  upc = request.match_info["upc"]

  item = await get_upc(request.pool, upc)
  if item:
    return web.json_response(item.dump)
  else:
    return web.Response(status=404)

@routes.get("/upc/bulk/")
@limiter.limit("30/minute")
async def get_upc_bulk_aiohttp(request: Request) -> Response:
  upc_raw = request.query["upcs"]
  total_requested = 0
  try:
    upc_list = upc_raw.split(",")
    upc_list = list(set(upc_list))
    total_requested = len(upc_list)
  except Exception:
    return Response(status=400,body="error in parsing upc list")

  if len(upc_list) > 50:
    return Response(status=400,body="More than 50 UPCs requested!")

  records = await request.conn.fetch("SELECT * FROM Items WHERE upc = ANY($1);", upc_list) # This is horrible and I hate it.
  total_found = len(records)
  upc_dict: dict[str,str] = {}
  for record in records:
    item = Item.from_record(record)
    upc_dict[item.upc] = item.dump
  packet = {
    "requested": total_requested,
    "found": total_found,
    "items": upc_dict
  }
  return web.json_response(packet)

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
  
  response = await request.conn.execute(
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
  if response == "INSERT 0 1":
    return Response()
  else:
    print("Failed SQL",response)
    return Response(status=500)

@routes.get("/upc/search/")
async def get_upc_search(request: Request) -> Response:
  query = request.query

  search_text = query.get("s",None)
  if search_text is None:
    return Response(status=400,text="pass s parameter!")

  search_text = urllib.parse.unquote_plus(search_text)

  try:
    offset = int(query.get("offset","0"))
  except ValueError:
    return Response(status=400,text="offset must be integer!")
  try:
    limit = int(query.get("limit","50"))
  except ValueError:
    return Response(status=400,text="limit must be integer!")

  item_records = await request.conn.fetch("SELECT * FROM Items WHERE Name ILIKE $1 LIMIT $2 OFFSET $3;", f"%{search_text}%", limit, offset)
  count_record = await request.conn.fetchrow("SELECT COUNT(*) FROM Items;")
  count = count_record.get("count")

  items = [Item.from_record(record).dump for record in item_records]

  out = {
    "total": count,
    "returned": len(items),
    "items": items
  }

  return web.json_response(out)

async def setup(app: web.Application) -> None:
  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)