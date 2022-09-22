import json
import sys
import os
import time
from shutil import copyfile
from secrets import token_hex
import logging

from mlvc.base import MLVCBase
from mlvc.utils.gen_utils import write_json_to_file, read_lines_from_file, make_tarfile, make_dir_if_not_exist
from mlvc.utils.log_helper import StdoutLogger, make_logger, remove_logger

from mlvc.modules.git.gitutils import GITUtils
from mlvc.modules.system.system_stats import SystemStats


class MLVC(MLVCBase):

    def __init__(self):
        super(MLVC, self).__init__()
        self.git_utils = GITUtils()

    def set_params(self, project_id, model_id):
        self.project_id = project_id
        self.model_id = model_id

    def create_run(self, name="", description=""):
        self.check_project_init()
        # Create run id and folder
        self.run_id = token_hex(16)
        self.run_dir = os.path.join(self.mlvc_dir, self.run_id)
        make_dir_if_not_exist(self.run_dir)

        # Collect Git details
        git_folder = os.path.join(self.run_dir, "git")
        make_dir_if_not_exist(git_folder)
        repo_details = self.git_utils.get_repo_details()
        git_diff_file_name = "code_diff.patch"
        self.git_utils.write_diff(os.path.join(git_folder, git_diff_file_name))
        repo_details["diff_file_name"] = git_diff_file_name

        # Make loggers
        log_details = self.init_loggers()

        # Start system stats thread
        self.system_stats_thread = SystemStats(self.system_stats_logger)
        self.system_stats_thread.start()

        # Build run object
        run = {
            "project_id": self.project_id,
            "model_id": self.model_id,
            "run_id": self.run_id,
            "remote_run_id": "",
            "name": name,
            "description": description,
            "run_dir": self.run_dir,

            "system_info": self.system_stats_thread.get_system_info(),

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
        self.mlvc_db.insert_run(run)

    # ******************** Add Data ******************** #
    def add_annotation(self, ann_input, ann_input_type, run_id=None):
        run_id, run_doc = self.get_run(run_id)
        run_dir = run_doc["run_dir"]
        
        ann_folder = os.path.join(run_dir, "ann")
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

        ann_obj = {
            "type": ann_input_type,
            "file_name": ann_file_name,
        }
        self.mlvc_db.update_run(run_id, ann_obj)

    # ******************** Add Code ******************** #
    def add_code_file(self, file_path, run_id=None):
        run_id, run_doc = self.get_run(run_id)
        run_dir = run_doc["run_dir"]

        file_name = os.path.basename(file_path)
        code_dir = os.path.join(run_dir, "code")
        make_dir_if_not_exist(code_dir)
        copyfile(file_path, os.path.join(code_dir, file_name))
        code_files = run_doc["code"]["files"]
        code_files.append(file_name)

        self.mlvc_db.update_run(run_id, self.mlvc_db.set_nested(["code", "files"], code_files))

    # ******************** Add Config ******************** #
    def add_config(self, config_input, run_id=None):
        run_id, run_doc = self.get_run(run_id)

        config = run_doc["config"]
        config.update(config_input)

        self.mlvc_db.update_run(run_id, {"config": config})

    # ******************** Add Logs ******************** #
    def log(self, line):
        self.check_project_init()
        self.check_run_init()
        self.run_logger.debug(line)

    def log_metric(self, metric_input):
        self.check_project_init()
        self.check_run_init()
        self.metric_logger.debug(metric_input)

    # ******************** Add Results ******************** #
    def add_result(self, result_obj, run_id=None):
        run_id, run_doc = self.get_run(run_id)

        results = run_doc["results"]
        results.update(result_obj)

        self.mlvc_db.update_run(run_id, {"results": results})

    # ******************** Commit / Upload ******************** #
    @staticmethod
    def append_final_metrics(run_doc):
        run_dir = run_doc["run_dir"]
        metric_logs = read_lines_from_file(os.path.join(run_dir, run_doc["logs"]["metric"]["file_name"]))
        run_results = run_doc["results"]
        metric_final_results = {}
        for log in metric_logs:
            log_json = json.loads(log)
            for key, val in log_json["payload"].items():
                metric_final_results[key] = val
        for key, val in metric_final_results.items():
            if key not in run_results:
                run_results[key] = val
        return run_results

    def commit(self, run_id=None):
        if run_id is None:
            self.check_project_init()
            self.check_run_init()
            # Stop system logger
            self.system_stats_thread.stop()
            # Remove Loggers
            self.remove_loggers()
        run_id, run_doc = self.get_run(run_id)
        
        # Training time
        training_time = time.time() - run_doc["created_at"]
        # Get final metric results
        final_results = self.append_final_metrics(run_doc)

        # Update
        self.mlvc_db.update_run(run_id, {"status": "submitted", "training_time": training_time, "results": final_results})

    def upload(self, run_id=None):
        run_id, run_doc = self.get_run(run_id)
        if run_doc["status"] != "submitted":
            raise Exception("Run either not commited or already uploaded")
        run_dir = run_doc["run_dir"]
        project_id = run_doc["project_id"]
        model_id = run_doc["model_id"]

        remote_run_id = self.mlvc_api.create_run(project_id, model_id, run_doc)
        self.mlvc_db.update_run(run_id, {"remote_run_id": remote_run_id})

        run_zip_file_path = os.path.join(self.mlvc_dir, run_id + ".tar.gz")
        make_tarfile(run_zip_file_path, run_dir)
        self.mlvc_api.upload_run_files(project_id, model_id, remote_run_id, run_zip_file_path)
        
        self.mlvc_db.update_run(run_id, {"status": "uploaded"})

    # ******************** Db Queries ******************** #
    def get_run(self, run_id=None):
        if run_id is None:
            self.check_project_init()
            self.check_run_init()
            run_id = self.run_id
        
        return run_id, self.mlvc_db.get_run(run_id)

    def get_all_runs(self):
        return self.mlvc_db.get_all_runs()

    def remove_all_runs(self):
        self.mlvc_db.remove_all_runs()

    # ******************** Logging ******************** #
    def init_loggers(self):
        logger_details = {
            "stdout": {"file_name": "stdout.log"},
            "run": {"file_name": "run.log"},
            "metric": {"file_name": "metric.log"},
            "system": {"file_name": "system_stats.log"},
        }

        stdout_log_file_path = os.path.join(self.run_dir, logger_details["stdout"]["file_name"])
        run_log_file_path = os.path.join(self.run_dir, logger_details["run"]["file_name"])
        metric_log_file_path = os.path.join(self.run_dir, logger_details["metric"]["file_name"])
        system_log_file_path = os.path.join(self.run_dir, logger_details["system"]["file_name"])

        sys.stdout = StdoutLogger(stdout_log_file_path)

        self.run_logger = make_logger("run", logging.DEBUG, run_log_file_path)
        self.metric_logger = make_logger("metric", logging.DEBUG, metric_log_file_path)
        self.system_stats_logger = make_logger("system_stats", logging.DEBUG, system_log_file_path)

        return logger_details

    def remove_loggers(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        remove_logger(self.run_logger)
        remove_logger(self.metric_logger)
        remove_logger(self.system_stats_logger)
