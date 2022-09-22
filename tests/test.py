import time
from mlvc.MLVC import MLVC

run_id = None
mlvc_obj = MLVC()


mlvc_obj.set_params(1, 1)
mlvc_obj.create_run(name="My Run", description="My test run")
mlvc_obj.add_annotation({"bbox": [1, 1, 100, 100]}, "json", run_id=run_id)
mlvc_obj.add_code_file("tests/sample_code_upload.py", run_id=run_id)
mlvc_obj.add_config({"epochs": "100"}, run_id=run_id)
mlvc_obj.add_config({"lr": "0.01", "model": {"arch": "resnet"}}, run_id=run_id)
mlvc_obj.log("Hi this is a sample log")
mlvc_obj.log_metric({"epoch": "1", "loss": "0.9"})
mlvc_obj.log("Hi this is a second sample log")
mlvc_obj.log_metric({"epoch": "2", "loss": "0.5"})
mlvc_obj.add_result({"f1": "0.7", "details": {"prec": "0.8", "recall": "0.75"}}, run_id=run_id)
time.sleep(3)
mlvc_obj.commit()

mlvc_obj.upload(run_id=run_id)

print(mlvc_obj.get_all_runs())


# mlvc_obj.remove_all_runs()
