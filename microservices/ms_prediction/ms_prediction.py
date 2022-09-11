import datetime
import logging

import numpy as np
import pandas as pd
import psycopg2
import requests
from dateutil.relativedelta import relativedelta
from flask import Flask, request
from flask import jsonify, abort, make_response
from requests.exceptions import HTTPError

app = Flask(__name__)
PORT = 8085

ANOMALY_DETECTION_URL = 'http://localhost:8084/v1/cleanAnomaly'

YEAR = 'YEAR'
MONTH = 'MONTH'
DAY = 'DAY'

LOW_ACCURACY = 'LOW'
HIGH_ACCURACY = 'HIGH'

TABLE = 'aggregated_data'


class Prediction:
    def __init__(self, date, agg_mode, agg_interval, data_type, predicted_value):
        self.date = date
        self.agg_mode = agg_mode
        self.agg_interval = agg_interval
        self.data_type = data_type
        self.predicted_value = predicted_value


def get_db_connection():
    """
    Create a new database connection.
    """
    conn = psycopg2.connect(host='localhost',
                            database='postgres',
                            user='postgres',
                            password='password')
    return conn


def get_last_day_of_month(date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month + 1, day=1) - datetime.timedelta(days=1)


def get_last_day_of_year(date):
    return datetime.date(year=date.year, month=12, day=31)


def get_daterange(agg_interval, date, accuracy):
    """
    Compute a date range based on aggregation interval, prediction date and prediction accuracy
    for extracting data from a database.
    """
    if agg_interval == YEAR:
        # 1982-01-01 => 1981-12-31 (the last day of the prev year)
        end_date = get_last_day_of_year(date - relativedelta(years=1))
    elif agg_interval == MONTH:
        # 1982-01-01 => 1981-01-31 (the last day of the month of the prev year)
        end_date = get_last_day_of_month(date - relativedelta(years=1))
    else:
        # 1982-01-01 => 1981-12-31 (the prev day)
        end_date = date - relativedelta(days=1)

    if accuracy == LOW_ACCURACY:
        start_date = end_date - relativedelta(years=2)
    else:
        start_date = datetime.datetime(1971, 1, 1)
    return start_date, end_date


def get_query(data_type, agg_mode, agg_interval, start_date, end_date):
    """
    Define a query for extracting data from a database.
    """
    str_start_date = datetime.datetime.strftime(start_date, "%Y-%m-%d")
    str_end_date = datetime.datetime.strftime(end_date, "%Y-%m-%d")

    query = f"SELECT data_value, timestamp FROM {TABLE}" \
            f" WHERE data_type = '{data_type}'" \
            f" AND aggregation_mode= '{agg_mode}' AND aggregation_interval= '{agg_interval}'" \
            f" AND '[{str_start_date}, {str_end_date}]'::daterange @> timestamp"
    if agg_interval != YEAR:
        query = query + f" AND DATE_PART('{MONTH.lower()}', timestamp) = {end_date.month}"
    if agg_interval == DAY:
        query = query + f" AND DATE_PART('{DAY.lower()}', timestamp) <= {end_date.day}"
    query = query + f" ORDER BY timestamp"
    return query


def extract(data_type, date, accuracy):
    """
    Extract data from a database.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT aggregation_mode, aggregation_interval"
                    f" FROM {TABLE} WHERE data_type = '{data_type}'")
        if cur.rowcount > 0:
            agg_mode, agg_interval = cur.fetchone()
            start_date, end_date = get_daterange(agg_interval, date, accuracy)
            query = get_query(data_type, agg_mode, agg_interval, start_date, end_date)
            logging.debug(f"Prediction query:\n{query}")
            cur.execute(query)
            if cur.rowcount > 0:
                df = pd.DataFrame(cur.fetchall(), columns=['data_value', 'timestamp'])
                cur.close()
                conn.close()
                return df, agg_mode, agg_interval, end_date
            else:
                logging.error("Not enough data to predict")
                abort(400)
        else:
            logging.error("No data of this type")
            abort(400)
    except (Exception, psycopg2.DatabaseError, psycopg2.OperationalError) as err:
        logging.error(err)
        abort(400)


def preprocess(df):
    """
    Transform raw data in a required format, remove duplicates and sort time index.
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d")
    df.drop_duplicates(subset=['timestamp'], inplace=True)
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    return df


