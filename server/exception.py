from dataclasses import MISSING
from http.client import NOT_IMPLEMENTED
from prometheus_client import Enum
from exception import BaseException
from enum import Enum
from typing import List

class ServerExceptionType(Enum):
  CONNECTION_ERROR = 'SERVER_CONNECTION_ERROR'
  MISSING_ELEMENT = 'SERVER_MISSING_ELEMENT'
  INVALID_MESSAGE = 'SERVER_INVALID_MESSAGE_RECEIVED'
  NOT_IMPLEMENTED = 'SERVER_SERVICE_NOT_IMPLEMENTED'
  INTERNAL_ERROR = 'SERVER_INTERNAL_ERROR'

class ServerException(BaseException):
  def __init__(self, origin_stack:List[str],
               _type:ServerExceptionType,
               description:str):
    super().__init__(origin_stack, _type, description)