import datetime
import itertools
import logging

import pandas as pd
import psycopg2
from flask import Flask, request
from flask import jsonify, abort, make_response
from sklearn.metrics import mean_squared_error

import thresholds

app = Flask(__name__)
PORT = 8087

TABLE = 'aggregated_data'


class Prediction(object):
    def __init__(self, dt_prediction):
        self.date = dt_prediction['date']                        # string
        self.agg_mode = dt_prediction['agg_mode']                # string
        self.agg_interval = dt_prediction['agg_interval']        # string
        self.data_type = dt_prediction['data_type']              # string
        self.predicted_value = dt_prediction['predicted_value']  # float


def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='postgres',
                            user='postgres',
                            password='password')
    return conn


def get_predictions(dt_predictions):
    """
    Convert predictions from dictionaries to class objects.
    """
    try:
        predictions = []
        for dt_prediction in dt_predictions:
            if dt_prediction is not None:
                predictions.append(Prediction(dt_prediction))
        return predictions
    except (Exception, KeyError) as err:
        logging.error(err)
        abort(400)


def validate_prediction_params(predictions):
    """
    Parameters of predictions should match for further analysis.
    """
    if not predictions:
        logging.error("Predictions are empty")
        abort(400)
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
    """
    Calculate the mean squared error (MSE) of the predicted values,
    i.e., difference between the true value the predicted values.
    """
    df = pd.DataFrame(columns=['predicted_value', 'error'], index=predictions)
    df.rename_axis('prediction', inplace=True)
    for prediction in predictions:
        error = mean_squared_error(cast_to_list(true_value), cast_to_list(prediction.predicted_value))
        df.loc[prediction] = [prediction.predicted_value, error]
    return df


def get_thresholds(date, agg_mode, agg_interval, data_type):
    """
    Retrieve expected thresholds according to the parameters of predictions.
    """
    if data_type == thresholds.PRESSURE:
        return thresholds.get_pressure_thresholds()
    elif data_type == thresholds.TEMPERATURE:
        if agg_interval == thresholds.YEAR:
            return thresholds.get_temperature_thresholds_for_year()
        elif (agg_interval == thresholds.MONTH) or (agg_interval == thresholds.DAY):
            return thresholds.get_temperature_thresholds_for_month(date.month)
        else:
            logging.error("Unknown aggregation interval")
            abort(400)
    else:
        logging.error("Unknown data type")
        abort(400)


def is_valid(predicted_value, dt_thresholds):
    """
    Compare a predicted value with expected thresholds, and
    identify it as anomalous when it is beyond the thresholds.
    """
    return dt_thresholds['low'] <= predicted_value <= dt_thresholds['high']


def check_predictions(predictions, dt_thresholds):
    """
    Examine predicted values against the expected thresholds.
    """
    df = pd.DataFrame(columns=['predicted_value', 'valid'], index=predictions)
    df.rename_axis('prediction', inplace=True)
    for prediction in predictions:
        valid = is_valid(prediction.predicted_value, dt_thresholds)
        df.loc[prediction] = [prediction.predicted_value, valid]
    return df


@app.route('/v1/assessPredictions', methods=['POST'])
def assess_predictions():
    """
    Accept predictions as dictionaries with the same parameters.
    Measure the mean squared error (MSE) of the predicted values.
    Return assessed predictions.
    Applicable only if the true value is known.
    A 200 OK response indicates that the intended action was successful.
    """
    json = request.get_json()
    dt_predictions = json['predictions']

    if (dt_predictions is None) or not dt_predictions:
        abort(400)

    logging.info(f"* Assess predictions: {dt_predictions}")

    predictions = get_predictions(dt_predictions)
    validate_prediction_params(predictions)
    date, agg_mode, agg_interval, data_type = get_prediction_params(predictions)
    true_value = load_true_value(date, agg_mode, agg_interval, data_type)
    logging.debug(f"True value:\n{true_value}")
    df = estimate_errors(true_value, predictions)
    logging.debug(f"Estimated errors:\n{df}")
    dt_predictions.clear()
    predictions.clear()
    for prediction, row in df.iterrows():
        dt_prediction = vars(prediction)
        dt_prediction['error'] = row['error']
        predictions.append(dt_prediction)
    dt_predictions = {'predictions': predictions}
    logging.info(f"Assessed predictions:\n{dt_predictions}")
    return create_response(dt_predictions, 200)


@app.route('/v1/getAccuratePrediction', methods=['POST'])
def get_accurate_prediction():
    """
    Accept predictions as dictionaries with the same parameters.
    Measure the mean squared error (MSE) of the predicted values.
    Return the most accurate prediction.
    Applicable only if the true value is known.
    A 200 OK response indicates that the intended action was successful.
    """
    json = request.get_json()
    dt_predictions = json['predictions']

    if (dt_predictions is None) or not dt_predictions:
        abort(400)

    logging.info(f"* Get accurate prediction from {dt_predictions}")

    predictions = get_predictions(dt_predictions)
    validate_prediction_params(predictions)
    date, agg_mode, agg_interval, data_type = get_prediction_params(predictions)
    true_value = load_true_value(date, agg_mode, agg_interval, data_type)
    logging.debug(f"True value:\n{true_value}")
    df = estimate_errors(true_value, predictions)
    df.sort_values(by=['error'], inplace=True)
    logging.debug(f"Estimated errors:\n{df}")
    dt_prediction = vars(df.first_valid_index())
    logging.info(f"The most accurate value:\n{dt_prediction}")
    return create_response(dt_prediction, 200)


@app.route('/v1/getValidPredictions', methods=['DELETE'])
def get_valid_predictions():
    """
    Accept predictions as dictionaries with the same parameters.
    Examine predicted values against the expected thresholds.
    Return valid predictions.
    No true value is required.
    A 200 OK response indicates that the intended action was successful.
    """
    json = request.get_json()
    dt_predictions = json['predictions']

    if (dt_predictions is None) or not dt_predictions:
        abort(400)

    logging.info(f"* Get valid predictions: {dt_predictions}")

    predictions = get_predictions(dt_predictions)
    validate_prediction_params(predictions)
    date, agg_mode, agg_interval, data_type = get_prediction_params(predictions)
    dt_thresholds = get_thresholds(date, agg_mode, agg_interval, data_type)
    logging.debug(f"Expected thresholds:\n[{dt_thresholds['low']}, {dt_thresholds['high']}]")
    df = check_predictions(predictions, dt_thresholds)
    logging.debug(f"Checked predictions:\n{df}")
    dt_predictions.clear()
    predictions.clear()
    for prediction, row in df.iterrows():
        if row['valid']:
            dt_prediction = vars(prediction)
            predictions.append(dt_prediction)
    dt_predictions = {'predictions': predictions}
    logging.info(f"Valid predictions:\n{dt_predictions}")
    return create_response(dt_predictions, 200)


def create_response(body, code):
    response = make_response(
        jsonify(body),
        code,
    )
    response.headers['Content-Type'] = "application/json"
    return response


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port=PORT, debug=True)
