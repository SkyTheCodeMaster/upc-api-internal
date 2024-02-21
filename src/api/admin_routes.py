from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from aiohttp.web import Response

from utils.auth import verify
from utils.backup import backup_task

if TYPE_CHECKING:
  from utils.extra_request import Request

routes = web.RouteTableDef()

@routes.post("/admin/backup/")
async def post_api_admin_backup(request: Request) -> Response:
  if not await verify(request):
    return web.Response(status=403)

  result = await backup_task(request.session, request.conn)
  return web.Response(status=200 if result else 500)

@routes.post("/admin/clearmisses/")
async def post_admin_clearmisses(request: Request) -> Response:
  if not await verify(request):
    return web.Response(status=403)
  # Go through each UPC in missed, and if it's included in the main database, remove it.
  request.LOG.info("Checking missing UPCs...")
  missing_upc_records = await request.conn.fetch("SELECT upc FROM Misses;")
  missing_upcs = [record.get("upc",None) for record in missing_upc_records]
  for missing_upc in missing_upcs:
    record_exists = await request.conn.fetchrow("SELECT EXISTS( SELECT 1 FROM Items WHERE upc=$1 );", missing_upc)
    exists = record_exists.get("exists")
    if exists:
      try:
        await request.conn.execute("DELETE FROM Misses WHERE upc=$1;", missing_upc)
        request.LOG.info(f"{missing_upc} was added to the main database! Removing it from misses.")
      except Exception:
        request.LOG.exception(f"Failed to remove {missing_upc} from misses!")

async def setup(app: web.Application) -> None:
  for route in routes:
    app.LOG.info(f"  ↳ {route}")
  app.add_routes(routes)