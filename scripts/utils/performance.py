"""
Performance monitoring utilities
"""

import time
import functools
from typing import Callable, Any
from contextlib import contextmanager

from .logger import setup_logger

logger = setup_logger(__name__)


@contextmanager
def timer(operation_name: str, log_level: str = "info"):
    """
    Context manager for timing operations

    Usage:
        with timer("Processing file"):
            # do work
            pass
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        log_func = getattr(logger, log_level, logger.info)
        log_func(f"{operation_name} completed in {elapsed:.2f}s")


def timed(operation_name: str = None):
    """
    Decorator for timing function execution

    Usage:
        @timed("parse_data")
        def parse_data():
            pass
    """
    def decorator(func: Callable) -> Callable:
        name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"{name} completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{name} failed after {elapsed:.2f}s: {e}")
                raise

        return wrapper
    return decorator


class PerformanceMonitor:
    """Track performance metrics"""

    def __init__(self):
        self.metrics = {}

    def start(self, operation: str) -> None:
        """Start timing an operation"""
        self.metrics[operation] = {
            "start": time.time(),
            "end": None,
            "duration": None
        }

    def end(self, operation: str) -> float:
        """End timing an operation and return duration"""
        if operation not in self.metrics:
            logger.warning(f"Operation {operation} not started")
            return 0.0

        end_time = time.time()
        self.metrics[operation]["end"] = end_time
        duration = end_time - self.metrics[operation]["start"]
        self.metrics[operation]["duration"] = duration

        return duration

    def get_summary(self) -> dict:
        """Get summary of all metrics"""
        summary = {}
        total_duration = 0.0

        for operation, data in self.metrics.items():
            if data["duration"] is not None:
                summary[operation] = {
                    "duration": f"{data['duration']:.2f}s"
                }
                total_duration += data["duration"]

        summary["total"] = f"{total_duration:.2f}s"
        return summary

    def log_summary(self) -> None:
        """Log performance summary"""
        summary = self.get_summary()
        logger.info("Performance Summary:")
        for operation, metrics in summary.items():
            if operation != "total":
                logger.info(f"  {operation}: {metrics['duration']}")
        logger.info(f"  Total: {summary['total']}")
