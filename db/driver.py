
import abc
class DBDriver(metaclass=abc.ABCMeta):

  @classmethod
  def __subclasshook__(cls, subclass):
    return (hasattr(subclass, 'find_by_id') and 
            callable(subclass.find_by_id) or 
            NotImplemented)

  @abc.abstractstaticmethod
  def build_from_config()->'DBDriver':
    pass

  @abc.abstractmethod
  def find_by_id(self, id:str):
    raise NotImplementedError

