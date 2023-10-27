from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

from aiohttp import web

from utils.auth import verify
from utils.backup import backup_task

if TYPE_CHECKING:
  from aiohttp import ClientSession
  from asyncpg import Connection, Pool

admin_routes = web.RouteTableDef()

@admin_routes.post("/api/admin/backup/")
async def post_api_admin_backup(request: web.Request) -> web.Response:
  if not await verify(request):
    return web.Response(status=403)
  pool: Pool = request.app.pool
  cs: ClientSession = request.app.cs
  async with pool.acquire() as conn:
    result = await backup_task(cs, conn)
    return web.Response(status=200 if result else 500)