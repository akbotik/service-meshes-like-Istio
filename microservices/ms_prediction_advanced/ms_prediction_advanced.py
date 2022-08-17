import datetime
import logging

import numpy as np
import pandas as pd
import psycopg2
import requests
from darts import TimeSeries
from darts.models import ExponentialSmoothing
from dateutil.relativedelta import relativedelta
from flask import Flask, request
from flask import jsonify, abort, make_response
from prophet import Prophet
from requests.exceptions import HTTPError

app = Flask(__name__)
PORT = 8086

ANOMALY_DETECTION_URL = 'http://localhost:8084/v1/cleanAnomaly'

YEAR = 'YEAR'
MONTH = 'MONTH'
DAY = 'DAY'

LOW_ACCURACY = 'low'
HIGH_ACCURACY = 'high'

TABLE = 'aggregated_data'


class Prediction:
    def __init__(self, date, agg_mode, agg_interval, data_type, predicted_value):
        self.date = date                        # string
        self.agg_mode = agg_mode                # string
        self.agg_interval = agg_interval        # string
        self.data_type = data_type              # string
        self.predicted_value = predicted_value  # float


def get_db_connection():
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
        start_date = end_date - relativedelta(years=10)
    else:
        start_date = datetime.datetime(1971, 1, 1)
    return start_date, end_date


def get_query(data_type, start_date, end_date, agg_interval, freq):
    str_start_date = datetime.datetime.strftime(start_date, "%Y-%m-%d")
    str_end_date = datetime.datetime.strftime(end_date, "%Y-%m-%d")

    query = f"SELECT data_value, timestamp FROM {TABLE}" \
            f" WHERE data_type = '{data_type}'" \
            f" AND '[{str_start_date}, {str_end_date}]'::daterange @> timestamp"
    if freq:
        if agg_interval != YEAR:
            query = query + f" AND DATE_PART('{MONTH.lower()}', timestamp) = {end_date.month}"
        if agg_interval == DAY:
            query = query + f" AND DATE_PART('{DAY.lower()}', timestamp) <= {end_date.day}"
    query = query + f" ORDER BY timestamp"
    return query


def load(data_type, date, accuracy, freq=False):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT aggregation_mode, aggregation_interval"
                    f" FROM {TABLE} WHERE data_type = '{data_type}'")
        if cur.rowcount > 0:
            agg_mode, agg_interval = cur.fetchone()
            start_date, end_date = get_daterange(agg_interval, date, accuracy)
            query = get_query(data_type, start_date, end_date, agg_interval, freq)
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


def preprocess(df, transform=None):
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d")
    df.drop_duplicates(subset=['timestamp'], inplace=True)
    df.sort_values(by=['timestamp'], inplace=True)
    if transform == 'TimeSeries':
        s = TimeSeries.from_dataframe(df, 'timestamp', 'data_value')
    elif transform == 'DataFrame':
        s = df.rename(columns={'timestamp': 'ds', 'data_value': 'y'})
    else:
        s = df.set_index('timestamp')
    return s


def clean_anomaly(df):
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
    if agg_interval != DAY:
        missing_date = last_date + relativedelta(years=1)
        if end_date.month == 2:
            missing_date = get_last_day_of_month(missing_date)
    else:
        missing_date = last_date + relativedelta(days=1)
    return missing_date


def fill_missing_values(s, end_date, agg_interval, model=None):
    if type(model).__name__ == 'ExponentialSmoothing':
        last_date = s.end_time().to_pydatetime().date()
        num_steps = 1
        while last_date != end_date:
            missing_date = get_missing_date(last_date, end_date, agg_interval)
            num_steps += 1
            last_date = missing_date
        if num_steps > 0:
            prediction = model.predict(num_steps)
            s = s.concatenate(prediction, ignore_time_axes=True)
    elif type(model).__name__ == 'Prophet':
        last_date = s['ds'].iat[-1].date()
        periods = 1
        while last_date != end_date:
            missing_date = get_missing_date(last_date, end_date, agg_interval)
            periods += 1
            last_date = missing_date
        if periods > 0:
            future = model.make_future_dataframe(periods=periods)
            forecast = model.predict(future)
            s = forecast[['ds', 'yhat']].copy()
    else:
        last_date = s.index[-1].date()
        while last_date != end_date:
            missing_date = get_missing_date(last_date, end_date, agg_interval)
            if missing_date.month == end_date.month:
                if missing_date.day <= end_date.day:
                    arr = s['data_value'].to_numpy()
                    hist, bins = np.histogram(arr, bins='fd')
                    missing_value = (bins[hist.argmax()] + bins[hist.argmax() + 1]) / 2
                    prediction = pd.DataFrame({'data_value': missing_value}, index=[pd.Timestamp(missing_date)])
                    s = pd.concat([s, prediction])
            last_date = missing_date
        missing_date = get_missing_date(last_date, end_date, agg_interval)
        arr = s['data_value'].to_numpy()
        hist, bins = np.histogram(arr, bins='fd')
        missing_value = (bins[hist.argmax()] + bins[hist.argmax() + 1]) / 2
        prediction = pd.DataFrame({'data_value': missing_value}, index=[pd.Timestamp(missing_date)])
        s = pd.concat([s, prediction])
    return s


