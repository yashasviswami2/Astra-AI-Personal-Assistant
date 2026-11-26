import time
import threading

from collections import defaultdict, deque
from contextlib import contextmanager
from statistics import mean


class PerformanceMonitor:

    def __init__(self, max_samples=1000):

        self.max_samples = max_samples

        self.metrics = defaultdict(
            lambda: deque(maxlen=self.max_samples)
        )

        self.lock = threading.Lock()

    def record(self, operation, duration, success=True):

        with self.lock:

            self.metrics[operation].append({
                "duration_ms": duration * 1000,
                "success": success
            })

    @contextmanager
    def measure(self, operation):

        start = time.perf_counter()
        success = False

        try:
            yield
            success = True

        finally:
            self.record(
                operation,
                time.perf_counter() - start,
                success
            )

    def get_summary(self):

        summary = {}

        with self.lock:

            for operation, records in self.metrics.items():

                if not records:
                    continue

                durations = [
                    item["duration_ms"]
                    for item in records
                ]

                successful = sum(
                    item["success"]
                    for item in records
                )

                summary[operation] = {
                    "executions": len(records),
                    "average_ms": round(mean(durations), 2),
                    "minimum_ms": round(min(durations), 2),
                    "maximum_ms": round(max(durations), 2),
                    "success_rate": round(
                        successful / len(records) * 100,
                        2
                    )
                }

        return summary

    def reset(self):

        with self.lock:
            self.metrics.clear()


performance_monitor = PerformanceMonitor()
