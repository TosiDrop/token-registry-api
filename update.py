#!/usr/bin/env python3


import logging.handlers
import logging
import sys
import sqlite3
import json
from config import *


if __name__ == '__main__':
    """
    create some required folders to store log and transaction file
    """
    try:
        if not os.path.exists(FILES_PATH):
            os.mkdir(FILES_PATH)
        if not os.path.exists(os.path.dirname(UPDATE_LOG_FILE)):
            os.mkdir(os.path.dirname(UPDATE_LOG_FILE))
        if not os.path.exists(os.path.dirname(DB_NAME)):
            os.mkdir(os.path.dirname(DB_NAME))
    except Exception as e:
        print('Error creating the required folders: %s' % e)
        sys.exit(1)

    """
    Set up logging
    """
    handler = logging.handlers.WatchedFileHandler(UPDATE_LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    applog = logging.getLogger('token-registry-update')
    applog.addHandler(handler)
    applog.setLevel(logging.INFO)

    """
    Create database and tables if not already existing
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                policy_id CHAR(56) NOT NULL,
                name_hex CHAR(32),
                name CHAR(32),
                ticker CHAR(32),
                decimals INTEGER,
                description TEXT
                )''')
    conn.commit()
    cur.execute('''CREATE INDEX IF NOT EXISTS tokens_policy_id on tokens(policy_id)''')
    cur.execute('''CREATE INDEX IF NOT EXISTS tokens_name_hex on tokens(name_hex)''')
    cur.execute('''CREATE INDEX IF NOT EXISTS tokens_ticker on tokens(ticker)''')
    conn.commit()

    applog.info("*****************************************************************")
    applog.info('Start')

    for f in os.listdir(POLICIES_PATH):
        file = os.path.join(POLICIES_PATH, f)
        if os.path.isfile(file):
            with open(POLICIES_PATH + '/' + f, 'r') as pf:
                try:
                    policy = json.loads(pf.read())
                    policy_id = str(policy['subject'][0:56])
                    token_name_hex = str(policy['subject'][56:])
                    token_name = str(policy['name']['value'])
                    if 'ticker' in policy:
                        token_ticker = str(policy['ticker']['value'])
                    else:
                        token_ticker = ''
                    if 'decimals' in policy:
                        token_decimals = int(policy['decimals']['value'])
                    else:
                        token_decimals = 0
                    token_description = policy['description']['value']
                    print('Ticker: %s, Name: %s, Policy: %s, Hex_name: %s' %
                          (token_ticker, token_name, policy_id, token_name_hex))
                    cur.execute("SELECT count(*) from tokens where policy_id = ? and name_hex = ?",
                                (policy_id, token_name_hex))
                    if cur.fetchone()[0] == 0:
                        cur.execute("INSERT INTO tokens (policy_id, name_hex, name, ticker, decimals, description) "
                                    "VALUES (?, ?, ?, ?, ?, ?)",
                                    (policy_id, token_name_hex, token_name, token_ticker,
                                     token_decimals, token_description))
                    else:
                        cur.execute("UPDATE tokens  set name = ?, ticker = ?, decimals = ?, description = ? "
                                    "WHERE policy_id = ? and name_hex = ?",
                                    (token_name, token_ticker, token_description, policy_id,
                                     token_decimals,  token_name_hex))
                except Exception as e:
                    applog.error('Invalid policy file %s' % pf)
                    applog.exception(e)
    conn.commit()
    conn.close()
    applog.info('end')
    applog.info("*****************************************************************")
