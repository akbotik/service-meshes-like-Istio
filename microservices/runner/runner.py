# start iot data generation for X seconds
# wait X seconds...
# call prediction (2 endpoints in parallel)
# call anomaly_detection (detectAnomalyWithThreshold and detectAnomaly)
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from faker import Faker

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
    date = Faker().date_between(start_date=datetime(1971, 1, 1))
    accuracy = random.choice(prediction_accuracies)
    body = dict(type=data_type, date=date, accuracy=accuracy)
    response = requests.post(url, json=body)
    return response.json()


def get_random_thresholds(data_type):
    if data_type == 'TEMPERATURE':
        low_value = random.uniform(-50, 50)
        high_value = random.uniform(-50, 50)
    else:
        low_value = random.uniform(980, 1030)
        high_value = random.uniform(980, 1030)
    if low_value > high_value:
        temp = low_value
        low_value = high_value
        high_value = temp
    return low_value, high_value


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
    data_type = random.choice(data_types)
    if thresholds:
        url = get_url('localhost', 8084, '/v1/detectAnomaly?thresholds=' + thresholds)
        end_date = Faker().date_between(start_date=datetime(1971, 1, 1))
        start_date = Faker().date_between_dates(date_start=datetime(1971, 1, 1), date_end=end_date)
        low_value, high_value = get_random_thresholds(data_type)
        body = dict(type=data_type, start_date=start_date, end_date=end_date,
                    low_value=low_value, high_value=high_value)
    else:
        url = get_url('localhost', 8084, '/v1/detectAnomaly')
        body = dict(type=data_type)
    requests.post(url, json=body)


def assess_prediction(predictions):
    url = get_url('localhost', 8087, '/v1/assessPrediction')
    body = dict(predictions=predictions)
    requests.post(url, json=body)


def get_accurate_prediction(predictions):
    url = get_url('localhost', 8087, '/v1/getAccuratePrediction')
    body = dict(predictions=predictions)
    requests.post(url, json=body)


def get_valid_predictions(predictions):
    url = get_url('localhost', 8087, '/v1/getValidPredictions')
    body = dict(predictions=predictions)
    requests.post(url, json=body)


def run():
    generate_data()
    time.sleep(60)  # in seconds
    while True:
        predictions = get_predictions()
        # use a with statement to ensure threads are cleaned up promptly
        with ThreadPoolExecutor(max_workers=4) as executor:
            # submit a task with arguments
            executor.submit(detect_anomaly, bool(random.getrandbits(1)))  # does not block
            executor.submit(assess_prediction, predictions)
            executor.submit(get_accurate_prediction, predictions)
            executor.submit(get_valid_predictions, predictions)


if __name__ == '__main__':
    run()
