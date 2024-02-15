# ruff: noqa: F401

from .goupc import get_goupc as goupc_get
from .local import get_local as local_get
from .nutritionix import get_nutritionix as nutritionix_get
from .upcdatabase import get_upcdatabase as upcdatabase_get
from .upcitemdb import get_upcitemdb as upcitemdb_get

all_handlers = [
  goupc_get,
  nutritionix_get,
  upcdatabase_get,
  upcitemdb_get
]