from __future__ import annotations

import asyncio
import logging
import math
import tomllib

import aiohttp
import asyncpg
import coloredlogs
from aiohttp import web

from frontend.routes.frontend_routes import frontend_routes
from routes.admin_routes import admin_routes
from routes.api_routes import api_routes
from utils.logger import CustomWebLogger

LOGFMT = "[%(filename)s][%(asctime)s][%(levelname)s] %(message)s"
LOGDATEFMT = "%Y/%m/%d-%H:%M:%S"

with open("config.toml") as f:
  config = tomllib.loads(f.read())

handlers = [
  logging.StreamHandler()
]

if config["log"]["file"]:
  handlers.append(logging.FileHandler(config["log"]["file"]))

logging.basicConfig(
  handlers = handlers,
  format=LOGFMT,
  datefmt=LOGDATEFMT,
  level=logging.INFO,
)

coloredlogs.install(
  fmt=LOGFMT,
  datefmt=LOGDATEFMT
)

LOG = logging.getLogger(__name__)

app = web.Application(
  logger = CustomWebLogger(LOG)
)
app.add_routes(api_routes)
app.add_routes(frontend_routes)
app.add_routes(admin_routes)
  
async def startup():
  try:
    pool = await asyncpg.create_pool(
      config["postgres"]["url"],
      password=config["postgres"]["password"]
    )

    session = aiohttp.ClientSession()
    app.pool = pool
    app.cs = session
    app.config = config

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
      runner,
      config["srv"]["host"],
      config["srv"]["port"],
    )
    await site.start()
    print(f"Started server on http://{config['srv']['host']}:{config['srv']['port']}...\nPress ^C to close...")
    await asyncio.sleep(math.inf)
  except KeyboardInterrupt:
    pass
  except asyncio.exceptions.TimeoutError:
    LOG.error("PostgresQL connection timeout. Check the connection arguments!")
  finally:
    try: await site.stop() 
    except: pass
    try: await pool.close()
    except: pass
    try: await session.close()
    except: pass

asyncio.run(startup())