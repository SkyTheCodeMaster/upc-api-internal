from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp.web import middleware

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
    resp = await handler(request)
    return resp