def clean_anomaly(df):
    """
    Clean outliers of historical data to make a better prediction.
    """
    try:
        url = ANOMALY_DETECTION_URL
        json_request = df.to_json(orient='index')
        response = requests.delete(url, json=json_request)
        response.raise_for_status()
        json_response = response.json()
        df = pd.read_json(json_response, orient='index')
        df.sort_index(inplace=True)
        df.rename_axis('timestamp', inplace=True)
        return df
    except (Exception, HTTPError) as err:
        logging.error(err)
        abort(400)


def get_missing_date(last_date, end_date, agg_interval):
    """
    Identify a missing date.
    """
    if agg_interval != DAY:
        missing_date = last_date + relativedelta(years=1)
        if end_date.month == 2:
            missing_date = get_last_day_of_month(missing_date)
    else:
        missing_date = last_date + relativedelta(days=1)
    return missing_date


def predict_missing_values(df, end_date, agg_interval):
    """
    Predict the target value incl. missing values to ensure that there are no prediction failures.
    """
    last_date = df.index[-1].date()
    while last_date != end_date:
        missing_date = get_missing_date(last_date, end_date, agg_interval)
        if missing_date.month == end_date.month:
            if missing_date.day <= end_date.day:
                arr = df['data_value'].to_numpy()
                hist, bins = np.histogram(arr, bins='fd')
                missing_value = (bins[hist.argmax()] + bins[hist.argmax() + 1]) / 2
                prediction = pd.DataFrame({'data_value': missing_value}, index=[pd.Timestamp(missing_date)])
                df = pd.concat([df, prediction])
        last_date = missing_date
    missing_date = get_missing_date(last_date, end_date, agg_interval)
    arr = df['data_value'].to_numpy()
    hist, bins = np.histogram(arr, bins='fd')
    missing_value = (bins[hist.argmax()] + bins[hist.argmax() + 1]) / 2
    prediction = pd.DataFrame({'data_value': missing_value}, index=[pd.Timestamp(missing_date)])
    df = pd.concat([df, prediction])
    return df


def get_predicted_value(df):
    """
    Return a predicted value.
    """
    predicted_value = df['data_value'].iat[-1]
    return predicted_value


def get_prediction(date, agg_mode, agg_interval, data_type, predicted_value):
    """
    Formulate a prediction with prediction parameters.
    """
    if agg_interval == YEAR:
        date = get_last_day_of_year(date)
    elif agg_interval == MONTH:
        date = get_last_day_of_month(date)
    else:
        date = date
    date = datetime.datetime.strftime(date, "%Y-%m-%d")

    prediction = Prediction(date, agg_mode, agg_interval, data_type, predicted_value)
    return vars(prediction)


@app.route('/v1/predict', methods=['POST'])
def predict():
    """
    Predict with Freedman Diaconis Estimator.

    :return: a prediction with prediction parameters and a 200 OK response if intended action is successful
    """
    json = request.get_json()
    data_type = json['type']
    date = json['date']
    accuracy = json['accuracy']

    if (data_type is None) or (date is None) or (accuracy is None):
        abort(400)

    logging.info(f"* Predicting {data_type} with Freedman Diaconis Estimator for {date} with {accuracy} accuracy")

    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    # extract data
    df, agg_mode, agg_interval, end_date = extract(data_type, date, accuracy)
    df = preprocess(df)
    logging.debug(f"Extracted data:\n{df.tail()}")

    # clean anomaly
    df = clean_anomaly(df)

    # predict
    old_size = df.size
    df = predict_missing_values(df, end_date, agg_interval)
    if df.size != old_size:
        logging.debug(f"Predicted data:\n{df.tail()}")

    # formulate a prediction
    predicted_value = get_predicted_value(df)
    prediction = get_prediction(date, agg_mode, agg_interval, data_type, predicted_value)
    logging.info(f"Prediction:\n{prediction}")
    return create_response(prediction, 200)


def create_response(body, code):
    response = make_response(
        jsonify(body),
        code,
    )
    response.headers['Content-Type'] = "application/json"
    return response


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', port=PORT, debug=True)
