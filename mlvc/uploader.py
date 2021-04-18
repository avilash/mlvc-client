import requests
import json


API_URL = "http://localhost:8082/mlvcapi/v1.0"


def post(url, data=None, headers=None, files=None):
    r = requests.post(API_URL + url, files=files, json=data, headers=headers)
    return r.text
