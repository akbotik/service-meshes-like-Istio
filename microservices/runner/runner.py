# start iot data generation for X seconds
# wait X seconds...
# call prediction (2 endpoints in parallel)
# call anomaly_detection (detectAnomalyWithThreshold and detectAnomaly)
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from faker import Faker
import requests
import random
import threading
import concurrent.futures

data_types = ['PRESSURE', 'TEMPERATURE']
prediction_accuracies = ['low', 'high']
prediction_models = [None, 'ExponentialSmoothing', 'Prophet']


def get_url(ip, port, route):
    url = f"http://{ip}:{port}{route}"
    return url


def predict(model):
    if model is not None:
        url = get_url('localhost', 8086, '/v1/predict?predictionModel=' + model)
    else:
        url = get_url('localhost', 8086, '/v1/predict')
    data_type = random.choice(data_types)
    date = Faker().date()
    accuracy = random.choice(prediction_accuracies)
    body = dict(type=data_type, date=date, accuracy=accuracy)
    response = requests.post(url, json=body)
    return response.json()


def generate_data():
    duration = 1800000  # in milliseconds
    for data_type in data_types:
        url = get_url('localhost', 8080, '/v1/generateSensorData?requestDuration=' + duration)
        sensor_id = random.randint(1, 100)
        sensor_type = data_type
        body = dict(id=sensor_id, type=sensor_type)
        requests.post(url, json=body)


def get_predictions():
    predictions = []
    # create a thread pool with 3 worker threads
    executor = ThreadPoolExecutor(max_workers=3)
    # dispatch tasks into the thread pool and create a list of futures
    futures = [executor.submit(predict, model) for model in prediction_models]
    # iterate over all submitted tasks and get results as they are available
    for future in as_completed(futures):
        # get the result for the next completed task
        prediction = future.result()  # blocks
        predictions.append(prediction)
    # shutdown the thread pool
    executor.shutdown()  # blocks
    return predictions


def detect_anomaly(thresholds):
    pass


def assess_prediction(predictions):
    pass


def get_accurate_prediction(predictions):
    pass


def get_valid_predictions(predictions):
    pass


def run():
    generate_data()
    time.sleep(60)  # in seconds
    while True:
        predictions = get_predictions()
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.submit(detect_anomaly, bool(random.getrandbits(1)))
            executor.submit(assess_prediction, predictions)
            executor.submit(get_accurate_prediction, predictions)
            executor.submit(get_valid_predictions, predictions)


if __name__ == '__main__':
    run()
