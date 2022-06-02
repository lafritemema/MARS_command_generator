import imp
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.collection import Collection, Cursor
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError
from typing import Dict

from .driver import DBDriver
from .exception import DBDriverException, DBExceptionType

MONGO_SELECTION_TIMEOUT = 10
 
def _get_database(database:str, client:MongoClient) -> Database:
  """function to get the database object
     raise an error if database not exist

  Args:
      database (str): database name
      client (MongoClient): Mongo Client

  Raises:
      DBDriverException

  Returns:
      Database: Object representing the database
  """
  try:
    # get the list of database in mongo server
    db_names = client.list_database_names()
    #check if database in listif not raise error
    assert(database in db_names)
    return client.get_database(database)
  except AssertionError :
    # raise if database not exist in server
    raise DBDriverException(['DATABASE'],
                            DBExceptionType.MISSING_ELEMENT,
                            f"the database {database} not exist in mongodb instance")
  except ServerSelectionTimeoutError:
    # raise if client not able to reach the server
    raise DBDriverException(["CLIENT"],
                            DBExceptionType.NOT_REACHABLE,
                            f"no mongo server listening on url {client.HOST}:{client.PORT}") 

def _get_collection(collection:str, database:Database) -> Collection:
  """function to get the collection object
     raise an error if collection not exist

  Args:
      database (str): collection name
      client (MongoClient): Database object

  Raises:
      DBDriverException

  Returns:
      Database: Object representing the collection
  """
  try:
    # check if collection exist in database if not raise an error
    assert(collection in database.list_collection_names())
    return database.get_collection(collection)
  except AssertionError:
    # raise if collection not exist in database 
    db_name = database.name
    raise DBDriverException(['COLLECTION'],
                            DBExceptionType.MISSING_ELEMENT,
                            f"the collection {collection} not exist in database {db_name}")

class MongoDriver(DBDriver):
  def __init__(self, host:str, port:int, database:str, collection:str):
    self.__client:MongoClient = MongoClient(host,
                                            port,
                                            serverSelectionTimeoutMS=MONGO_SELECTION_TIMEOUT)
    self.__db:Database = _get_database(database, self.__client)
    self.__collection:Collection = _get_collection(collection, self.__db)

  def find_by_id(self, id:str) -> Dict:
    """function to find a document with using its id

    Args:
        id (str): document id

    Returns:
        Dict: document found
    """
    # build the id
    _id = ObjectId(id)
    # get the document using the collection function
    document = self.__collection.find_one({'_id':_id})
    return document

  @staticmethod
  def build_from_config(config:Dict)->'MongoDriver':
    """function to build a MongoDriver object from a configuration
       config must contains following keys:
       - host
       - port
       - database
       - collection
      raise an error if config not conform or database not reachable ...
    Args:
        config (Dict): configuration of mongo driver

    Raises:
        DBDriverException:

    Returns:
        MongoDriver: Driver object for mongodb communications
    """
    try:
      # get all info from config
      mongo_host = config['host']
      mongo_port = config['port']
      mongo_db = config['database']
      mongo_coll = config['collection']

      return MongoDriver(mongo_host, mongo_port, mongo_db, mongo_coll)
    
    except DBDriverException as error:
      # raise if error during MongoDriver initialization
      error.add_in_stack(["MONGODB", "BUILD"])
      raise error

    except KeyError as error:
      # raise if info missing in configuration
      missing_para = error.args[0]
      raise DBDriverException(["MONGODB", "BUILD"],
                              DBExceptionType.CONFIG_ERROR,
                              f"mandatory parameter {missing_para} not found in the configuration")
