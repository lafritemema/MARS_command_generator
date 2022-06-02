
from enum import Enum
from functools import partial

  
class EquipmentI(Enum):
  pass


def load(equipment:EquipmentI):
  return {
    'manipulation': 'LOAD',
    'equipment': {
      'type':equipment.__class__.__name__.upper(),
      'reference': equipment.value
    }
  }

def unload(equipment:EquipmentI):
  return {
    'manipulation': 'UNLOAD',
    'equipment': {
      'type': equipment.__class__.__name__.upper(),
      'reference': equipment.value
    }
  }

class Operation(Enum):
  LOAD = partial(load)
  UNLOAD = partial(unload)

  def apply_on(self, equipement:EquipmentI):
    fct = self.value
    return fct(equipement)



  