import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta
from faker import Faker

IOT_PORTS = [8080, 8081]
PREDICTION_PORT = 8086
ANOMALY_DETECTION_PORT = 8084
ANALYTICS_PORT = 8087

data_types = ['PRESSURE', 'TEMPERATURE']
prediction_accuracies = ['LOW', 'HIGH']
prediction_models = [None, 'ExponentialSmoothing', 'Prophet']


def get_url(host, port, path):
    url = f"http://{host}:{port}{path}"
    return url


def generate_data(data_type, port):
    duration = 1800000  # in milliseconds
    url = get_url('localhost', port, '/v1/generateSensorData?requestDuration=' + str(duration))
    sensor_id = random.randint(1, 100)
    sensor_type = data_type
    body = dict(id=sensor_id, type=sensor_type)
    logging.info(f"Start data generation of type {data_type} on {port}")
    requests.post(url, json=body)


def get_random_anomaly_thresholds(data_type):
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


def detect_anomaly(thresholds, date_start, date_end):
    data_type = random.choice(data_types)
    if thresholds:
        url = get_url('localhost', ANOMALY_DETECTION_PORT, '/v1/detectAnomaly?thresholds=' + str(thresholds))
        start_date = Faker().date_between_dates(date_start=date_start, date_end=date_end)
        start_date = datetime.strftime(start_date, "%Y-%m-%d")
        end_date = datetime.strftime(date_end, "%Y-%m-%d")
        low_value, high_value = get_random_anomaly_thresholds(data_type)
        body = dict(type=data_type, start_date=start_date, end_date=end_date,
                    low_value=low_value, high_value=high_value)
        logging.info(f"Detect {data_type} anomaly from {start_date} to {end_date} "
                     f"with thresholds {low_value}, {high_value}")
    else:
        url = get_url('localhost', ANOMALY_DETECTION_PORT, '/v1/detectAnomaly')
        body = dict(type=data_type)
        logging.info(f"Detect {data_type} anomaly")
    requests.post(url, json=body)


def get_random_prediction_body(date_start, date_end):
    data_type = random.choice(data_types)
    date = Faker().date_between(start_date=random.choice((date_start, date_end)))
    date = datetime.strftime(date, "%Y-%m-%d")
    accuracy = random.choice(prediction_accuracies)
    body = dict(type=data_type, date=date, accuracy=accuracy)
    logging.info(f"Predict {data_type} for {date} with {accuracy} accuracy")
    return body


def predict(model, body):
    if model is not None:
        url = get_url('localhost', PREDICTION_PORT, '/v1/predict?predictionModel=' + model)
    else:
        url = get_url('localhost', PREDICTION_PORT, '/v1/predict')
    response = requests.post(url, json=body)
    try:
        prediction = response.json()
    except (Exception, ValueError):
        prediction = None
    return prediction


def get_predictions(executor, date_start, date_end):
    predictions = []
    prediction_body = get_random_prediction_body(date_start, date_end)
    # dispatch tasks into the thread pool and create a list of futures
    futures = [executor.submit(predict, model, prediction_body) for model in prediction_models]
    # iterate over all submitted tasks and get results as they are available
    for future in as_completed(futures):
        # get the result for the next completed task
        prediction = future.result()  # blocks
        predictions.append(prediction)
    return predictions


def assess_predictions(predictions):
    url = get_url('localhost', ANALYTICS_PORT, '/v1/assessPredictions')
    body = dict(predictions=predictions)
    logging.info(f"Assess predictions: {predictions}")
    requests.post(url, json=body)


def get_accurate_prediction(predictions):
    url = get_url('localhost', ANALYTICS_PORT, '/v1/getAccuratePrediction')
    body = dict(predictions=predictions)
    logging.info(f"Get accurate prediction from {predictions}")
    requests.post(url, json=body)


def get_valid_predictions(predictions):
    url = get_url('localhost', ANALYTICS_PORT, '/v1/getValidPredictions')
    body = dict(predictions=predictions)
    logging.info(f"Get valid predictions: {predictions}")
    requests.delete(url, json=body)


def run():
    date_start = datetime(1971, 1, 1)
    date_step = relativedelta(years=1)
    date_end = date_start
    # use a with statement to ensure threads are cleaned up promptly
    with ThreadPoolExecutor(max_workers=10) as executor:
        # submit a task with arguments
        executor.submit(generate_data, data_types[0], IOT_PORTS[0])  # does not block
        executor.submit(generate_data, data_types[1], IOT_PORTS[1])
        while True:
            time.sleep(30)  # in seconds
            date_end = date_end + date_step
            executor.submit(detect_anomaly, bool(random.getrandbits(1)), date_start, date_end)
            predictions = get_predictions(executor, date_start, date_end)
            if any(prediction is not None for prediction in predictions):
                executor.submit(assess_predictions, predictions)
                executor.submit(get_accurate_prediction, predictions)
                executor.submit(get_valid_predictions, predictions)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    run()
