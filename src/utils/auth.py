from __future__ import annotations

import asyncio
import base64
import hashlib
import tomllib
from typing import TYPE_CHECKING

from aiohttp_basicauth import BasicAuthMiddleware

if TYPE_CHECKING:
  from typing import Any, Coroutine

  from aiohttp import web

with open("config.toml") as f:
  config = tomllib.loads(f.read())
  ADMIN_HASH = config["pages"]["administration"]["hash"]
  HASH_ITERS = config["pages"]["administration"]["hash_iters"]

def hash(passwd: str, username: str) -> str:
  "Returns a SHA512 hash of the password."
  salt = hashlib.sha512(username.encode()).digest()
  output_hash = hashlib.pbkdf2_hmac("sha512", passwd.encode(), salt, HASH_ITERS).hex()
  return output_hash

async def ahash(passwd: str, username: str) -> Coroutine[Any, Any, str]:
  loop = asyncio.get_running_loop()
  result = await loop.run_in_executor(None, hash, passwd, username)
  return result

def get_details(details: str) -> tuple[str,str]:
  "Take in a string, and return username,password"
  try:
    auth = base64.b64decode(details.removeprefix("Basic ")).decode()
  except:
    auth = details
  try:
    upass = auth.split(":")
    return upass[0],upass[1]
  except:
    return False,False

async def verify(request: web.Request) -> bool:
  authorization = request.headers.get("Authorization",None)
  if authorization is not None:
    username, passwd = get_details(authorization)
    print(authorization,username,passwd)
    if not username: return False
    return await ahash(passwd, username) in ADMIN_HASH
  authorization = request.cookies.get("Authorization",None)
  if authorization is not None:
    username, passwd = get_details(authorization)
    if not username: return False
    return await ahash(passwd, username) in ADMIN_HASH
  return False

class HashedBasicAuth(BasicAuthMiddleware):
  async def check_credentials(self, username: str, password: str, request: web.Request):
    # here, for example, you can search user in the database by passed `username` and `password`, etc.
    return hash(password, username) in ADMIN_HASH