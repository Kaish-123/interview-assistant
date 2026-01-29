from simple_task_management_system import SimpleTaskManagementSystem


class SimpleTaskManagementSystemImpl(SimpleTaskManagementSystem):

    def __init__(self):
        # Dictionary to store tasks: task_id -> description
        self.tasks = {}

    def create_task(self, timestamp: int, task_id: str, description: str) -> bool:
        """
        Creates a new task with the specified task_id and description.
        Returns True if the task was created successfully, or False if a task with the task_id already exists.
        """
        if task_id in self.tasks:
            return False
        self.tasks[task_id] = description
        return True

    def update_task(self, timestamp: int, task_id: str, new_description: str) -> bool:
        """
        Updates the description of the task with the specified task_id.
        Returns True if the task was updated successfully, or False if the task does not exist.
        """
        if task_id not in self.tasks:
            return False
        self.tasks[task_id] = new_description
        return True

    def get_task(self, timestamp: int, task_id: str) -> str | None:
        """
        Retrieves the description of the task with the specified task_id.
        Returns the task description if it exists, or None otherwise.
        """
        return self.tasks.get(task_id)

    def delete_task(self, timestamp: int, task_id: str) -> bool:
        """
        Deletes the task with the specified task_id.
        Returns True if the task was deleted successfully, or False if the task does not exist.
        """
        if task_id not in self.tasks:
            return False
        del self.tasks[task_id]
        return True
