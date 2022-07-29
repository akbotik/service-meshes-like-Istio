import logging
import datetime
import itertools

import psycopg2
import coloredlogs
import pandas as pd
import requests as requests
from flask import Flask, request
from flask import jsonify, abort, make_response
from requests.exceptions import HTTPError
from sklearn.metrics import mean_squared_error

app = Flask(__name__)
PORT = 8087

TABLE = 'aggregated_data'


class Prediction(object):
    def __init__(self, dict_prediction):
        self.date = dict_prediction['date']
        self.agg_mode = dict_prediction['agg_mode']
        self.agg_interval = dict_prediction['agg_interval']
        self.data_type = dict_prediction['data_type']
        self.predicted_value = dict_prediction['predicted_value']


def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='postgres',
                            user='postgres',
                            password='password')
    return conn


def get_predictions(dict_predictions):
    try:
        predictions = []
        for dict_prediction in dict_predictions:
            predictions.append(Prediction(dict_prediction))
        return predictions
    except (Exception, KeyError) as err:
        logging.error(err)
        abort(400)


def validate_prediction_params(predictions):
    for p1, p2 in itertools.combinations(predictions, 2):
        if (p1.date != p2.date) or (p1.agg_mode != p2.agg_mode) or \
                (p1.agg_interval != p2.agg_interval) or (p1.data_type != p2.data_type):
            logging.error("Parameters of predictions do not match")
            abort(400)


def get_prediction_params(predictions):
    date = datetime.datetime.strptime(predictions[0].date, "%Y-%m-%d").date()
    agg_mode = predictions[0].agg_mode
    agg_interval = predictions[0].agg_interval
    data_type = predictions[0].data_type
    return date, agg_mode, agg_interval, data_type


def load_true_value(date, agg_mode, agg_interval, data_type):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT data_value FROM {TABLE}"
                    f" WHERE timestamp = '{date}' AND aggregation_mode = '{agg_mode}'"
                    f" AND aggregation_interval = '{agg_interval}' AND data_type = '{data_type}'")
        if cur.rowcount > 0:
            true_value = cur.fetchone()[0]
            cur.close()
            conn.close()
            return true_value
        else:
            logging.error("True value is not available")
            abort(400)
    except (Exception, psycopg2.DatabaseError, psycopg2.OperationalError) as err:
        logging.error(err)
        abort(400)


def cast_to_list(x):
    if isinstance(x, int):
        return [x]
    elif isinstance(x, float):
        return [x]
    else:
        err = TypeError("Only integer or float is allowed")
        logging.error(err)
        abort(400)


def estimate_errors(true_value, predictions):
    df = pd.DataFrame(columns=['predicted_value', 'error'], index=predictions)
    df.rename_axis('prediction', inplace=True)
    for prediction in predictions:
        error = mean_squared_error(cast_to_list(true_value), cast_to_list(prediction.predicted_value))
        df.loc[prediction] = [prediction.predicted_value, error]
    return df


def extract_predicted_values(predictions):
    predicted_values = []
    for prediction in predictions:
        predicted_values.append(prediction.predicted_value)
    return predicted_values


def get_thresholds():
    thresholds = {'low': 30, 'high': 35}
    return thresholds


def is_valid(predicted_value, thresholds):
    return thresholds['low'] <= predicted_value <= thresholds['high']


def check_predictions(predictions, thresholds):
    df = pd.DataFrame(columns=['predicted_value'], index=predictions)
    df.rename_axis('prediction', inplace=True)
    for prediction in predictions:
        label = is_valid(prediction.predicted_value, thresholds)
        df.loc[prediction] = [label]
    return df


@app.route('/v1/assessPrediction', methods=['POST'])
def assess_prediction():
    """
    Accept predictions as dictionaries with the same parameters.
    Measure the mean squared error (MSE) of the predicted values.
    Return JSON object of DataFrame with assessments.
    Applicable only if the true value is known.
    """
    json = request.get_json()
    dict_predictions = json['predictions']

    if dict_predictions is None:
        abort(400)

    predictions = get_predictions(dict_predictions)
    validate_prediction_params(predictions)
    date, agg_mode, agg_interval, data_type = get_prediction_params(predictions)
    true_value = load_true_value(date, agg_mode, agg_interval, data_type)
    logging.debug(f"True value:\n{true_value}")
    df = estimate_errors(true_value, predictions)
    logging.info(f"Estimated errors:\n{df}")
    return create_response(df.to_json(orient="index"), 200)


@app.route('/v1/getAccurateValue', methods=['POST'])
def get_accurate_value():
    """
    Accept predictions as dictionaries with the same parameters.
    Measure the mean squared error (MSE) of the predicted values.
    Return the most accurate value from the predicted values.
    Applicable only if the true value is known.
    """
    json = request.get_json()
    dict_predictions = json['predictions']

    if dict_predictions is None:
        abort(400)

    predictions = get_predictions(dict_predictions)
    validate_prediction_params(predictions)
    date, agg_mode, agg_interval, data_type = get_prediction_params(predictions)
    true_value = load_true_value(date, agg_mode, agg_interval, data_type)
    logging.debug(f"True value:\n{true_value}")
    df = estimate_errors(true_value, predictions)
    df.sort_values(by=['error'], inplace=True)
    logging.debug(f"Estimated errors:\n{df}")
    accurate_value = df['predicted_value'].iat[0]
    logging.info(f"The most accurate value:\n{accurate_value}")
    return create_response(accurate_value, 200)


@app.route('/v1/getValidPredictions', methods=['DELETE'])
def get_valid_predictions():
    """
    Accept predictions as dictionaries with the same parameters.
    Examine predicted values against the expected thresholds.
    Return JSON object of DataFrame with valid predictions.
    No true value is required.
    """
    json = request.get_json()
    dict_predictions = json['predictions']

    if dict_predictions is None:
        abort(400)

    predictions = get_predictions(dict_predictions)
    validate_prediction_params(predictions)
    data = {'prediction': predictions,
            'predicted_value': extract_predicted_values(predictions)}
    df = pd.DataFrame(data)
    df.set_index('prediction', inplace=True)
    logging.debug(f"Received data:\n{df.tail()}")
    thresholds = get_thresholds()
    logging.debug(f"Expected thresholds:\n[{thresholds['low']}, {thresholds['high']}]")
    df_labels = check_predictions(predictions, thresholds)
    df = df.loc[df_labels['predicted_value'] == True]
    logging.info(f"Valid predictions:\n{df}")
    return create_response(df.to_json(orient="index"), 200)


def create_response(body, code):
    response = make_response(
        jsonify(body),
        code,
    )
    response.headers['Content-Type'] = "application/json"
    return response


if __name__ == '__main__':
    coloredlogs.install(level='DEBUG')
    app.run(host='0.0.0.0', port=PORT, debug=True)
