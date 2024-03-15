# ruff: noqa: F401

from .foodbasics import get_foodbasics
from .local import get_local
from .metro import get_metro
from .upcdatabasecom import get_upcdatabasecom
from .upcdatabaseorg import get_upcdatabaseorg
from .upcitemdb import get_upcitemdb

all_handlers = [
  get_metro, # Both name and quantity.
  get_foodbasics, # Both name and quantity.
  get_upcdatabasecom, # Sometimes quantity
  get_upcitemdb, # Only name.
  get_upcdatabaseorg, # Only name.
]