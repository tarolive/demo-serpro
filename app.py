from elasticsearch import Elasticsearch
from flask         import Flask, request
from os            import getenv
from requests      import get

ELASTICSEARCH_HOST           = getenv('ELASTICSEARCH_HOST')
ELASTICSEARCH_USERNAME       = getenv('ELASTICSEARCH_USERNAME')
ELASTICSEARCH_PASSWORD       = getenv('ELASTICSEARCH_PASSWORD')
ELASTICSEARCH_DOCUMENT_INDEX = getenv('ELASTICSEARCH_DOCUMENT_INDEX')
TELEGRAM_TOKEN               = getenv('TELEGRAM_TOKEN')
TELEGRAM_API                 = f'https://api.telegram.org/bot{ TELEGRAM_TOKEN }'

app = Flask(__name__)

elasticsearch_client = Elasticsearch(
    hosts        = ELASTICSEARCH_HOST,
    basic_auth   = (ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    verify_certs = False
)

chat_ids = []


@app.route('/', methods = ['POST'])
def add_to_chat_list() -> dict:

    message = request.json
    text    = message['text']
    chat_id = message['chat']['id']

    if not text.startswith('/add'):

        return 0

    if chat_id not in chat_ids:

        chat_ids.append(chat_id)

    params = {
        'chat_id' : chat_id,
        'text'    : f'Chat id { chat_id } added to chat ids!'
    }

    api = f'{ TELEGRAM_API }/sendMessage'
    get(url = api, params = params)
