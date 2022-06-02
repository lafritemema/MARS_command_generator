from model.equipment import EquipmentI
from enum import Enum
from utils import GetItemEnum

class Effector(EquipmentI):
  WEB_C_DRILLING = 'WEB_C_DRILLING'
  FLANGE_C_DRILLING = 'FLANGE_C_DRILLING'
  # TODO : Try to delete no effector entry
  NO_EFFECTOR = 'NO_EFFECTOR'

class Equipment(Enum, metaclass=GetItemEnum):
  EFFECTOR = Effector

