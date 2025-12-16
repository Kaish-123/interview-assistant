"""
Mock AWS Glue Framework for Local Testing
"""


class GlueContext:
    """Mock Glue context for local execution"""
    def __init__(self):
        self.spark_session = None

    def get_logger(self):
        """Return a simple logger"""
        return MockLogger()


class MockLogger:
    """Simple logger for local testing"""

    def info(self, message):
        print(f"[INFO] {message}")

    def error(self, message):
        print(f"[ERROR] {message}")

    def warn(self, message):
        print(f"[WARN] {message}")


def get_glue_context():
    """Get mock Glue context for local execution"""
    return GlueContext()


