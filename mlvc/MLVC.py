import json
import sys
import os
import time
from shutil import copyfile
from secrets import token_hex
from tinydb import Query
import logging

from mlvc.base import MLVCBase
from mlvc.utils.gen_utils import write_json_to_file, read_lines_from_file, make_tarfile, make_dir_if_not_exist
from mlvc.utils.uploader import post
from mlvc.utils.log_helper import CustomJsonFormatter, StdoutLogger

from mlvc.modules.git.gitutils import GITUtils
from mlvc.modules.system.system_stats import SystemStats


class MLVC(MLVCBase):

    def __init__(self):
        super(MLVC, self).__init__()
        self.run_logger = None
        self.metric_logger = None
        self.git_utils = GITUtils()
        self.system_stats_obj = None

    def set_params(self, project_id, model_id):
        self.project_id = project_id
        self.model_id = model_id

    def create_run(self, name="", tags=[], description=""):
        self.check_init()
        self.run_id = token_hex(16)
        self.run_dir = os.path.join(self.mlvc_dir, self.run_id)
        make_dir_if_not_exist(self.run_dir)

        git_folder = os.path.join(self.run_dir, "git")
        make_dir_if_not_exist(git_folder)
        repo_details = self.git_utils.get_repo_details()
        git_diff_file_name = "code_diff.patch"
        self.git_utils.write_diff(os.path.join(git_folder, git_diff_file_name))
        repo_details["diff_file_name"] = git_diff_file_name

        log_details = self.init_loggers()

        self.system_stats_obj = SystemStats(self.system_stats_logger)
        self.system_stats_obj.start()

        run = {
            "run_id": self.run_id,
            "name": name,
            "description": description,
            "tags": tags,

            "system_info": self.system_stats_obj.get_system_info(),

            "ann": {},
            "code": {
                "git": repo_details,
                "files": []
            },
            "config": {},

            "model": {},

            "logs": log_details,
            "results": {},

            "artifacts": {},

            "extra_info": {},
            "status": "draft",

            "created_at": time.time(),
        }
        self.db.insert(run)

    # ******************** DATA ******************** #
    def add_annotation(self, ann_input, ann_input_type):
        self.check_init()
        ann_folder = os.path.join(self.run_dir, "ann")
        make_dir_if_not_exist(ann_folder)

        if ann_input_type == "json_file":
            ann_file_name = "data.json"
            ann_file_path = os.path.join(ann_folder, ann_file_name)
            copyfile(ann_input, ann_file_path)
        if ann_input_type == "json":
            ann_file_name = "data.json"
            ann_file_path = os.path.join(ann_folder, ann_file_name)
            write_json_to_file(ann_input, ann_file_path)
        elif ann_input_type == "csv_file":
            ann_file_name = "data.csv"
            ann_file_path = os.path.join(ann_folder, ann_file_name)
            copyfile(ann_input, ann_file_path)
        elif ann_input_type == "dataframe":
            ann_file_name = "data.csv"
            ann_file_path = os.path.join(ann_folder, ann_file_name)
            ann_input.to_csv(ann_file_path)
        else:
            raise Exception("No proper input type mentioned")

        query = Query()
        ann_obj = {
            "type": ann_input_type,
            "file_name": ann_file_name,
        }
        self.db.update({"ann": ann_obj}, query.run_id == self.run_id)

    # ******************** CONFIG ******************** #
    def add_config(self, config_input):
        self.check_init()
        query = Query()

        doc = self.db.get(query.run_id == self.run_id)
        config = doc["config"]
        config.update(config_input)
        self.db.update({"config": config}, query.run_id == self.run_id)

    # ******************** CODE ******************** #
    def add_code_file(self, file_path):
        self.check_init()
        file_name = os.path.basename(file_path)
        code_dir = os.path.join(self.run_dir, "code")
        make_dir_if_not_exist(code_dir)
        copyfile(file_path, os.path.join(code_dir, file_name))
        query = Query()
        doc = self.db.get(query.run_id == self.run_id)
        code_files = doc["code"]["files"]
        code_files.append(file_name)
        self.db.update(self.set_nested(["code", "files"], code_files))

    # ******************** LOGS ******************** #
    def log(self, line):
        self.check_init()
        self.run_logger.debug(line)

    def log_metric(self, metric_input):
        self.check_init()
        self.metric_logger.debug(metric_input)

    # ******************** RESULTS ******************** #
    def add_results(self, metric_input):
        self.check_init()
        query = Query()
        doc = self.db.get(query.run_id == self.run_id)
        results = doc["results"]
        results.update(metric_input)
        self.db.update({"results": results}, query.run_id == self.run_id)

    def append_final_metric_results(self):
        self.check_init()
        query = Query()
        doc = self.db.get(query.run_id == self.run_id)
        metric_logs = read_lines_from_file(os.path.join(self.run_dir, doc["logs"]["metric"]["file_name"]))
        run_results = doc["results"]
        metric_final_results = {}
        for log in metric_logs:
            log_json = json.loads(log)
            for key, val in log_json["payload"].items():
                metric_final_results[key] = val
        for key, val in metric_final_results.items():
            if key not in run_results:
                run_results[key] = val
        return run_results

    # ******************** COMMIT ******************** #
    def commit(self):
        self.check_init()
        query = Query()
        doc = self.db.get(query.run_id == self.run_id)
        # Time
        created_time = doc["created_at"]
        now = time.time()
        training_time = now - created_time
        # Stop sstem logger
        self.system_stats_obj.stop()
        # Get final metric results
        final_results = self.append_final_metric_results()
        self.db.update({"status": "submitted", "training_time": training_time, "results": final_results},
                       query.run_id == self.run_id)
        self.remove_loggers()

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
        post("/project/" + self.project_id + "/model/" + self.model_id + "/run/" + self.run_id + "/files",
             files=files, headers=self.req_header)
        self.db.update({"status": "uploaded"}, query.run_id == self.run_id)

    # ******************** Statictics ******************** #
    def get_all_runs(self):
        return self.db.all()

    def remove_all_runs(self):
        self.db.truncate()

    # ******************** Logging ******************** #

    def init_loggers(self):
        stdout_log_file_name = "stdout.log"
        run_log_file_name = "run.log"
        metric_log_file_name = "metric.log"
        system_log_file_name = "system_stats.log"

        file_log_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')

        stdout_log_file_path = os.path.join(self.run_dir, stdout_log_file_name)
        sys.stdout = StdoutLogger(stdout_log_file_path)

        self.run_logger = logging.getLogger("run")
        self.run_logger.setLevel(logging.DEBUG)
        run_log_file_path = os.path.join(self.run_dir, run_log_file_name)
        run_file_handler = logging.FileHandler(run_log_file_path)
        run_file_handler.setFormatter(file_log_formatter)
        self.run_logger.addHandler(run_file_handler)

        self.metric_logger = logging.getLogger("metric")
        self.metric_logger.setLevel(logging.DEBUG)
        metric_log_file_path = os.path.join(self.run_dir, metric_log_file_name)
        metric_file_handler = logging.FileHandler(metric_log_file_path)
        metric_file_handler.setFormatter(file_log_formatter)
        self.metric_logger.addHandler(metric_file_handler)

        self.system_stats_logger = logging.getLogger("system_stats")
        self.system_stats_logger.setLevel(logging.DEBUG)
        system_log_file_path = os.path.join(self.run_dir, system_log_file_name)
        system_log_file_handler = logging.FileHandler(system_log_file_path)
        system_log_file_handler.setFormatter(file_log_formatter)
        self.system_stats_logger.addHandler(system_log_file_handler)

        return {
            "stdout": {"file_name": stdout_log_file_name},
            "run": {"file_name": run_log_file_name},
            "metric": {"file_name": metric_log_file_name},
            "system": {"file_name": system_log_file_name},
        }

    def remove_loggers(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        if self.run_logger is not None:
            while self.run_logger.hasHandlers():
                self.run_logger.removeHandler(self.run_logger.handlers[0])
            self.run_logger = None
        if self.metric_logger is not None:
            while self.metric_logger.hasHandlers():
                self.metric_logger.removeHandler(self.metric_logger.handlers[0])
            self.metric_logger = None

    # ******************** DB Functions ******************** #

    @staticmethod
    def set_nested(path, val):
        def transform(doc):
            current = doc
            for key in path[:-1]:
                current = current[key]

            current[path[-1]] = val

        return transform

