import os
import json
import requests
from os.path import expanduser

from mlvc.utils.singleton import SingletonMeta
from mlvc.utils.gen_utils import read_json_from_file, make_dir_if_not_exist


class MLVCApi(object):
    __metaclass__ = SingletonMeta

    API_URL = "http://localhost:8082"

    def __init__(self):
        self.api_key = None
        self.api_secret = None
        self.req_header = None

        user_home = expanduser("~")
        self.mlvc_dir = os.path.join(user_home, ".mlvc")
        make_dir_if_not_exist(self.mlvc_dir)
        self.init_keys()

    def init_keys(self):
        credentials = read_json_from_file(os.path.join(self.mlvc_dir, "credentials.json"))
        self.api_key = credentials["key"]
        self.api_secret = credentials["secret"]
        self.req_header = {
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret
        }

    def create_run(self, project_id, model_id, run_doc):
        run_basic_details = {
            "name": run_doc["name"],
            "description": run_doc["description"]
        }
        res = self.post("/v1.0/project/{}/model/{}/run/".format(project_id, model_id),
             data=run_basic_details, headers=self.req_header)
        remote_run_id = res["data"]["id"]
        self.put("/v1.0/project/{}/model/{}/run/{}".format(project_id, model_id, remote_run_id),
             data=run_doc, headers=self.req_header)
        
        return remote_run_id

    def upload_run_files(self, project_id, model_id, remote_run_id, run_zip_file_path):
        self.put("/v1.0/project/{}/model/{}/run/{}/upload".format(project_id, model_id, remote_run_id),
             file=run_zip_file_path, headers=self.req_header)

    def post(self, url, data={}, headers=None, file=None):
        files_payload = {}
        if file is not None:
            files_payload = {'file': open(file, 'rb')}
        r = requests.post(self.API_URL + url, files=files_payload, json=data, headers=headers)
        print(r.text)
        res_json = json.loads(r.text)
        return res_json

    def put(self, url, data={}, headers=None, file=None):
        files_payload = {}
        if file is not None:
            files_payload = {'file': open(file, 'rb')}
        r = requests.put(self.API_URL + url, files=files_payload, json=data, headers=headers)
        print(r.text)
        res_json = json.loads(r.text)
        return res_json
    