def get_predicted_value(s, model=None):
    if type(model).__name__ == 'ExponentialSmoothing':
        predicted_value = s.last_value()
    elif type(model).__name__ == 'Prophet':
        predicted_value = s['yhat'].iat[-1]
    else:
        predicted_value = s['data_value'].iat[-1]
    return predicted_value


def get_prediction(date, agg_mode, agg_interval, data_type, predicted_value):
    if agg_interval == YEAR:
        date = get_last_day_of_year(date)
    elif agg_interval == MONTH:
        date = get_last_day_of_month(date)
    else:
        date = date
    date = datetime.datetime.strftime(date, "%Y-%m-%d")

    prediction = Prediction(date, agg_mode, agg_interval, data_type, predicted_value)
    return vars(prediction)


def predict_with_freedman_diaconis_estimator():
    json = request.get_json()
    data_type = json['type']
    date = json['date']
    accuracy = json['accuracy']

    if (data_type is None) or (date is None) or (accuracy is None):
        abort(400)

    logging.info(f"* Predicting {data_type} with Freedman Diaconis Estimator for {date} with {accuracy} accuracy")

    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    # load data
    df, agg_mode, agg_interval, end_date = load(data_type, date, accuracy, freq=True)
    df = preprocess(df)
    logging.debug(f"Loaded data:\n{df.tail()}")

    # clean anomaly
    df = clean_anomaly(df)

    # fill missing values
    old_size = df.size
    df = fill_missing_values(df, end_date, agg_interval)
    if df.size != old_size:
        logging.debug(f"Cleaned data with missing values:\n{df.tail()}")

    # predict
    predicted_value = get_predicted_value(df)

    # formulate a prediction
    prediction = get_prediction(date, agg_mode, agg_interval, data_type, predicted_value)
    logging.info(f"Predicted with Freedman Diaconis Estimator:\n{prediction}")
    return prediction


def predict_with_exponential_smoothing():
    json = request.get_json()
    data_type = json['type']
    date = json['date']
    accuracy = json['accuracy']

    if (data_type is None) or (date is None) or (accuracy is None):
        abort(400)

    logging.info(f"* Predicting {data_type} with Exponential Smoothing for {date} with {accuracy} accuracy")

    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    # load data
    df, agg_mode, agg_interval, end_date = load(data_type, date, accuracy)
    ts = preprocess(df, transform='TimeSeries')
    logging.debug(f"Loaded data:\n{ts.pd_dataframe().tail()}")

    # train a forecasting model
    m = ExponentialSmoothing(damped=True)
    m.fit(ts)

    # fill missing values
    old_size = ts.duration
    ts = fill_missing_values(ts, end_date, agg_interval, model=m)
    if ts.duration != old_size:
        logging.debug(f"Data with missing values:\n{ts.pd_dataframe().tail()}")

    # predict
    predicted_value = get_predicted_value(ts, model=m)

    # formulate a prediction
    prediction = get_prediction(date, agg_mode, agg_interval, data_type, predicted_value)
    logging.info(f"Predicted with Exponential Smoothing:\n{prediction}")
    return prediction


def predict_with_prophet():
    json = request.get_json()
    data_type = json['type']
    date = json['date']
    accuracy = json['accuracy']

    if (data_type is None) or (date is None) or (accuracy is None):
        abort(400)

    logging.info(f"* Predicting {data_type} with Prophet for {date} with {accuracy} accuracy")

    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    # load data
    df, agg_mode, agg_interval, end_date = load(data_type, date, accuracy, freq=True)
    df = preprocess(df, transform='DataFrame')
    df_renamed = df.rename(columns={'ds': 'timestamp', 'y': 'data_value'})
    df_renamed.set_index('timestamp', inplace=True)
    logging.debug(f"Loaded data:\n{df_renamed.tail()}")

    # train a forecasting model
    m = Prophet()
    m.fit(df)

    # fill missing values
    old_size = df.size
    df = fill_missing_values(df, end_date, agg_interval, model=m)
    df_renamed = df.rename(columns={'ds': 'timestamp', 'yhat': 'data_value'})
    df_renamed.set_index('timestamp', inplace=True)
    if df.size != old_size:
        logging.debug(f"Data with missing values:\n{df_renamed.tail()}")

    # predict
    predicted_value = get_predicted_value(df, model=m)

    # formulate a prediction
    prediction = get_prediction(date, agg_mode, agg_interval, data_type, predicted_value)
    logging.info(f"Predicted with Prophet:\n{prediction}")
    return prediction


@app.route('/v1/predict', methods=['POST'])
def predict():
    prediction_model = request.args.get('predictionModel')

    if prediction_model == 'ExponentialSmoothing':
        prediction = predict_with_exponential_smoothing()
    elif prediction_model == 'Prophet':
        prediction = predict_with_prophet()
    else:
        prediction = predict_with_freedman_diaconis_estimator()
    return create_response(prediction, 200)


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
