from MLVC import MLVC

mlvc_obj = MLVC()
mlvc_obj.set_params("6075bdd29b6f23000a9e1163", "1618337342618")
mlvc_obj.create_run()
mlvc_obj.add_data({"a": "b"}, "json")
mlvc_obj.add_config({"b": "c"}, "json")
mlvc_obj.commit()
mlvc_obj.upload()
# print(mlvc_obj.get_all_runs())
mlvc_obj.remove_all_runs()
