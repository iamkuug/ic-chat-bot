from contextlib import contextmanager
from time import time
from typing import Dict
from utils.logger import *
import json

class RequestProfiler:
    def __init__(self):
        self.start_time = time()
        self.timings: Dict[str, float] = {}
    
    @contextmanager
    def measure(self, name: str):
        start = time()
        yield
        self.timings[name] = time() - start
    
    def report(self) -> None:
        total_time = time() - self.start_time
        timing_report = {
            "total_seconds": round(total_time, 2),
            "operations": {
                name: {
                    "seconds": round(duration, 2),
                    "percentage": round((duration/total_time) * 100, 2)
                }
                for name, duration in self.timings.items()
            }
        }
        logger.info(f"Request timing report: {json.dumps(timing_report, indent=2)}")
