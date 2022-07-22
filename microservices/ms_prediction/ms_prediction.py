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

LOW_ACCURACY = 'low'
HIGH_ACCURACY = 'high'

TABLE = 'aggregated_data'


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
        start_date = end_date - relativedelta(years=2)
    else:
        start_date = datetime.datetime(1971, 1, 1)
    return start_date, end_date


def get_query(data_type, start_date, end_date, agg_interval, save_freq):
    str_start_date = datetime.datetime.strftime(start_date, "%Y-%m-%d")
    str_end_date = datetime.datetime.strftime(end_date, "%Y-%m-%d")

    query = f"SELECT data_value, timestamp FROM {TABLE}" \
            f" WHERE data_type = '{data_type}'" \
            f" AND '[{str_start_date}, {str_end_date}]'::daterange @> timestamp"
    if agg_interval != YEAR:
        query = query + f" AND DATE_PART('{MONTH.lower()}', timestamp) = {end_date.month}"
    if (agg_interval == DAY) and (save_freq == False):
        query = query + f" AND DATE_PART('{DAY.lower()}', timestamp) <= {end_date.day}"
    query = query + f" ORDER BY timestamp"
    return query


def preprocess(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d")
    len_prev = len(df)
    df.drop_duplicates(inplace=True)
    len_curr = len(df)
    print("\nRemoved duplicates:")
    print(len_prev - len_curr)
    df.set_index('timestamp', inplace=True)
    return df


def load(data_type, date, accuracy, save_freq=False):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT aggregation_mode, aggregation_interval"
                    f" FROM {TABLE} WHERE data_type = '{data_type}'")
        if cur.rowcount > 0:
            agg_mode, agg_interval = cur.fetchone()
            start_date, end_date = get_daterange(agg_interval, date, accuracy)
            query = get_query(data_type, start_date, end_date, agg_interval, save_freq)
            print("\nPrediction query:")
            print(query)
            cur.execute(query)
            if cur.rowcount > 0:
                df = pd.DataFrame(cur.fetchall(), columns=['data_value', 'timestamp'])
                df = preprocess(df)
                cur.close()
                conn.close()
                return df, agg_mode, agg_interval, end_date
            else:
                logging.error("Not enough data to predict")
                abort(400)
        else:
            abort(400)
    except (Exception, psycopg2.DatabaseError, psycopg2.OperationalError) as err:
        logging.error(err)
        abort(400)


def clean_anomaly(df):
    try:
        url = ANOMALY_DETECTION_URL
        json_df = df.to_json(orient='index')
        response = requests.post(url, json=json_df)
        response.raise_for_status()
        json_no_anomaly = response.json()
        df_no_anomaly = pd.read_json(json_no_anomaly, orient='index')
        df_no_anomaly.sort_index(inplace=True)
        df_no_anomaly.rename_axis('timestamp', inplace=True)
        return df_no_anomaly
    except HTTPError as http_err:
        logging.error(http_err)
        abort(400)
    except Exception as err:
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


def fill_missing_values(data, end_date, agg_interval, model=None):
    if model is None:
        last_date = data.index[-1].date()
        while last_date != end_date:
            missing_date = get_missing_date(last_date, end_date, agg_interval)
            if missing_date.month == end_date.month:
                if missing_date.day <= end_date.day:
                    arr = data['data_value'].to_numpy()
                    hist, bins = np.histogram(arr, bins='fd')
                    missing_value = (bins[hist.argmax()] + bins[hist.argmax() + 1]) / 2
                    prediction = pd.DataFrame({'data_value': missing_value}, index=[pd.Timestamp(missing_date)])
                    data = pd.concat([data, prediction])
            last_date = missing_date
    else:
        last_date = data.end_time().to_pydatetime().date()
        num_steps = 0
        while last_date != end_date:
            missing_date = get_missing_date(last_date, end_date, agg_interval)
            num_steps += 1
            last_date = missing_date
        if num_steps > 0:
            prediction = model.predict(num_steps)
            data = data.concatenate(prediction, ignore_time_axes=True)
    return data


def get_predicted_value(data, model=None):
    if model is None:
        arr = data['data_value'].to_numpy()
        hist, bins = np.histogram(arr, bins='fd')
        predicted_value = bins[hist.argmax()]
    else:
        predicted_value = model.predict(1).pd_dataframe()['data_value'].iat[-1]
    return predicted_value


def get_prediction(date, agg_mode, agg_interval, data_type, predicted_value):
    d = {
        'agg_mode': agg_mode,
        'agg_interval': agg_interval,
        'data_type': data_type,
        'predicted_value': predicted_value
    }

    if agg_interval == YEAR:
        d['date'] = f"{date.year}"
    elif agg_interval == MONTH:
        d['date'] = f"{date.year}-{date.month}"
    else:
        d['date'] = f"{date}"
    return d


@app.route('/v1/predictWithFreedmanDiaconisEstimator', methods=['POST'])
def predict_with_freedman_diaconis_estimator():
    json = request.get_json()
    data_type = json['type']
    date = json['date']
    accuracy = json['accuracy']

    if (data_type is None) or (date is None) or (accuracy is None):
        abort(400)

    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    # load data
    df, agg_mode, agg_interval, end_date = load(data_type, date, accuracy)
    print("\nLoaded data:")
    print(df.tail())

    # clean anomaly
    df_no_anomaly = clean_anomaly(df)

    # fill missing values
    df_missing_values = fill_missing_values(df_no_anomaly, end_date, agg_interval)
    print("\nCleaned data with missing values:")
    print(df_missing_values.tail())

    # predict
    predicted_value = get_predicted_value(df_missing_values)

    # formulate a prediction
    prediction = get_prediction(date, agg_mode, agg_interval, data_type, predicted_value)
    print("\nPrediction:")
    print(prediction)
    return create_response(prediction, 200)


def create_response(body, code):
    response = make_response(
        jsonify(body),
        code,
    )
    response.headers['Content-Type'] = "application/json"
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
