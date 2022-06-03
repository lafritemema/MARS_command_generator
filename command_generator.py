import json
from server.exception import ServerException
from utils import get_config_from_file
import os
from dotenv import load_dotenv
from typing import Dict, List
from server.amqp import AMQPServer, CFunction, CPipeline
from exception import BaseException, BaseExceptionType
from server.exception import ServerException
import sys
import logging

import model
from model.action import Action
import mars

load_dotenv()
__SERVER_CONFIG_FILE = os.getenv('SERVER_CONFIG')
__SERVER_CONFIG_FILE = __SERVER_CONFIG_FILE if __SERVER_CONFIG_FILE else './config/server.yaml'
__MARS_CONFIG_FILE = os.getenv('MARS_CONFIG')
__MARS_CONFIG_FILE = __MARS_CONFIG_FILE if __MARS_CONFIG_FILE else './config/mars.yaml' 
__AMQP_TOPICS = 'request.command_generator','report.command_generator'

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGER = logging.getLogger("cmd_generator")
logging.getLogger("pika").setLevel(logging.WARNING)

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

def build_commands(body:Dict, headers:Dict):
  LOGGER.info()
  id = body.get('id')
  action = Action.get_from_db(id)
  return action.get_commands(), headers


def main():
  amqp_server = None
  http_server = None
  
  LOGGER.info("read configurations")
  SERVER_CONFIG = get_config_from_file(__SERVER_CONFIG_FILE)
  MARS_CONFIG = get_config_from_file(__MARS_CONFIG_FILE)
  amqp_config:Dict = SERVER_CONFIG.get('amqp')
  http_config:Dict = SERVER_CONFIG.get('http')

  LOGGER.info("load mars environment")
  model.EQUIPMENT, model.REFERENCE, model.COMMAND_REGISTER, model.DB_DRIVER = mars.build_environment(MARS_CONFIG)

  # if amqp server configuration is defined and if parameter activate == true
  if amqp_config and amqp_config.get('activate'):
    LOGGER.info("build amqp server")
    amqp_server = build_amqp_server(amqp_config)

    LOGGER.info('configure amqp server')
    amqp_server.add_queue(label="request_report",
                          topics=__AMQP_TOPICS)
    

    # prepare a consumer pipeline
    # no topic parameter for publish => report_topic contained in the message header
    req_pipeline = CPipeline([CFunction(build_commands),
                              CFunction(amqp_server.publish)])
    
    amqp_server.add_consumer('request.command_generator', req_pipeline)
  
  if http_config and http_config.get('activate'):
    # http server configuration - not implemented yet
    # TODO implement http_server and run 
    pass

  if not http_server and not amqp_server:
    raise BaseException(['CONFIG', 'SERVER'],
                        BaseExceptionType.CONFIG_NOT_CONFORM,
                        "no server activated, check the configuration")
  
  if http_server:
    # http_server run on new tread - not implemented yet
    pass

  if amqp_server:
    # run amqp server on the current tread
    LOGGER.info('run amqp server and wait for messages')
    amqp_server.run()
  


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