import os
from shutil import copyfile
from secrets import token_hex
from tinydb import TinyDB, Query

from base import MLVCBase
from utils.gen_utils import read_json_from_file, write_json_to_file, make_tarfile, make_dir_if_not_exist
from uploader import post

from modules.git.gitutils import GITUtils


class MLVC(MLVCBase):

    def __init__(self):
        super(MLVC, self).__init__()
        self.git_utils = GITUtils()

    def set_params(self, project_id, model_id):
        self.project_id = project_id
        self.model_id = model_id

    def create_run(self):
        self.check_init()
        self.run_id = token_hex(16)
        self.run_dir = os.path.join(self.mlvc_dir, self.run_id)
        make_dir_if_not_exist(self.run_dir)

        repo_details = self.git_utils.get_repo_details()
        git_diff_file_name = "code_diff.patch"
        self.git_utils.write_diff(os.path.join(self.run_dir, git_diff_file_name))
        repo_details["diff_file_name"] = git_diff_file_name

        run = {
            'run_id': self.run_id,
            "name": self.run_id,
            "data": [],
            "configs": [],
            "code": {
                "git": repo_details
            },
            "logs": [],
            "output": [],
            "extra_info": {},
            "status": "draft"
        }
        self.db.insert(run)

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
