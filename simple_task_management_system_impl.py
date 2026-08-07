from simple_task_management_system import SimpleTaskManagementSystem


class SimpleTaskManagementSystemImpl(SimpleTaskManagementSystem):

    def __init__(self):
        self._counter = 0
        self._tasks = {}
        self._users = {}
        self._assignments = []

    def add_task(self, timestamp: int, name: str, priority: int) -> str:
        self._counter += 1
        task_id = f"task_id_{self._counter}"
        self._tasks[task_id] = {
            "name": name,
            "priority": priority,
            "seq": self._counter,
        }
        return task_id

    def update_task(self, timestamp: int, task_id: str, name: str, priority: int) -> bool:
        if task_id not in self._tasks:
            return False
        task = self._tasks[task_id]
        task["name"] = name
        task["priority"] = priority
        return True

    def get_task(self, timestamp: int, task_id: str) -> str | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        return f'{{"name":"{task["name"]}","priority":{task["priority"]}}}'

    def search_tasks(self, timestamp: int, name_filter: str, max_results: int) -> list[str]:
        if max_results <= 0:
            return []
        matched = [
            (task_id, task)
            for task_id, task in self._tasks.items()
            if name_filter in task["name"]
        ]
        matched.sort(key=lambda item: (-item[1]["priority"], item[1]["seq"]))
        return [task_id for task_id, _ in matched[:max_results]]

    def list_tasks_sorted(self, timestamp: int, limit: int) -> list[str]:
        if limit <= 0:
            return []
        items = list(self._tasks.items())
        items.sort(key=lambda item: (-item[1]["priority"], item[1]["seq"]))
        return [task_id for task_id, _ in items[:limit]]

    def add_user(self, timestamp: int, user_id: str, quota: int) -> bool:
        if user_id in self._users:
            return False
        self._users[user_id] = quota
        return True

    def _active_assignments(self, user_id: str, timestamp: int) -> list[dict]:
        return [
            a for a in self._assignments
            if a["user_id"] == user_id
            and not a["completed"]
            and a["start"] <= timestamp < a["finish"]
        ]

    def assign_task(self, timestamp: int, task_id: str, user_id: str, finish_time: int) -> bool:
        if task_id not in self._tasks or user_id not in self._users:
            return False
        if len(self._active_assignments(user_id, timestamp)) >= self._users[user_id]:
            return False
        self._assignments.append({
            "task_id": task_id,
            "user_id": user_id,
            "start": timestamp,
            "finish": finish_time,
            "completed": False,
        })
        return True

    def get_user_tasks(self, timestamp: int, user_id: str) -> list[str]:
        active = self._active_assignments(user_id, timestamp)
        active.sort(key=lambda a: (a["finish"], a["start"]))
        return [a["task_id"] for a in active]

    def complete_task(self, timestamp: int, task_id: str, user_id: str) -> bool:
        if task_id not in self._tasks or user_id not in self._users:
            return False
        candidates = [
            a for a in self._assignments
            if a["task_id"] == task_id
            and a["user_id"] == user_id
            and not a["completed"]
            and a["start"] <= timestamp < a["finish"]
        ]
        if not candidates:
            return False
        earliest = min(candidates, key=lambda a: a["start"])
        earliest["completed"] = True
        return True

    def get_overdue_assignments(self, timestamp: int, user_id: str) -> list[str]:
        if user_id not in self._users:
            return []
        overdue = [
            a for a in self._assignments
            if a["user_id"] == user_id
            and not a["completed"]
            and a["finish"] <= timestamp
        ]
        overdue.sort(key=lambda a: (a["finish"], a["start"]))
        return [a["task_id"] for a in overdue]
