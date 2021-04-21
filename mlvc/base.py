import os
from os.path import expanduser
from tinydb import TinyDB, Query

from singleton import SingletonMeta
from utils.gen_utils import read_json_from_file, write_json_to_file, make_tarfile, make_dir_if_not_exist


class MLVCBase(object):
    __metaclass__ = SingletonMeta

    def __init__(self):
        # API Key
        self.api_key = None
        self.api_secret = None
        self.req_header = None

        self.db = None

        # Project Details
        self.project_id = None
        self.model_id = None
        self.run_id = None
        self.run_dir = None

        user_home = expanduser("~")
        self.mlvc_dir = os.path.join(user_home, ".mlvc")
        make_dir_if_not_exist(self.mlvc_dir)

        # Init functions
        self.init_keys()
        self.init_db()

    def init_keys(self):
        credentials = read_json_from_file(os.path.join(self.mlvc_dir, "credentials.json"))
        self.api_key = credentials["key"]
        self.api_secret = credentials["secret"]
        self.req_header = {
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret
        }

    def init_db(self):
        self.db = TinyDB(os.path.join(self.mlvc_dir, "mlvc.json"))

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


