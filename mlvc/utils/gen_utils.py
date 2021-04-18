import os
import json
import tarfile
import datetime


def make_dir_if_not_exist(path):
    if not os.path.exists(path):
        os.makedirs(path)


def write_json_to_file(data, filepath):
    with open(filepath, 'w', encoding='utf8') as outfile:
        json.dump(data, outfile, ensure_ascii=False)


def read_json_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    if type(data) is str:
        return json.loads(data)
    return data


def read_lines_from_file(file_path):
    data = []
    with open(file_path) as fp:
        for cnt, line in enumerate(fp):
            line = line.strip()
            data.append(line)
    return data


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
