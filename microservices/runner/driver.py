# Python program to display all the prime numbers within an interval
import random
import threading
import requests
from flask import Flask, jsonify, request, redirect, abort, Response, json, make_response
import time
from string import Template

app = Flask(__name__)
PORT = 8080
bind_to = {'hostname': "0.0.0.0", 'port': PORT}
global shouldStop
shouldStop = False

HEADER_APP_JSON = {'Content-Type': 'application/json'}
users = ["ruslan", "alexandra", "hannes", "daniel", "ivan"]
calculation_type = ["add", "multiply", "fibonacci", "prime"]


def get_random_body():
    user = random.choice(users)
    calculation = random.choice(calculation_type)
    price = random.randint(1, 100)
    firstNumber = random.randint(100, 30000)
    secondNumber = random.randint(100, 30000)
    str = Template(
        '{"user": "${user}","calculationType": "${calc}","price": ${price},"firstNumber": ${first},"secondNumber": ${second}}')
    return str.substitute(user=user, calc=calculation, price=price, first=firstNumber, second=secondNumber)


def random_request(url, body, header):
    print('Sending request: ' + body)
    return requests.post(url, data=body, headers=header)


def create_response(body, code):
    response = make_response(
        jsonify(body),
        code,
    )
    response.headers["Content-Type"] = "application/json"
    return response


@app.route('/simulate', methods=['GET'])
def simulate():
    minikube_port = request.args.get("port")
    minikube_ip = request.args.get("ip")
    duration = request.args.get("duration")
    start_time = current_time_seconds()
    BASE_URL = 'http://' + minikube_ip + ':' + minikube_port + '/'
    global shouldStop
    shouldStop = False
    # create bank account and deposit
    for u in users:
        url_create = BASE_URL + 'createAccount?user=' + u
        url_deposit = BASE_URL + 'depositAccount?user=' + u + '&amount=' + str(1000)
        requests.post(url_create)
        requests.post(url_deposit)
    while not shouldStop:
        for u in users:
            url_deposit = BASE_URL + 'depositAccount?user=' + u + '&amount=' + str(100)
            requests.post(url_deposit)
        url = BASE_URL + 'calculate2'
        threading.Thread(target=random_request, args=(url, get_random_body(), HEADER_APP_JSON)).start()
        requests.get("http://192.168.64.3:30439/getAnalytics?function=add")
        check_if_should_stop_works(duration, start_time)
        time.sleep(0.2)
    return create_response("OK", 200)


def check_if_should_stop_works(duration, start_time):
    d = int(duration) * 1000
    if int(start_time) + d <= current_time_seconds():
        global shouldStop
        shouldStop = True


def current_time_seconds():
    return round(time.time() * 1000)


@app.route('/stop', methods=['GET'])
def stop():
    global shouldStop
    s = request.args.get('shouldStop')
    shouldStop = s
    return create_response("OK", 200)


if __name__ == '__main__':
    app.run(host=bind_to['hostname'], port=int(bind_to['port']), debug=True, use_reloader=False)
