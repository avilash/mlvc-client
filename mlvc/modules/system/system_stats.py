import time
import psutil
import threading
import GPUtil


class SystemStats(threading.Thread):

    def __init__(self, logger):
        super().__init__()
        self.should_run = True
        self.gpus = GPUtil.getGPUs()
        self.logger = logger

    def run(self):
        while self.should_run:
            cpu_per = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            mem_per = memory.percent
            gpu_stats = []
            for gpu in self.gpus:
                gpu_stats.append({
                    "name": gpu.name,
                    "uuid": gpu.uuid,
                    "load": gpu.load,
                    "memory_total": gpu.memoryTotal,
                    "memory_used": gpu.memoryUsed,
                    "memory_free": gpu.memoryFree,
                    "driver": gpu.driver,
                    "serial": gpu.serial,
                    "temperature": gpu.temperature,
                })
            system_stats = {
                "cpu": {
                    "percentage": cpu_per,
                    "memory": mem_per
                },
                "gpu": gpu_stats
            }
            print ("Hello")
            self.logger.debug(system_stats)
            time.sleep(1)

    def stop(self):
        self.should_run = False
