import os
from os.path import expanduser
from tinydb import TinyDB, Query

from mlvc.utils.singleton import SingletonMeta
from mlvc.utils.gen_utils import read_json_from_file, make_dir_if_not_exist


class MLVCDB(object):
    __metaclass__ = SingletonMeta

    def __init__(self):
        self.db = None

        user_home = expanduser("~")
        self.mlvc_dir = os.path.join(user_home, ".mlvc")
        make_dir_if_not_exist(self.mlvc_dir)
        self.init_db()

    def init_db(self):
        self.db = TinyDB(os.path.join(self.mlvc_dir, "mlvc.json"))

    def insert_run(self, run):
        self.db.insert(run)
    
    def get_run(self, run_id):
        query = Query()
        doc = self.db.get(query.run_id == run_id)
        return doc
    
    def get_all_runs(self):
        return self.db.all()
    
    def update_run(self, run_id, obj):
        query = Query()
        self.db.update(obj, query.run_id == run_id)

    def remove_all_runs(self):
        self.db.truncate()

    @staticmethod
    def set_nested(path, val):
        def transform(doc):
            current = doc
            for key in path[:-1]:
                current = current[key]

            current[path[-1]] = val

        return transform