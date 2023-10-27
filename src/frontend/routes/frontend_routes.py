from __future__ import annotations

import datetime
import os
import pathlib
import tomllib

from aiohttp import web
from django import setup as django_setup
from django.conf import settings as django_settings
from django.template import Context, Engine, Template

from utils.auth import HashedBasicAuth

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  ITEMS_PAGE_SIZE = config["pages"]["items"]["page_size"]
  DATABASE_PAGE_SIZE = config["pages"]["database"]["page_size"]
  FRONTEND_VERSION = config["pages"]["frontend_version"]
  API_VERSION = config["srv"]["api_version"]

django_settings.configure()
django_setup()

NAV_CTX = Context({
  "FRONTEND_VERSION": FRONTEND_VERSION,
  "API_VERSION": API_VERSION
})

auth = HashedBasicAuth()

frontend_routes = web.RouteTableDef()

engine = Engine()
templates: dict[str,Template] = {}
sup_templates: dict[str,Template] = {}

def join(a: str, b: str) -> str:
  "Join 2 filepaths"
  return str(pathlib.Path(a).joinpath(pathlib.Path(b)))

for root, dirs, files in os.walk("frontend/templates"):
  if "supporting" in root: continue
  for file in files:
    filepath = join(root,file)
    with open(filepath,"r") as f:
      tmpl = engine.from_string(f.read())
      templates[filepath.removeprefix("frontend/templates").removeprefix("/")] = tmpl

for root, dirs, files in os.walk("frontend/templates/supporting"):
  for file in files:
    filepath = join(root,file)
    with open(filepath,"r") as f:
      tmpl = engine.from_string(f.read())
      sup_templates[filepath.removeprefix("frontend/templates/supporting").removeprefix("/")] = tmpl

count_cache = 0
count_cache_time = 0

@frontend_routes.get("/")
async def get_root(request: web.Request) -> web.Response:
  global count_cache, count_cache_time

  pool = request.app.pool

  current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
  if current_time > count_cache + 600:
    async with pool.acquire() as conn:
      count_cache = (await conn.fetchrow("SELECT count(*) FROM Items"))["count"]
      count_cache_time = current_time

  ctx_dict = {
    "navbar": sup_templates["nav/navbar.html"].render(NAV_CTX),
    "footer": sup_templates["nav/footer.html"].render(NAV_CTX),
    "item_count": count_cache
  }

  return web.Response(body=templates["index.html"].render(Context(ctx_dict)), content_type="text/html")

