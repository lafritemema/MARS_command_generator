from typing import Dict

class Command:
  def __init__(self,
               target:str,
               action:str,
               description:str,
               definition:Dict):

    self.__action = action
    self.__target = target
    self.__description = description
    self.__definition = definition

  def to_dict(self):
    return {
      'action': self.__action,
      'target': self.__target,
      'description' : self.__description,
      'definition' : self.__definition
    }
