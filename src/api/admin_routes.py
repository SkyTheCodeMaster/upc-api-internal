from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response

from utils.auth import verify
from utils.backup import backup_task

if TYPE_CHECKING:
  from utils.extra_request import Request

routes = web.RouteTableDef()

@routes.post("/api/admin/backup/")
async def post_api_admin_backup(request: Request) -> Response:
  if not await verify(request):
    return web.Response(status=403)

  result = await backup_task(request.session, request.conn)
  return web.Response(status=200 if result else 500)

def setup() -> web.RouteTableDef:
  return routes