@frontend_routes.get("/items")
async def get_items(request: web.Request) -> web.Response:
  global count_cache, count_cache_time

  pool = request.app.pool
  page = request.query.get("page",0)

  try:
    page=int(page)
  except ValueError:
    return web.Response(status=400,body="page must be a number.")
  if (0>page):
    return web.Response(status=400,body="page must be positive.")

  offset = page*ITEMS_PAGE_SIZE

  current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

  async with pool.acquire() as conn:
    if current_time > count_cache + 30:
      # We want to keep the count more up to date here so that the correct number of pages is shown more often.
      count_cache = (await conn.fetchrow("SELECT count(*) FROM Items"))["count"]
      count_cache_time = current_time

    records = await conn.fetch("SELECT * FROM Items LIMIT $1 OFFSET $2", ITEMS_PAGE_SIZE, offset)

  total_pages = (count_cache // ITEMS_PAGE_SIZE)

  quan = lambda x,y: x if x is not None else y

  rows = [{"upc":record["upc"],"name":record["name"],"quantity":quan(record["quantity"],"Unknown"),"quantity_unit":quan(record["quantityunit"],"")} for record in records]

  ctx_dict = {
    "navbar": sup_templates["nav/navbar.html"].render(NAV_CTX),
    "footer": sup_templates["nav/footer.html"].render(NAV_CTX),
    "rows": rows,
    "current_page": page,
    "total_pages": total_pages
  }

  if 0 <= page - 1:
    ctx_dict["previous_page"] = page - 1
  if page + 1 < total_pages:
    ctx_dict["next_page"] = page + 1

  return web.Response(body=templates["items.html"].render(Context(ctx_dict)), content_type="text/html")

@frontend_routes.get("/lookup")
async def get_lookup(request: web.Request) -> web.Response:
  global count_cache, count_cache_time

  pool = request.app.pool

  current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
  if current_time > count_cache + 600:
    async with pool.acquire() as conn:
      count_cache = (await conn.fetchrow("SELECT count(*) FROM Items"))["count"]
      count_cache_time = current_time

  ctx_dict = {
    "navbar": sup_templates["nav/navbar.html"].render(NAV_CTX),
    "footer": sup_templates["nav/footer.html"].render(NAV_CTX),
    "item_count": count_cache
  }

  return web.Response(body=templates["lookup.html"].render(Context(ctx_dict)), content_type="text/html")

@frontend_routes.get("/database")
async def get_database(request: web.Request) -> web.Response:
  global count_cache, count_cache_time

  pool = request.app.pool
  page = request.query.get("page",0)

  try:
    page=int(page)
  except ValueError:
    return web.Response(status=400,body="page must be a number.")
  if (0>page):
    return web.Response(status=400,body="page must be positive.")

  offset = page*DATABASE_PAGE_SIZE

  async with pool.acquire() as conn:
    total_backups = (await conn.fetchrow("SELECT count(*) FROM Backups"))["count"]
    records = await conn.fetch("SELECT * FROM Backups ORDER BY Date DESC LIMIT $1 OFFSET $2", DATABASE_PAGE_SIZE, offset)
    db_size = (await conn.fetchrow("SELECT pg_size_pretty ( pg_database_size ($1 ) );", "upc_database"))["pg_size_pretty"]

    current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    if current_time > count_cache + 30:
      # We want to keep the count more up to date here so that the correct number of pages is shown more often.
      count_cache = (await conn.fetchrow("SELECT count(*) FROM Items"))["count"]
      count_cache_time = current_time

  total_pages = (total_backups // DATABASE_PAGE_SIZE)

  # Really weird date handling stuff
  def suffix(x):
    if len(str(x)) > 1 and str(x)[-2] == "1":
      return f"{x}th"
    elif x % 10 == 1:
      return f"{x}st"
    elif x % 10 == 2:
      return f"{x}nd"
    elif x % 10 == 3:
      return f"{x}rd"
    else:
      return f"{x}th"
  ftime = lambda fmt, t: t.strftime(fmt).replace('{S}', suffix(t.day))
  parse_date = lambda timestamp: ftime("%b {S}, %Y",datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc))

  rows = [{"id": record["pasteid"], "date": parse_date(record["date"])} for record in records]

  ctx_dict = {
    "navbar": sup_templates["nav/navbar.html"].render(NAV_CTX),
    "footer": sup_templates["nav/footer.html"].render(NAV_CTX),
    "rows": rows,
    "current_page": page,
    "total_pages": total_pages,
    "item_count": count_cache,
    "total_backups": total_backups,
    "db_size": db_size
  }

  if 0 <= page - 1:
    ctx_dict["previous_page"] = page - 1
  if page + 1 < total_pages:
    ctx_dict["next_page"] = page + 1

  return web.Response(body=templates["database.html"].render(Context(ctx_dict)), content_type="text/html")

@frontend_routes.get("/admin")
@auth.required
async def get_admin(request: web.Request) -> web.Response:
  ctx_dict = {
    "navbar": sup_templates["nav/navbar.html"].render(NAV_CTX),
    "footer": sup_templates["nav/footer.html"].render(NAV_CTX),
  }

  return web.Response(body=templates["administration.html"].render(Context(ctx_dict)), content_type="text/html")

@frontend_routes.get("/publish")
async def get_publish(request: web.Request) -> web.Response:
  ctx_dict = {
    "navbar": sup_templates["nav/navbar.html"].render(NAV_CTX),
    "footer": sup_templates["nav/footer.html"].render(NAV_CTX),
  }

  return web.Response(body=templates["publish.html"].render(Context(ctx_dict)), content_type="text/html")