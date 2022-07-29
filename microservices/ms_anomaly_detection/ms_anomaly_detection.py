import datetime
import logging

import coloredlogs
import pandas as pd
import psycopg2
from adtk.data import validate_series
from adtk.detector import GeneralizedESDTestAD, ThresholdAD
from flask import Flask, request
from flask import jsonify, abort, make_response

app = Flask(__name__)
PORT = 8084

YEAR = 'YEAR'
MONTH = 'MONTH'
DAY = 'DAY'

TABLE = 'aggregated_data'


def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='postgres',
                            user='postgres',
                            password='password')
    return conn


def get_query(data_type, start_date, end_date):
    query = f"SELECT data_value, timestamp FROM {TABLE}" \
            f" WHERE data_type = '{data_type}'"
    if (start_date is not None) and (end_date is not None):
        str_start_date = datetime.datetime.strftime(start_date, "%Y-%m-%d")
        str_end_date = datetime.datetime.strftime(end_date, "%Y-%m-%d")
        query = query + f" AND '[{str_start_date}, {str_end_date}]'::daterange @> timestamp"
    query = query + f" ORDER BY timestamp"
    return query


def load(data_type, start_date=None, end_date=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT aggregation_mode, aggregation_interval"
                    f" FROM {TABLE} WHERE data_type = '{data_type}'")
        if cur.rowcount > 0:
            agg_mode, agg_interval = cur.fetchone()
            query = get_query(data_type, start_date, end_date)
            logging.debug(f"Anomaly query:\n{query}")
            cur.execute(query)
            if cur.rowcount > 0:
                df = pd.DataFrame(cur.fetchall(), columns=['data_value', 'timestamp'])
                cur.close()
                conn.close()
                return df, agg_mode, agg_interval
            else:
                logging.error("Not enough data to detect")
                abort(400)
        else:
            logging.error("No data of this type")
            abort(400)
    except (Exception, psycopg2.DatabaseError, psycopg2.OperationalError) as err:
        logging.error(err)
        abort(400)


def preprocess(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d")
    df.set_index('timestamp', inplace=True)
    df = validate_series(df)
    return df


def get_anomaly_params(agg_mode, agg_interval, data_type, anomaly_count, start_date=None, end_date=None):
    d = {
        'agg_mode': agg_mode,
        'agg_interval': agg_interval,
        'data_type': data_type,
        'anomaly_count': anomaly_count
    }

    if (start_date is not None) and (end_date is not None):
        if agg_interval == YEAR:
            d['start_date'] = f"{start_date.year}"
            d['end_date'] = f"{end_date.year}"
        elif agg_interval == MONTH:
            d['start_date'] = f"{start_date.year}-{start_date.month}"
            d['end_date'] = f"{end_date.year}-{end_date.month}"
        else:
            d['start_date'] = f"{start_date}"
            d['end_date'] = f"{end_date}"
    return d


@app.route('/v1/detectAnomaly', methods=['POST'])
def detect_anomaly():
    json = request.get_json()
    data_type = json['type']

    if data_type is None:
        abort(400)

    # load data
    df, agg_mode, agg_interval = load(data_type)
    df = preprocess(df)
    logging.debug(f"Loaded data:\n{df.tail()}")

    # detect anomaly
    esd_ad = GeneralizedESDTestAD()
    df_anomaly = esd_ad.fit_detect(df)
    anomalies = df.loc[df_anomaly['data_value'] == True]
    logging.debug(f"Detected anomaly:\n{anomalies.tail()}")

    # formulate an anomaly
    if anomalies.shape[0] != 0:
        anomaly_count = df_anomaly.value_counts()[True].item()
    else:
        anomaly_count = 0
    params = get_anomaly_params(agg_mode, agg_interval, data_type, anomaly_count)
    anomaly = {'params': params,
               'anomalies': anomalies.to_json(orient='index')}
    logging.info(f"Anomaly:\n{anomaly}")
    return create_response(anomaly, 200)


@app.route('/v1/detectAnomalyWithThreshold', methods=['POST'])
def detect_anomaly_with_threshold():
    json = request.get_json()
    data_type = json['type']
    start_date = json['start_date']
    end_date = json['end_date']
    low_value = json['low_value']
    high_value = json['high_value']

    if (data_type is None) or (start_date is None) or (end_date is None) \
            or (low_value is None) or (high_value is None):
        abort(400)

    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    # load data
    df, agg_mode, agg_interval = load(data_type, start_date=start_date, end_date=end_date)
    df = preprocess(df)
    logging.debug(f"Loaded data:\n{df.tail()}")

    # detect anomaly
    threshold_ad = ThresholdAD(low=low_value, high=high_value)
    df_anomaly = threshold_ad.detect(df)
    anomalies = df.loc[df_anomaly['data_value'] == True]
    logging.debug(f"Detected anomaly:\n{anomalies.tail()}")

    # formulate an anomaly
    if anomalies.shape[0] != 0:
        anomaly_count = df_anomaly.value_counts()[True].item()
    else:
        anomaly_count = 0
    params = get_anomaly_params(agg_mode, agg_interval, data_type, anomaly_count,
                                start_date=start_date, end_date=end_date)
    anomaly = {'params': params,
               'anomalies': anomalies.to_json(orient='index')}
    logging.info(f"Anomaly:\n{anomaly}")
    return create_response(anomaly, 200)


@app.route('/v1/cleanAnomaly', methods=['DELETE'])
def clean_anomaly():
    # receive data
    json_request = request.get_json()
    df = pd.read_json(json_request, orient='index')
    df.sort_index(inplace=True)
    df.rename_axis('timestamp', inplace=True)
    logging.debug(f"Received data:\n{df.tail()}")

    # detect anomaly
    df = validate_series(df)
    esd_ad = GeneralizedESDTestAD()
    df_anomaly = esd_ad.fit_detect(df)
    anomalies = df.loc[df_anomaly['data_value'] == True]
    logging.debug(f"Detected anomaly:\n{anomalies.tail()}")

    # send clean data
    df = df.loc[df_anomaly['data_value'] == False]
    logging.info(f"Cleaned data:\n{df.tail()}")
    json_response = df.to_json(orient='index')
    return create_response(json_response, 200)


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
