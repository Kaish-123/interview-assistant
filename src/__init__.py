"""
Task package used by the unit tests.

The tests import modules via `__import__('src.taskX')` and then access the
module attribute on the `src` package, so we re-export task modules here.
"""

from . import task1, task2, task3, task4, task5, task6, task7  # noqa: F401

__all__ = ["task1", "task2", "task3", "task4", "task5", "task6", "task7"]

