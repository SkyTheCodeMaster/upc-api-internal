from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from asyncpg import Record

class Item:
  upc: str # This is a string because sometimes the UPCs have leading 0s.
  name: str
  quantity: str
  quantity_unit: str

  def __init__(self,*,
               upc: str = None,
               name: str = None,
               quantity: str = None,
               quantity_unit: str = None) -> None:
    self.upc = upc
    self.name = name
    self.quantity = quantity
    self.quantity_unit = quantity_unit

  @classmethod
  def from_record(cls, record: Record):
    return cls(
      upc=record["upc"],
      name=record["name"],
      quantity=record["quantity"],
      quantity_unit=record["quantityunit"]
    )
  
  @property
  def dump(self) -> str:
    return {
      "upc": self.upc,
      "name": self.name,
      "quantity": self.quantity,
      "quantity_unit": self.quantity_unit
    }
  
  def __str__(self) -> str:
    return f"<Item upc={self.upc} name='{self.name}' size: {self.quantity}{self.quantity_unit}>"