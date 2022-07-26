import logging

import coloredlogs
import pandas as pd
from flask import Flask, request
from flask import jsonify, abort, make_response
from sklearn.metrics import mean_squared_error

app = Flask(__name__)
PORT = 8087


def cast_to_list(x):
    if isinstance(x, int):
        return [x]
    elif isinstance(x, float):
        return [x]
    else:
        err = TypeError("Only integer or float is allowed")
        logging.error(err)
        abort(400)


def estimate_errors(true_value, predicted_values):
    df = pd.DataFrame(columns=['Error'], index=predicted_values)
    for predicted_value in predicted_values:
        error = mean_squared_error(cast_to_list(true_value), cast_to_list(predicted_value))
        df.loc[predicted_value] = error
    return df


@app.route('/v1/assessPrediction', methods=['POST'])
def assess_prediction():
    """
    Measure the mean squared error (MSE) of the predicted values.
    Applicable only if the true value is known.
    """
    json = request.get_json()
    # date, type
    true_value = json['true_value']
    predicted_values = json['predicted_values']

    if (true_value is None) or (predicted_values is None):
        abort(400)

    df = estimate_errors(true_value, predicted_values)
    logging.debug(f"\n{df}")

    json_df = df.to_json(orient='index')
    return create_response(json_df, 200)


@app.route('/v1/getAccurateValue', methods=['POST'])
def get_accurate_value():
    """
    Return the most accurate value from the predicted values.
    Applicable only if the true value is known.
    """
    json = request.get_json()
    true_value = json['true_value']
    predicted_values = json['predicted_values']

    if (true_value is None) or (predicted_values is None):
        abort(400)

    df = estimate_errors(true_value, predicted_values)
    df.sort_values(by=['Error'], inplace=True)
    accurate_value = df.first_valid_index()

    logging.debug(f"\n{df}")
    logging.info(accurate_value)
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