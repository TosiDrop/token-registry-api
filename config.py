import os
env = dict(os.environ)


"""
general settings
"""
FILES_PATH = 'files'
LOG_FILE = 'logs/application.log'
UPDATE_LOG_FILE = 'logs/update.log'
NAMESPACE = 'api/v0'
HOST = '0.0.0.0'
PORT = 8050

"""
token registry settings
"""
TOKEN_REGISTRY_URL = 'https://github.com/cardano-foundation/cardano-token-registry.git'
REPOSITORY_PATH = FILES_PATH + '/cardano-token-registry'
POLICIES_PATH = REPOSITORY_PATH + '/mappings'

"""
sqlite3 database settings
"""
DB_NAME = 'db/tokens-registry.db'
