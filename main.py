import sys
import json
from http import HTTPStatus
from flask import Flask
from flask_restx import Api, Resource, reqparse
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlite3
import logging.handlers
from config import *


app = Flask(__name__)
app.config['DEBUG'] = False
app.config['UPLOAD_FOLDER'] = FILES_PATH
app.wsgi_app = ProxyFix(app.wsgi_app)

api = Api(app, version='0.1', title='Token Registry API', description='A simple API for the Cardano Token Registry',)
ns = api.namespace(NAMESPACE, description='Cardano Token Registry')

tokens_parser = reqparse.RequestParser()
tokens_parser.add_argument('tokens', action='append', required=True)


@ns.route('/token/<string:token_policy>/<string:token_name>')
@api.response(HTTPStatus.OK.value, "OK")
@api.response(HTTPStatus.NOT_ACCEPTABLE.value, "Not Acceptable client error")
@api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, "Server error")
class TokenDetails(Resource):
    def get(self, token_policy, token_name):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name, ticker, description, decimals FROM tokens WHERE policy_id = ? and name_hex = ?",
                    (token_policy, token_name))
        tokens_info = cur.fetchall()
        tokens = []
        for item in tokens_info:
            token = {}
            token['name'] = item[0]
            token['ticker'] = item[1]
            token['description'] = item[2]
            token['decimals'] = item[3]
            tokens.append(token)
        conn.close()
        if len(tokens) == 0:
            msg = {}
            msg['error'] = 'Token %s.%s not found' % (token_policy, token_name)
            return [msg], 406
        return tokens


@ns.route('/ticker/<string:ticker>')
@api.response(HTTPStatus.OK.value, "OK")
@api.response(HTTPStatus.NOT_ACCEPTABLE.value, "Not Acceptable client error")
@api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, "Server error")
class Ticker(Resource):
    def get(self, ticker):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT policy_id, name_hex, name, description, decimals FROM tokens WHERE ticker = ?", (ticker,))
        tokens_info = cur.fetchall()
        tokens = []
        for item in tokens_info:
            token = {}
            token['policy_id'] = item[0]
            token['name_hex'] = item[1]
            token['name'] = item[2]
            token['ticker'] = ticker
            token['description'] = item[3]
            token['decimals'] = item[4]
            tokens.append(token)
        conn.close()
        if len(tokens) == 0:
            msg = {}
            msg['error'] = 'Ticker %s not found' % ticker
            return [msg], 406
        return tokens


@ns.route('/tokens')
@api.response(HTTPStatus.OK.value, "OK")
@api.response(HTTPStatus.NOT_ACCEPTABLE.value, "Not Acceptable client error")
@api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, "Server error")
@api.doc(parser=tokens_parser)
class Tokens(Resource):
    def post(self):
        args = tokens_parser.parse_args()
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        token_policies_list = []
        token = {}
        tokens_list = []
        try:
            for item in args['tokens']:
                token = json.loads(item.replace("'", '"'))
                if 'policy_id' in token and 'token_name' in token:
                    token_policies_list.append(token['policy_id'])
                    token_with_name = {}
                    token_with_name['policy_id'] = token['policy_id']
                    token_with_name['token_name'] = token['token_name']
                    tokens_list.append(token_with_name)
        except Exception as e:
            applog.exception(e)
            applog.error(token)
        cur.execute("SELECT policy_id, name_hex, name, ticker, description, decimals FROM tokens WHERE policy_id in "
                    "({seq})".format(seq=','.join(['?'] * len(token_policies_list))), token_policies_list)
        tokens_info = cur.fetchall()
        tokens = []
        for item in tokens_info:
            token = {}
            token['policy_id'] = item[0]
            token['name_hex'] = item[1]
            token['name'] = item[2]
            token['ticker'] = item[3]
            token['description'] = item[4]
            token['decimals'] = item[5]
            for item in tokens_list:
                if token['policy_id'] == item['policy_id'] and token['name_hex'] == item['token_name']:
                    tokens.append(token)
                    break
        conn.close()
        if len(tokens) == 0:
            msg = {}
            msg['error'] = 'Tokens not found'
            return [msg], 406
        return tokens


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
    handler = logging.handlers.WatchedFileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    applog = logging.getLogger('token-registry')
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
    conn.close()

    applog.info("*****************************************************************")
    applog.info('Starting')

    app.run(
        threaded=True,
        host=HOST,
        port=PORT
    )
