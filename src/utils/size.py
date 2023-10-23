from __future__ import annotations

import re

pattern = re.compile("^([+-]?(?:[0-9]*[.])?[0-9]+)\s*(.+)$")

def split_size(size: str) -> False|tuple[str,str]:
  "Take in an input like '2 litres' and return ('2','litre')"

  if size is None:
    raise ValueError("Size can not be None!")

  size = size.lower()
  if match := pattern.match(size):
    groups = match.groups()
    return groups
  else:
    return False