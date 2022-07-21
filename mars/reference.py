from enum import Enum
# MODIFGEN from ..model.equipment import ReferenceI
from model.reference import ReferenceI
# MODIFGEN from ..utils import GetItemEnum
from utils import GetItemEnum

class Frame(ReferenceI):
  CELL_FRAME = 'CELL_FRAME'
  NONE = 'NONE'

  def __init__(self, reference:str):
    ReferenceI.__init__(self, reference)

class Reference(Enum, metaclass=GetItemEnum):
  FRAME = Frame

