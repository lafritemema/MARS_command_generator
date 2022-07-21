
from enum import EnumMeta, Enum
from functools import partial

  
class EquipmentI(Enum):
  def __init__(self, reference:str):
    self.__reference = reference
  
  @property
  def type(self)->str:
    return self.__class__.__name__.upper()

  @property
  def reference(self)->str:
    return self.__reference

def load(equipment:EquipmentI):
  return {
    'operation': 'LOAD',
    'equipment': {
      'type':equipment.type,
      'reference': equipment.reference
    }
  }

def unload(equipment:EquipmentI):
  return {
    'operation': 'UNLOAD',
    'equipment': {
      'type': equipment.type,
      'reference': equipment.reference
    }
  }

class Operation(Enum):
  
  LOAD = partial(load)
  UNLOAD = partial(unload)

  def apply_on(self, equipement:EquipmentI):
    fct = self.value
    return fct(equipement)



  