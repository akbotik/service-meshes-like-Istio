import logging
import datetime
import itertools

import psycopg2
import coloredlogs
import pandas as pd
from flask import Flask, request
from flask import jsonify, abort, make_response
from sklearn.metrics import mean_squared_error

app = Flask(__name__)
PORT = 8087

TABLE = 'aggregated_data'


class Prediction(object):
    def __init__(self, dict):
        self.date = dict['date']
        self.agg_mode = dict['agg_mode']
        self.agg_interval = dict['agg_interval']
        self.data_type = dict['data_type']
        self.predicted_value = dict['predicted_value']


def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='postgres',
                            user='postgres',
                            password='password')
    return conn


def get_predictions(items):
    try:
        predictions = []
        for item in items:
            predictions.append(Prediction(item))
        return predictions
    except (Exception, KeyError) as err:
        logging.error(err)
        abort(400)


def compare_prediction_params(predictions):
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
    df = pd.DataFrame(columns=['Error'], index=predictions)
    for prediction in predictions:
        error = mean_squared_error(cast_to_list(true_value), cast_to_list(prediction.predicted_value))
        df.loc[prediction] = error
    return df


@app.route('/v1/assessPrediction', methods=['POST'])
def assess_prediction():
    """
    Accept predictions as dictionaries.
    Measure the mean squared error (MSE) of the predicted values.
    Return JSON object of DataFrame with assessments.
    Applicable only if the true value is known.
    """
    json = request.get_json()
    items = json['predictions']

    if items is None:
        abort(400)

    predictions = get_predictions(items)
    compare_prediction_params(predictions)
    date, agg_mode, agg_interval, data_type = get_prediction_params(predictions)
    true_value = load_true_value(date, agg_mode, agg_interval, data_type)
    logging.debug(f"True value:\n{true_value}")
    df = estimate_errors(true_value, predictions)
    logging.info(f"Estimated_errors:\n{df}")
    return create_response(df.to_json(orient="columns"), 200)


@app.route('/v1/getAccurateValue', methods=['POST'])
def get_accurate_value():
    """
    Accept predictions as dictionaries.
    Measure the mean squared error (MSE) of the predicted values.
    Return the most accurate value from the predicted values.
    Applicable only if the true value is known.
    """
    json = request.get_json()
    items = json['predictions']

    if items is None:
        abort(400)

    predictions = get_predictions(items)
    compare_prediction_params(predictions)
    date, agg_mode, agg_interval, data_type = get_prediction_params(predictions)
    true_value = load_true_value(date, agg_mode, agg_interval, data_type)
    logging.debug(f"True value:\n{true_value}")
    df = estimate_errors(true_value, predictions)
    df.sort_values(by=['Error'], inplace=True)
    logging.debug(f"Estimated_errors:\n{df}")
    accurate_value = df.first_valid_index().predicted_value
    logging.info(f"The most accurate value:\n{accurate_value}")
    return create_response(accurate_value, 200)


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
