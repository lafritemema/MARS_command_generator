# MODIFGEN from ..model.equipment import EquipmentI
from model.equipment import EquipmentI
# MODIFGEN from ..utils import GetItemEnum
from utils import GetItemEnum
from enum import Enum

class Effector(EquipmentI):
  WEB_C_DRILLING = 'WEB_C_DRILLING'
  FLANGE_C_DRILLING = 'FLANGE_C_DRILLING'
  NONE = 'NONE'
  
  def __init__(self, reference:str):
    EquipmentI.__init__(self, reference)

class Equipment(Enum, metaclass=GetItemEnum):
  EFFECTOR = Effector
