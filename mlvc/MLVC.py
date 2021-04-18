import json
import os
from os.path import expanduser
from shutil import copyfile
from secrets import token_hex
import pandas as pd
from tinydb import TinyDB, Query

from singleton import SingletonMeta
from utils.gen_utils import read_json_from_file, write_json_to_file, make_tarfile, make_dir_if_not_exist
from uploader import post


class MLVC(object):
    # __metaclass__ = SingletonMeta

    def __init__(self):
        self.api_key = None
        self.api_secret = None
        self.req_header = None

        self.db = None
        self.project_id = None
        self.model_id = None
        self.run_id = None
        self.run_dir = None

        user_home = expanduser("~")
        self.mlvc_dir = os.path.join(user_home, ".mlvc")
        make_dir_if_not_exist(self.mlvc_dir)
        self.init_keys()
        self.init_db()

    def init_keys(self):
        credentials = read_json_from_file(os.path.join(self.mlvc_dir, "credentials.json"))
        self.api_key = credentials["key"]
        self.api_secret = credentials["secret"]
        self.req_header = {
            "api_key": self.api_key,
            "api_secret": self.api_secret
        }

    def init_db(self):
        self.db = TinyDB(os.path.join(self.mlvc_dir, "mlvc.json"))

    def set_params(self, project_id, model_id):
        self.project_id = project_id
        self.model_id = model_id

    def check_init(self, api=True, project=True, extr_vars=None):
        if extr_vars is None:
            extr_vars = []
        if api:
            api_key_vars = [self.api_key, self.api_secret, ]
            for var in api_key_vars:
                if var is None:
                    raise Exception("MLVC not configured")
        if project:
            project_vars = [self.project_id, self.model_id]
            for var in project_vars:
                if var is None:
                    raise Exception("MLVC not inititialised")
        for var in extr_vars:
            if var is None:
                raise Exception("Some Error")

    def create_run(self):
        self.check_init()
        self.run_id = token_hex(16)
        self.db.insert({
            'run_id': self.run_id,
            "name": self.run_id,
            "data": [],
            "configs": [],
            "logs": [],
            "output": [],
            "extra_info": {},
            "status": "draft"
        })
        self.run_dir = os.path.join(self.mlvc_dir, self.run_id)
        make_dir_if_not_exist(self.run_dir)

    # ******************** DATA ******************** #
    def add_data(self, data_input, data_input_type):
        self.check_init()
        query = Query()
        run_data = self.db.get(query.run_id == self.run_id)
        run_data = run_data["data"]
        data_file_name = "data_" + str(len(run_data))
        data_file_path = os.path.join(self.run_dir, data_file_name)

        if data_input_type == "json_file":
            copyfile(data_input, data_file_path)
        if data_input_type == "json":
            write_json_to_file(data_input, data_file_path)
        elif data_input_type == "csv_file":
            copyfile(data_input, data_file_path)
        elif data_input_type == "dataframe":
            data_input.to_csv(data_file_path)
        else:
            raise Exception("No proper input type mentioned")

        run_data.append({
            "type": data_input_type,
            "file_name": data_file_name,
        })
        self.db.update({'data': run_data}, query.run_id == self.run_id)

    # ******************** CONFIG ******************** #
    def add_config(self, config_input, config_input_type):
        self.check_init()
        query = Query()
        run_configs = self.db.get(query.run_id == self.run_id)
        run_configs = run_configs["configs"]
        config_file_name = "config_" + str(len(run_configs))
        config_file_path = os.path.join(self.run_dir, config_file_name)

        if config_input_type == "json_file":
            copyfile(config_input, config_file_path)
        if config_input_type == "json":
            write_json_to_file(config_input, config_file_path)
        else:
            raise Exception("No proper input type mentioned")

        run_configs.append({
            "type": config_input_type,
            "file_name": config_file_name,
        })
        self.db.update({'configs': run_configs}, query.run_id == self.run_id)

    def add_model_config(self):
        self.check_init()

    def add_hyper_params(self):
        self.check_init()

    # ******************** LOGS ******************** #
    def add_log_file(self):
        self.check_init()

    # ******************** OUTPUT ******************** #
    def add_output(self):
        self.check_init()

    # ******************** COMMIT ******************** #
    def commit(self):
        self.check_init()
        query = Query()
        doc = self.db.get(query.run_id == self.run_id)
        self.db.update({'status': "submitted"}, query.run_id == self.run_id)

    # ******************** UPLOAD ******************** #
    def upload(self):
        self.check_init()
        query = Query()
        doc = self.db.get(query.run_id == self.run_id)
        upload_file_path = os.path.join(self.mlvc_dir, self.run_id + ".tar.gz")
        make_tarfile(upload_file_path, self.run_dir)
        files = {"file": open(upload_file_path, "rb")}
        post("/project/" + self.project_id + "/model/" + self.model_id + "/run",
             data=doc, headers=self.req_header)
        post("/project/" + self.project_id + "/model/" + self.model_id + "/run/" + self.run_id,
             files=files, headers=self.req_header)
        self.db.update({'status': "uploaded"}, query.run_id == self.run_id)

    # ******************** Statictics ******************** #
    def get_all_runs(self):
        return self.db.all()

    def remove_all_runs(self):
        self.db.truncate()
