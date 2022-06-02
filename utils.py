from enum import EnumMeta
from pyrsistent import b
import yaml
from exception import BaseException, BaseExceptionType
from typing import Dict

# define metaclass for enumeration access
class GetAttrEnum(EnumMeta):
  def __getattribute__(cls, name: str) :
    value = super().__getattribute__(name)
    if isinstance(value, cls):
        value = value.value
    return value
  
class GetItemEnum(EnumMeta):
  def __getitem__(self, name):
    return super().__getitem__(name).value

def get_config_from_file(yaml_file:str)-> Dict:
    try:
      with open(yaml_file, 'r') as f:
          content = f.read()
          config = yaml.load(content, Loader=yaml.Loader)
  
      return config
    except FileNotFoundError as error:
      raise BaseException(['CONFIG', "LOAD"],
                          BaseExceptionType.CONFIG_MISSING,
                          f"no such configuration file {error.filename}")
    except yaml.parser.ParserError as error:
      raise BaseException(["CONFIG", "LOAD"],
                          BaseExceptionType.CONFIG_NOT_CONFORM,
                          f"the configuration file {yaml_file} not conform : yaml format not respected")