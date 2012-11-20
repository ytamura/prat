# coding=utf-8

from chat import string_filters

class DefaultConfig(object):
  """Default configuration for chat app"""
  DEBUG = True
  SECRET_KEY = "secret"

  APP_NAME = u"prat"

  MONGO_HOST = "127.0.0.1"
  MONGO_PORT = 27017
  MONGO_DB_NAME = "oochat"

  REDIS_HOST = "localhost"
  REDIS_PORT = 6379

  COMPILED_ASSET_PATH = "assets"
  COLLAPSED_MESSAGE_TIME_WINDOW = 5 * 60 # seconds

  PUSH_ADDRESS = "tcp://localhost:5666"
  SUBSCRIBE_ADDRESS = "tcp://localhost:5667"
  DEFAULT_CHANNELS = ["general", "Backlot", "OOSL"]
  STRING_FILTERS = [string_filters.replace_shas_with_barkeep_links, string_filters.replace_jira_links]
  KEEP_ALIVE_INTERVAL = 30000 # milliseconds
