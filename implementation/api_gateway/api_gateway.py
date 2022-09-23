import logging
from urllib.parse import urlencode

import requests
from flask import Flask, request

app = Flask(__name__)
PORT = 8090

IOT_PORT = 8080
ANOMALY_DETECTION_PORT = 8084
PREDICTION_PORT = 8085
PREDICTION_ADVANCED_PORT = 8086
ANALYTICS_PORT = 8087


def get_url(host, port, path):
    url = f"http://{host}:{port}{path}"
    return url


def create_response(response):
    return response.json(), response.status_code, response.headers.items()


@app.route('/api/generateSensorData', methods=['POST'])
def generate_sensor_data():
    query_params = urlencode(request.args)
    url = get_url('localhost', IOT_PORT, '/v1/generateSensorData' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    response.headers.pop('Transfer-Encoding')
    return create_response(response)


@app.route('/api/detectAnomaly', methods=['POST'])
def detect_anomaly():
    query_params = urlencode(request.args)
    url = get_url('localhost', ANOMALY_DETECTION_PORT, '/v1/detectAnomaly' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    return create_response(response)


@app.route('/api/predict', methods=['POST'])
def predict():
    query_params = urlencode(request.args)
    url = get_url('localhost', PREDICTION_ADVANCED_PORT, '/v1/predict' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    return create_response(response)


@app.route('/api/assessPredictions', methods=['POST'])
def assess_predictions():
    query_params = urlencode(request.args)
    url = get_url('localhost', ANALYTICS_PORT, '/v1/assessPredictions' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    return create_response(response)


@app.route('/api/getAccuratePrediction', methods=['POST'])
def get_accurate_prediction():
    query_params = urlencode(request.args)
    url = get_url('localhost', ANALYTICS_PORT, '/v1/getAccuratePrediction' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    return create_response(response)


@app.route('/api/getValidPredictions', methods=['DELETE'])
def get_valid_predictions():
    query_params = urlencode(request.args)
    url = get_url('localhost', ANALYTICS_PORT, '/v1/getValidPredictions' + "?" + query_params)
    response = requests.delete(url, json=request.get_json())
    return create_response(response)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', port=PORT, debug=True)
