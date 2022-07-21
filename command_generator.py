from multiprocessing.connection import wait
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
import argparse
import model
from model.action import Action
import mars

# TODO update server code define in build_processor

load_dotenv()

__VALIDATION_SCHEMA_DIR = './schemas'
__SERVER_CONFIG_FILE = './config/server.yaml'
__MARS_CONFIG_FILE = './config/mars.yaml'

# declare amqp topics
__AMQP_TOPICS = 'request.command_generator','report.command_generator'

class ConfigLoader(argparse.Action):
  def __call__(self, parser, namespace, values, option_strings=None) -> Dict:
    try:
      if '--environment-config' in option_strings:
        return get_config_from_file(values)
      elif '--validation-schemas' in option_strings:
        assert os.path.isdir(values)
        # get validations schemas stored in __VALIDATION_SCHEMA_DIR
        return get_validation_schemas(values)
    except BaseException as error:
      error.add_in_stack(['CONFIG'])
      raise error
    except AssertionError as error:
      raise BaseException(["CONFIG", "VALIDATION_SCHEMA"],
                        BaseExceptionType.CONFIG_MISSING,
                        f"validation schema directory {values} not found") 


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
  id = body.get('uid')

  # extract data from database and generate an action
  action = Action.get_from_db(id)

  if action:
    # build a body with commands
    body = {
      "uid": action.id,
      "commands":action.get_commands()
    }
  else:
    body = {
      "uid": id,
      "commands": None
    }
    
  return body, headers

def build_validator(schemas_dict:Dict)-> Validator:
  # instanciate validator to validate request 
  validator = Validator()
  # add all schemas in the validation object
  for path, schema in schemas_dict.items():
    validator.add_schema(path, schema)
  
  return validator

def main(activated_server:str,
         server_config:str,
         environment_config:str,
         validation_schemas:str,):

  AMQP_SERVER:AMQPServer = None
  HTTP_SERVER:HttpServer = None
  
  # get server configurations
  amqp_config:Dict = server_config.get('amqp')
  http_config:Dict = server_config.get('http')

  # build the validator object
  request_validator = build_validator(validation_schemas)

  # load mars environment
  LOGGER.info("load mars environment")
  model.EQUIPMENT, model.REFERENCE, model.COMMAND_REGISTER, model.DB_DRIVER = mars.build_environment(environment_config)


  # if amqp server configuration is defined and if parameter activate == true
  if activated_server == 'amqp' and amqp_config:
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
  
  elif activated_server == 'http' and http_config :
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
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGER = logging.getLogger("cmd_generator")

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', "--verbose", action='store_true')

    # read the configurations
    LOGGER.info("load configurations")
    parser.add_argument('-s', '--server',
                        type=str,
                        choices=['amqp', 'http'],
                        default='amqp',
                        help='type of server used for communications')
    
    parser.add_argument('--server-config',
                        type=str,
                        nargs=1,
                        action=ConfigLoader,
                        help='path of server configuration yaml file')

    parser.add_argument('--environment-config',
                        type=str,
                        nargs=1,
                        action=ConfigLoader,
                        help='path of environment configuration yaml file')
    
    parser.add_argument('--validation-schemas',
                        type=str,
                        nargs=1,
                        action=ConfigLoader,
                        help='path of the directory contains schemas for requests validations')

    args = parser.parse_args()
    args.validation_schemas = get_validation_schemas(__VALIDATION_SCHEMA_DIR)\
                              if not args.validation_schemas else args.validation_schemas
    args.server_config = get_config_from_file(__SERVER_CONFIG_FILE)\
                         if not args.server_config else args.server_config
    args.environment_config = get_config_from_file(__MARS_CONFIG_FILE)\
                              if not args.environment_config else args.environment_config
    
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGER = logging.getLogger("cmd_generator")
    
    if args.verbose:
      logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
      logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    
    logging.getLogger("pika").setLevel(logging.WARNING)


    LOGGER.info("run command_generator service")
    
    main(activated_server=args.server,
         server_config=args.server_config,
         environment_config=args.environment_config,
         validation_schemas=args.validation_schemas)

  except BaseException as error:
    LOGGER.fatal(error.describe())
    sys.exit(1)
  except KeyboardInterrupt as error:
    LOGGER.info("manual interruption of the program")
    sys.exit(1)