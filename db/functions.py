
from enum import Enum

from attr import has
from .driver import DBDriver
from .mongodb import MongoDriver
from db.exception import DBDriverException, DBExceptionType
from utils import GetItemEnum
from typing import Dict
from functools import partial


class DBType(Enum, metaclass=GetItemEnum):
  """Enumeration to list all database type supported

  Args:
      Enum (DBDriver): DBDriver object associated to the database type
  """
  MONGODB = MongoDriver

def build_driver(db_config:Dict) -> DBDriver:
  """function to build a database driver from a database configuration
     raise a DBDriverException if
     - the configuration is not conform
     - the database is not reachable
     - the database element not exist
  Args:
      db_config (Dict): database configuration

  Raises:
      DBDriverException: Exception object

  Returns:
      DBDriver: Object ot communicate with the database
  """
  try:
    # get the database type from config
    db_type = db_config['type']
    # check if type is supported
    assert(hasattr(DBType, db_type))
    
    #get the Driver class associated to the type
    driver_class:DBDriver = DBType[db_type]

    # return the builded driver
    return driver_class.build_from_config(db_config)

  except AssertionError:
    # raise if type not supported
    raise DBDriverException(["DBDRIVER", "IDENTIFY"],
                              DBExceptionType.UNKNOW_TYPE,
                              f"the database type {db_type} is not supported yet")
  except KeyError as error:
    # raise if bad configuration
    missing_para = error.args[0]
    raise DBDriverException(["DBDRIVER"],
                            DBExceptionType.CONFIG_ERROR,
                            f"the parameter {missing_para} is missing in the configuration")
  