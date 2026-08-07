from abc import ABC


class SimpleTaskManagementSystem(ABC):
    """
    `SimpleTaskManagementSystem` interface.
    """

    def add_task(self, timestamp: int, name: str, priority: int) -> str:
        return ""

    def update_task(self, timestamp: int, task_id: str, name: str, priority: int) -> bool:
        return False

    def get_task(self, timestamp: int, task_id: str) -> str | None:
        return None

    def search_tasks(self, timestamp: int, name_filter: str, max_results: int) -> list[str]:
        return []

    def list_tasks_sorted(self, timestamp: int, limit: int) -> list[str]:
        return []

    def add_user(self, timestamp: int, user_id: str, quota: int) -> bool:
        return False

    def assign_task(self, timestamp: int, task_id: str, user_id: str, finish_time: int) -> bool:
        return False

    def get_user_tasks(self, timestamp: int, user_id: str) -> list[str]:
        return []

    def complete_task(self, timestamp: int, task_id: str, user_id: str) -> bool:
        return False

    def get_overdue_assignments(self, timestamp: int, user_id: str) -> list[str]:
        return []
