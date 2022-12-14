import datetime
import logging

import pandas as pd
import psycopg2
from adtk.data import validate_series
from adtk.detector import GeneralizedESDTestAD, ThresholdAD
from flask import Flask, request
from flask import jsonify, abort, make_response

app = Flask(__name__)
PORT = 8080

YEAR = 'YEAR'
MONTH = 'MONTH'
DAY = 'DAY'

TABLE = 'aggregated_data'


def get_db_connection():
    """
    Create a new database connection.
    """
    conn = psycopg2.connect(host='postgres',
                            database='postgres',
                            user='postgres',
                            password='password')
    return conn


def get_query(data_type, aggregation_mode, aggregation_interval, start_date, end_date):
    """
    Define a query for extracting data from a database.
    """
    query = f"SELECT data_value, timestamp FROM {TABLE}" \
            f" WHERE data_type = '{data_type}'" \
            f" AND aggregation_mode = '{aggregation_mode}'" \
            f" AND aggregation_interval = '{aggregation_interval}'"
    if (start_date is not None) and (end_date is not None):
        str_start_date = datetime.datetime.strftime(start_date, "%Y-%m-%d")
        str_end_date = datetime.datetime.strftime(end_date, "%Y-%m-%d")
        query = query + f" AND '[{str_start_date}, {str_end_date}]'::daterange @> timestamp"
    query = query + f" ORDER BY timestamp"
    return query


def extract(data_type, start_date=None, end_date=None):
    """
    Extract data from a database.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT aggregation_mode, aggregation_interval"
                    f" FROM {TABLE} WHERE data_type = '{data_type}'")
        if cur.rowcount > 0:
            aggregation_mode, aggregation_interval = cur.fetchone()
            query = get_query(data_type, aggregation_mode, aggregation_interval, start_date, end_date)
            logging.debug(f"Anomaly query:\n{query}")
            cur.execute(query)
            if cur.rowcount > 0:
                df = pd.DataFrame(cur.fetchall(), columns=['data_value', 'timestamp'])
                cur.close()
                conn.close()
                return df, aggregation_mode, aggregation_interval
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
    """
    Transform raw data in a required format, remove duplicates and sort time index.
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d")
    df.set_index('timestamp', inplace=True)
    df = validate_series(df)
    return df


def get_anomaly_params(aggregation_mode, aggregation_interval, data_type, anomaly_count,
                       start_date=None, end_date=None, low_value=None, high_value=None):
    """
    Provide anomaly detection parameters.
    """
    dt = dict(aggregation_mode=aggregation_mode, aggregation_interval=aggregation_interval,
              data_type=data_type, anomaly_count=anomaly_count)

    if (start_date is not None) and (end_date is not None):
        dt['start_date'] = datetime.datetime.strftime(start_date, "%Y-%m-%d")
        dt['end_date'] = datetime.datetime.strftime(end_date, "%Y-%m-%d")

    if (low_value is not None) and (high_value is not None):
        dt['low_value'] = low_value
        dt['high_value'] = high_value
    return dt


def detect():
    """
    Detect anomalies of historical data based on generalized ESD test.
    Perform generalized extreme studentized deviate test on historical data
    which follows an approximately normal distribution
    and identify normal values vs. outliers.

    :return: detected anomalies with anomaly detection parameters
    """
    json = request.get_json()
    data_type = json['type']

    if data_type is None:
        abort(400)

    logging.info(f"* Detecting {data_type} anomaly")

    # extract data
    df, aggregation_mode, aggregation_interval = extract(data_type)
    df = preprocess(df)
    logging.debug(f"Extracted data:\n{df.tail()}")

    # detect anomaly
    esd_ad = GeneralizedESDTestAD()
    df_anomaly = esd_ad.fit_detect(df)
    anomalies = df.loc[df_anomaly['data_value'] == True]
    logging.debug(f"Detected anomaly:\n{anomalies.tail()}")

    # formulate an anomaly
    anomaly_count = anomalies.shape[0]
    params = get_anomaly_params(aggregation_mode, aggregation_interval, data_type, anomaly_count)
    anomaly = {'params': params,
               'anomalies': anomalies.to_json(orient='index')}
    logging.info(f"Anomaly:\n{anomaly}")
    return anomaly


def detect_with_thresholds():
    """
    Detect anomalies of historical data based on user-given thresholds.
    Compare stored values with user-given thresholds and
    identify values as anomalous when they are beyond the thresholds.

    :return: detected anomalies with anomaly detection parameters
    """
    json = request.get_json()
    data_type = json['type']
    start_date = json['start_date']
    end_date = json['end_date']
    low_value = json['low_value']
    high_value = json['high_value']

    if (data_type is None) or (start_date is None) or (end_date is None) \
            or (low_value is None) or (high_value is None):
        abort(400)

    logging.info(f"* Detecting {data_type} anomaly from {start_date} to {end_date} "
                 f"with thresholds {low_value}, {high_value}")

    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    # extract data
    df, aggregation_mode, aggregation_interval = extract(data_type, start_date=start_date, end_date=end_date)
    df = preprocess(df)
    logging.debug(f"Extracted data:\n{df.tail()}")

    # detect anomaly
    threshold_ad = ThresholdAD(low=low_value, high=high_value)
    df_anomaly = threshold_ad.detect(df)
    anomalies = df.loc[df_anomaly['data_value'] == True]
    logging.debug(f"Detected anomaly:\n{anomalies.tail()}")

    # formulate an anomaly
    anomaly_count = anomalies.shape[0]
    params = get_anomaly_params(aggregation_mode, aggregation_interval, data_type, anomaly_count,
                                start_date=start_date, end_date=end_date,
                                low_value=low_value, high_value=high_value)
    anomaly = {'params': params,
               'anomalies': anomalies.to_json(orient='index')}
    logging.info(f"Anomaly:\n{anomaly}")
    return anomaly


@app.route('/v1/detectAnomaly', methods=['POST'])
def detect_anomaly():
    """
    Detect anomalies of historical data based on generalized ESD test or on user-given thresholds.

    :return: detected anomalies with anomaly detection parameters and a 200 OK response if intended action is successful
    """
    thresholds = request.args.get('thresholds')

    if thresholds == 'True':
        anomaly = detect_with_thresholds()
    else:
        anomaly = detect()

    return create_response(anomaly, 200)


@app.route('/v1/cleanAnomaly', methods=['DELETE'])
def clean_anomaly():
    """
    Clean outliers of historical data based on generalized ESD test to reduce the noise.

    :return: cleaned data and a 200 OK response if intended action is successful
    """
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
    logging.getLogger().setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', port=PORT, debug=True)
