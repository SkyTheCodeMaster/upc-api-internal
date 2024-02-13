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

@routes.get("/api/upc/{upc:\d+}")
@limiter.limit("30/minute")
async def get_api_upc(request: Request) -> Response:
  
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
    return web.Response(status=404)
  
@routes.post("/api/upc/")
@limiter.limit("10/minute")
async def post_api_upc(request: Request) -> Response:
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

@routes.get("/api/validate/{upc:.*}")
async def get_api_validate(request: web.Request) -> web.Response:
  upc = request.match_info["upc"]
  converted = False
  try:
    if len(str(upc)) == 8:
      converted=True
      upc = convert_upce(upc)
    valid = validate_upca(upc)
  except:
    valid = False

  packet = {
    "ok": valid,
    "converted": converted
  }

  return web.json_response(packet)

def setup() -> web.RouteTableDef:
  return routes