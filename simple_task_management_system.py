from abc import ABC


class SimpleTaskManagementSystem(ABC):
    """
    `SimpleTaskManagementSystem` interface.
    """

    def create_task(self, timestamp: int, task_id: str, description: str) -> bool:
        """
        Creates a new task with the specified `task_id` and
        `description`.
        Returns `True` if the task was created successfully, or
        `False` if a task with the `task_id` already exists.
        """
        # default implementation
        return False

    def update_task(self, timestamp: int, task_id: str, new_description: str) -> bool:
        """
        Updates the description of the task with the specified
        `task_id`.
        Returns `True` if the task was updated successfully, or
        `False` if the task does not exist.
        """
        # default implementation
        return False

    def get_task(self, timestamp: int, task_id: str) -> str | None:
        """
        Retrieves the description of the task with the specified
        `task_id`.
        Returns the task description if it exists, or `None`
        otherwise.
        """
        # default implementation
        return None

    def delete_task(self, timestamp: int, task_id: str) -> bool:
        """
        Deletes the task with the specified `task_id`.
        Returns `True` if the task was deleted successfully, or
        `False` if the task does not exist.
        """
        # default implementation
        return False
