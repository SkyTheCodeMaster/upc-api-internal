# ruff: noqa: F401

from .goupc import get_goupc
from .local import get_local
from .nutritionix import get_nutritionix
from .upcdatabase import get_upcdatabase
from .upcitemdb import get_upcitemdb
from .openfoodfacts import get_openfoodfacts

all_handlers = [
  get_openfoodfacts,
  get_goupc,
  get_nutritionix,
  get_upcdatabase,
  get_upcitemdb
]