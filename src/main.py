from __future__ import annotations

import asyncio
import logging
import math
import os
import tomllib

import aiohttp
import coloredlogs
from aiohttp import web
import asyncpg
from utils.get_routes import get_module
from utils.logger import CustomWebLogger
from utils.pg_pool_middleware import pg_pool_middleware

LOGFMT = "[%(filename)s][%(asctime)s][%(levelname)s] %(message)s"
LOGDATEFMT = "%Y/%m/%d-%H:%M:%S"

handlers = [
  logging.StreamHandler()
]

with open("config.toml") as f:
  config = tomllib.loads(f.read())

if config['log']['file']:
  handlers.append(logging.FileHandler(config['log']))

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
  logger = CustomWebLogger(LOG),
  middlewares=[
    pg_pool_middleware
  ]
)
api_app = web.Application(
  logger = CustomWebLogger(LOG),
  middlewares=[
    pg_pool_middleware
  ]
)
  
async def startup():
  try:
    session = aiohttp.ClientSession()
    pool = await asyncpg.create_pool(
      config["postgres"]["url"],
      password=config["postgres"]["password"],
      max_size=250,

    )
    app.cs = session
    api_app.cs = session
    app.pool = pool
    api_app.pool = pool
    api_app.LOG = LOG
    app.LOG = LOG
    app.config = config
    api_app.config = config

    disabled_cogs: list[str] = []

    for cog in [
        f.replace(".py","") 
        for f in os.listdir("api") 
        if os.path.isfile(os.path.join("api",f)) and f.endswith(".py")
      ]:
      if cog not in disabled_cogs:
        LOG.info(f"Loading {cog}...")
        try:
          lib = get_module(f"api.{cog}")
          await lib.setup(api_app)
        except Exception:
          LOG.exception(f"Failed to load cog {cog}!")

    app.add_subapp("/api/", api_app)

    LOG.info("Loading frontend...")
    try:
      lib = get_module("frontend.routes")
      await lib.setup(app)
    except Exception:
      LOG.exception("Failed to load frontend!")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
      runner,
      config['srv']['host'],
      config['srv']['port'],
    )
    await site.start()
    print(f"Started server on http://{config['srv']['host']}:{config['srv']['port']}...\nPress ^C to close...")
    await asyncio.sleep(math.inf)
  except KeyboardInterrupt:
    pass
  except asyncio.exceptions.TimeoutError:
    LOG.error("PostgreSQL connection timeout. Check the connection arguments!")
  finally:
    try:
      await site.stop() 
    except Exception: 
      pass
    try: 
      await session.close()
    except Exception: 
      pass
    try: 
      await pool.close()
    except Exception: 
      pass

asyncio.run(startup())