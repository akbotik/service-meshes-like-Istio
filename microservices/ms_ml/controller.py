import logging

import pandas as pd
import requests
from flask import Flask
from flask import jsonify, abort, make_response
from requests.exceptions import HTTPError

app = Flask(__name__)
PORT = 8086

ANOMALY_DETECTION_URL = 'http://localhost:8084/v1/detectAnomalyWithThreshold'

YEAR = 'YEAR'
MONTH = 'MONTH'
DAY = 'DAY'

LOW_ACCURACY = 'low'
HIGH_ACCURACY = 'high'


@app.route('/')
def get_anomaly():
    try:
        url = ANOMALY_DETECTION_URL
        payload = {
            'type': 'temperature',
            'start_date': '1971-01-01',
            'end_date': '1971-02-28',
            'low': -15,
            'high': 0
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        df_params = result['params']
        print(df_params)
        df_anomaly = pd.read_json(result['anomalies'], orient='index')
        df_anomaly.sort_index(inplace=True)
        print(df_anomaly)
        return create_response(result, 200)
    except HTTPError as http_err:
        logging.error(http_err)
        abort(400)
    except Exception as err:
        logging.error(err)
        abort(400)


def create_response(body, code):
    response = make_response(
        jsonify(body),
        code,
    )
    response.headers['Content-Type'] = "application/json"
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
