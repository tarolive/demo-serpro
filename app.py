from elasticsearch           import Elasticsearch
from flask                   import Flask, request
from os                      import getenv
from requests                import get
from tensorflow.keras.losses import mae
from tensorflow.saved_model  import load
from urllib3                 import disable_warnings

disable_warnings()

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

    return {}


@app.route('/predict', methods = ['GET', 'POST'])
def predict() -> dict:

    query = {
        'bool' : {
            'must' : {
                'match' : {
                    'severity' : 0
                }
            }
        }
    }

    result = elasticsearch_client.search(index = ELASTICSEARCH_INDEX, query = query, size = 5)
    result = result['hits']['hits']

    for item in result:

        id    = item['_id']
        input = item['_source']['input']

        reconstruction = model.serve([input])
        loss           = mae(reconstruction, [input]).numpy()[0]

        severity = 5

        if loss <= 0.056: severity = 4
        if loss <= 0.049: severity = 3
        if loss <= 0.042: severity = 2
        if loss <= 0.035: severity = 1

        document = {
            'severity'   : severity,
            'prediction' : loss
        }

        elasticsearch_client.update(index = ELASTICSEARCH_INDEX, id = id, doc = document)

        for chat_id in chat_ids:

            sendMessage(chat_id, f'Id : { id } | Severity : { severity } | Prediction : { loss }')

            if severity == 1:

                reply_markup = {
                    'inline_keyboard' : [
                        [{ 'text' : 'Yes'}],
                        [{ 'text' : 'No'}]
                    ]
                }

                sendMessage(chat_id, 'ECG with severity 1 detected! Do you want me to open a ticket?', reply_markup)

    return {}


def sendMessage(chat_id, text, reply_markup = None):

    params = {
        'chat_id'      : chat_id,
        'text'         : text,
        'reply_markup' : reply_markup
    }

    api = f'{ TELEGRAM_API }/sendMessage'
    get(url = api, params = params)
