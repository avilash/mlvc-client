import os
from os.path import expanduser

from mlvc.utils.singleton import SingletonMeta
from mlvc.mlvc_api import MLVCApi
from mlvc.mlvc_db import MLVCDB
from mlvc.utils.gen_utils import read_json_from_file, make_dir_if_not_exist


class MLVCBase(object):
    __metaclass__ = SingletonMeta

    def __init__(self):
        self.mlvc_api = MLVCApi()
        self.mlvc_db = MLVCDB()
        
        # Project Details
        self.project_id = None
        self.model_id = None

        # Current Run vars
        self.run_id = None
        self.run_dir = None
        self.run_logger = None
        self.metric_logger = None
        self.system_stats_logger = None
        self.system_stats_thread = None

        # Init functions
        user_home = expanduser("~")
        self.mlvc_dir = os.path.join(user_home, ".mlvc")
        make_dir_if_not_exist(self.mlvc_dir)

    def check_project_init(self):
        essentials_vars = [self.project_id, self.model_id]
        for var in essentials_vars:
            if var is None:
                raise Exception("MLVC project not inititialised")

    def check_run_init(self):
        essentials_vars = [self.run_id, self.run_dir, self.metric_logger, self.system_stats_logger, self.system_stats_thread]
        for var in essentials_vars:
            if var is None:
                raise Exception("MLVC run not created")