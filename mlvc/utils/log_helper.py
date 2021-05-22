import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        message_dict = {"payload": message_dict}
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


class StdoutLogger(object):
    def __init__(self, stdout_log_file_path):
        self.terminal = sys.stdout
        self.stdout_log_file = open(stdout_log_file_path, "a")

    def write(self, message):
        self.terminal.write(message)
        self.stdout_log_file.write(message)

    def flush(self):
        pass
