from enum import Enum

class ReferenceI(Enum):
  def __init__(self, reference:str) -> None:
    self.__reference = reference

  @property
  def reference(self):
    return self.__reference