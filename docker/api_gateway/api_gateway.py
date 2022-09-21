import logging
from urllib.parse import urlencode

import requests
from flask import Flask, request

app = Flask(__name__)
PORT = 8080

IOT = 'ms-iot.default.svc.cluster.local'
ANOMALY_DETECTION = 'ms-anomaly-detection.default.svc.cluster.local'
PREDICTION = 'ms-prediction.default.svc.cluster.local'
PREDICTION_ADVANCED = 'ms-prediction-advanced.default.svc.cluster.local'
ANALYTICS = 'ms-analytics.default.svc.cluster.local'


def get_url(host, port, path):
    url = f"http://{host}:{port}{path}"
    return url


def create_response(response):
    return response.json(), response.status_code, response.headers.items()


@app.route('/v1/generateSensorData', methods=['POST'])
def generate_sensor_data():
    query_params = urlencode(request.args)
    url = get_url(IOT, PORT, '/v1/generateSensorData' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    response.headers.pop('Transfer-Encoding')
    return create_response(response)


@app.route('/v1/detectAnomaly', methods=['POST'])
def detect_anomaly():
    query_params = urlencode(request.args)
    url = get_url(ANOMALY_DETECTION, PORT, '/v1/detectAnomaly' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    return create_response(response)


@app.route('/v1/predict', methods=['POST'])
def predict():
    query_params = urlencode(request.args)
    url = get_url(PREDICTION_ADVANCED, PORT, '/v1/predict' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    return create_response(response)


@app.route('/v1/assessPredictions', methods=['POST'])
def assess_predictions():
    query_params = urlencode(request.args)
    url = get_url(ANALYTICS, PORT, '/v1/assessPredictions' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    return create_response(response)


@app.route('/v1/getAccuratePrediction', methods=['POST'])
def get_accurate_prediction():
    query_params = urlencode(request.args)
    url = get_url(ANALYTICS, PORT, '/v1/getAccuratePrediction' + "?" + query_params)
    response = requests.post(url, json=request.get_json())
    return create_response(response)


@app.route('/v1/getValidPredictions', methods=['DELETE'])
def get_valid_predictions():
    query_params = urlencode(request.args)
    url = get_url(ANALYTICS, PORT, '/v1/getValidPredictions' + "?" + query_params)
    response = requests.delete(url, json=request.get_json())
    return create_response(response)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', port=PORT, debug=True)
