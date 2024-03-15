from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp.web import middleware, Response

if TYPE_CHECKING:
  from aiohttp.web import Request
  from asyncpg import Connection

@middleware
async def pg_pool_middleware(request: Request, handler):
  async with request.app.pool.acquire() as conn:
    conn: Connection
    request.conn = conn
    request.pool = request.app.pool
    request.LOG = request.app.LOG
    request.session = request.app.cs
    resp: Response = await handler(request)
    if resp is None:
      resp = Response(status=204)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp