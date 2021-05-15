import time
from mlvc.MLVC import MLVC


mlvc_obj = MLVC()
mlvc_obj.set_params("6075bdd29b6f23000a9e1163", "1618337342618")
mlvc_obj.create_run(name="My Run", tags=["a", "b"], description="My test run")
mlvc_obj.add_annotation({"a": "aa"}, "json")
mlvc_obj.add_code_file("sample_code_upload.py")
mlvc_obj.add_config({"a": "aa"})
mlvc_obj.add_config({"b": "bb", "c": {"d": "dd"}})
mlvc_obj.log("Hi this is a sample log")
mlvc_obj.log_metric({"a": "aa", "b": "bb"})
mlvc_obj.log("Hi this is a second sample log")
mlvc_obj.log_metric({"c": "cc", "d": "dd"})
mlvc_obj.add_output({"b": "bb", "c": {"d": "dd"}})
time.sleep(3)
mlvc_obj.commit()
mlvc_obj.upload()
# print(mlvc_obj.get_all_runs())
mlvc_obj.remove_all_runs()
