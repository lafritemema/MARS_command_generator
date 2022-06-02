from enum import Enum
from utils import GetItemEnum
from model.reference import ReferenceI

class Frame(ReferenceI):
  CELL_FRAME = 'CELL_FRAME'

class Reference(Enum, metaclass=GetItemEnum):
  FRAME = Frame

