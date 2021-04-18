import requests
import json


API_URL = "http://localhost:8082/mlvcapi/v1.0"


def post(url, data, headers):
    r = requests.post(API_URL + url, json=data, headers=headers)
    return r
