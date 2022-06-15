from server.exceptions import ServerException
from utils import get_config_from_file, get_validation_schemas
import sys
import os
from dotenv import load_dotenv
from typing import Dict, Tuple
from server.amqp import AMQPServer, CFunction, CPipeline
from server.http import HttpServer, EFunction
from server.validation import Validator
from exceptions import BaseException, BaseExceptionType
from server.exceptions import ServerException
import logging

import model
from model.action import Action
import mars

# TODO update server code define in build_processor

load_dotenv()

# get server config file
__SERVER_CONFIG_FILE = os.getenv('SERVER_CONFIG')
__SERVER_CONFIG_FILE = __SERVER_CONFIG_FILE if __SERVER_CONFIG_FILE else './config/server.yaml'

# get mars config file
__MARS_CONFIG_FILE = os.getenv('MARS_CONFIG')
__MARS_CONFIG_FILE = __MARS_CONFIG_FILE if __MARS_CONFIG_FILE else './config/mars.yaml' 

# get validation schema directory
__VALIDATION_SCHEMA_DIR = os.getenv('VALIDATION_SCHEMA_DIR')
__VALIDATION_SCHEMA_DIR = __VALIDATION_SCHEMA_DIR if __VALIDATION_SCHEMA_DIR else './schemas'

# declare amqp topics
__AMQP_TOPICS = 'request.command_generator','report.command_generator'

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGER = logging.getLogger("cmd_generator")
logging.getLogger("pika").setLevel(logging.WARNING)

def get_http_para_from_config(http_config:Dict) -> Tuple[str, int]:
  try:
    host = http_config['host']
    port = http_config['port']
    return host, port
  except KeyError as error:
    raise BaseException(["SERVER", "HTTP"],
                        BaseExceptionType.CONFIG_NOT_CONFORM,
                        f"http server config is not conform, {error.args[0]} parameter is missing")


def build_amqp_server(amqp_config:Dict):
  try:
    host = amqp_config['host']
    port = amqp_config['port']
    exchange = amqp_config['exchange']
    ex_name = exchange['name']
    ex_type = exchange['type']

    amqp_server = AMQPServer(name="command_generator",
                            host=host,
                            port=port,
                            exchange_name=ex_name,
                            exchange_type=ex_type)                  
    return amqp_server

  except KeyError as error:
    missing_key = error.args[0]
    raise BaseException(['CONFIG', 'SERVER', 'AMQP'],
                        BaseExceptionType.CONFIG_NOT_CONFORM,
                        f"the amqp configuration parameter {missing_key} is missing")

  except ServerException as error:
    error.add_in_stack(['SERVER'])
    raise error


def build_commands(body:Dict,
                   headers:Dict,
                   path:str,
                   query_args:Dict):
                   
  #get the action id from the body
  id = body.get('id')

  # extract data from database and generate an action
  action = Action.get_from_db(id)

  # build a body with commands
  body = {
    "commands":action.get_commands()
  }
  return body, headers

def build_validator(schemas_dict:Dict)-> Validator:
  # instanciate validator to validate request 
  validator = Validator()
  # add all schemas in the validation object
  for path, schema in schemas_dict.items():
    validator.add_schema(path, schema)
  
  return validator

def main():

  AMQP_SERVER:AMQPServer = None
  HTTP_SERVER:HttpServer = None
  
  # read the configurations
  LOGGER.info("read configurations")
  SERVER_CONFIG = get_config_from_file(__SERVER_CONFIG_FILE)
  MARS_CONFIG = get_config_from_file(__MARS_CONFIG_FILE)
  
  # get server configurations
  amqp_config:Dict = SERVER_CONFIG.get('amqp')
  http_config:Dict = SERVER_CONFIG.get('http')

  # get validations schemas stored in __VALIDATION_SCHEMA_DIR
  schemas_dict = get_validation_schemas(__VALIDATION_SCHEMA_DIR)
  # build the validator object
  request_validator = build_validator(schemas_dict)

  # load mars environment
  LOGGER.info("load mars environment")
  model.EQUIPMENT, model.REFERENCE, model.COMMAND_REGISTER, model.DB_DRIVER = mars.build_environment(MARS_CONFIG)


  # if amqp server configuration is defined and if parameter activate == true
  if amqp_config and amqp_config.get('activate'):
    LOGGER.info("build amqp server")
    AMQP_SERVER = build_amqp_server(amqp_config)

    LOGGER.info('configure amqp server')
    AMQP_SERVER.add_queue(label="request_report",
                          topics=__AMQP_TOPICS)
    

    # prepare a consumer pipeline
    # no topic parameter for publish => report_topic contained in the message header
    req_pipeline = CPipeline([CFunction(build_commands),
                              CFunction(AMQP_SERVER.publish)])
    
    AMQP_SERVER.add_consumer('request.command_generator', req_pipeline)
  
  if http_config and http_config.get('activate'):
    # http server configuration - not implemented yet
    # TODO implement http_server and run
    LOGGER.info("build http server")
    HTTP_HOST, HTTP_PORT = get_http_para_from_config(http_config)
    HTTP_SERVER = HttpServer("command_generator", request_validator)

    LOGGER.info("configure http server")
    HTTP_SERVER.add_endpoint('/commands/generate',
                             'approach',
                             EFunction(build_commands),
                             methods=['GET'])

  if not HTTP_SERVER and not AMQP_SERVER:
    raise BaseException(['CONFIG', 'SERVER'],
                        BaseExceptionType.CONFIG_NOT_CONFORM,
                        "no server activated, check the configuration")
  
  if HTTP_SERVER:
    LOGGER.info('run http server and wait for messages')
    # http_server run on new tread - not implemented yet
    HTTP_SERVER.run(HTTP_HOST, HTTP_PORT)

  if AMQP_SERVER:
    # run amqp server on the current tread
    LOGGER.info('run amqp server and wait for messages')
    AMQP_SERVER.run()
  
if __name__ == '__main__':
  try:
    LOGGER.info("run command_generator service")
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    main()
  except BaseException as error:
    LOGGER.fatal(error.describe())
    sys.exit(1)
  except KeyboardInterrupt as error:
    LOGGER.info("manual interruption of the program")
    sys.exit(1)