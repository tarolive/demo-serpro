from elasticsearch           import Elasticsearch
from flask                   import Flask, request
from json                    import dumps
from os                      import getenv
from requests                import get
from tensorflow.keras.losses import mae
from tensorflow.math         import less
from tensorflow.saved_model  import load
from time                    import sleep
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

    if text.startswith('/start'):

        sendMessage(chat_id, 'Hello... The app is working!')
        return {}

    if text.startswith('/add'):

        if chat_id not in chat_ids:

            chat_ids.append(chat_id)

        sendMessage(chat_id, f'Chat id { chat_id } added to chat ids and will receive ECG messages!')
        return {}

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

    result = elasticsearch_client.search(index = ELASTICSEARCH_INDEX, query = query, size = 30)
    result = result['hits']['hits']

    for item in result:

        id    = item['_id']
        input = item['_source']['input']

        reconstruction = model.serve([input])
        loss           = mae(reconstruction, [input]).numpy()[0]

        severity = 5

        if less(loss, 0.091):
            severity = 4

        if less(loss, 0.090):
            severity = 3

        if less(loss, 0.087):
            severity = 2

        if less(loss, 0.086):
            severity = 1

        document = {
            'severity'   : severity,
            'prediction' : loss
        }

        elasticsearch_client.update(index = ELASTICSEARCH_INDEX, id = id, doc = document)

        for chat_id in chat_ids:

            sendMessage(chat_id, f'Id : { id } | Severity : { severity } | Prediction : { loss }')

            if severity == 1:

                print('severity == 1')

                reply_markup = {
                    'inline_keyboard' : [
                        [{ 'text' : 'Yes', 'callback_data' : 'open_ticket' }]
                    ]
                }

                sendMessage(chat_id, 'ECG with severity 1 detected! Do you want me to open a ticket?', dumps(reply_markup))

        sleep(0.5)

    return {}


def sendMessage(chat_id, text, reply_markup = None):

    params = {
        'chat_id'      : chat_id,
        'text'         : text,
        'reply_markup' : reply_markup
    }

    api = f'{ TELEGRAM_API }/sendMessage'
    get(url = api, params = params)
