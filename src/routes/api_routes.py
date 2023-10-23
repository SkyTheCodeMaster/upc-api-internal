from __future__ import annotations

import tomllib

from aiohttp import web
from aiohttplimiter import Limiter, default_keyfunc

from get_item import get_upc
from handlers.local import get_local
from utils.upc import convert_upce, validate_upca

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  exempt_ips = config["srv"]["ratelimit_exempt"]

limiter = Limiter(default_keyfunc, exempt_ips)

api_routes = web.RouteTableDef()

@api_routes.get("/api/upc/{upc:\d+}")
@limiter.limit("30/minute")
async def get_api_upc(request: web.Request) -> web.Response:
  cs = request.app.cs
  pool = request.app.pool
  
  upc = request.match_info["upc"]
  converted = False
  if len(str(upc)) == 8:
    converted=True
    upc = convert_upce(upc)

  if not validate_upca(upc):
    return web.Response(status=400,body=f"Invalid UPC-A.;Converted:{converted}")

  item = await get_upc(pool, cs, upc)
  if item:
    return web.json_response(item.dump)
  else:
    return web.Response(status=404)
  
@api_routes.post("/api/upc/{upc:\d+}")
@limiter.limit("10/minute")
async def post_api_upc(request: web.Request) -> web.Response:
  pool = request.app.pool

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
  
  async with pool.acquire() as conn:
    local_item = await get_local(conn, data["upc"])
    if local_item:
      await conn.execute(
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
      await conn.execute(
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