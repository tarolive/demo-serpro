from elasticsearch          import Elasticsearch
from flask                  import Flask, request
from os                     import getenv
from requests               import get
from tensorflow.saved_model import load

import tensorflow as tf

ELASTICSEARCH_HOST           = getenv('ELASTICSEARCH_HOST')
ELASTICSEARCH_USERNAME       = getenv('ELASTICSEARCH_USERNAME')
ELASTICSEARCH_PASSWORD       = getenv('ELASTICSEARCH_PASSWORD')
ELASTICSEARCH_INDEX          = 'ecg'
TELEGRAM_TOKEN               = getenv('TELEGRAM_TOKEN')
TELEGRAM_API                 = f'https://api.telegram.org/bot{ TELEGRAM_TOKEN }'

app = Flask(__name__)

elasticsearch_client = Elasticsearch(
    hosts        = ELASTICSEARCH_HOST,
    basic_auth   = (ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
    verify_certs = False
)

chat_ids = []
model    = load('model/')


@app.route('/', methods = ['POST'])
def add_to_chat_ids() -> dict:

    message = request.json
    text    = message['text']
    chat_id = message['chat']['id']

    if not text.startswith('/add'):

        return {}

    if chat_id not in chat_ids:

        chat_ids.append(chat_id)

    params = {
        'chat_id' : chat_id,
        'text'    : f'Chat id { chat_id } added to chat ids!'
    }

    api = f'{ TELEGRAM_API }/sendMessage'
    get(url = api, params = params)


@app.route('/predict', methods = ['GET', 'POST'])
def predict() -> dict:

    query = {}

    result = elasticsearch_client.search(index = ELASTICSEARCH_INDEX, query = query, size = 5)
    result = result['hits']['hits']

    for item in result: pass

    return {}
