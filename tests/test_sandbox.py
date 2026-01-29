import inspect
import os
import sys
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from simple_task_management_system_impl import SimpleTaskManagementSystemImpl


class SandboxTests(unittest.TestCase):
    """
    The test suit below includes sandbox tests.

    All have the same score.
    You are not allowed to modify this file,
    but feel free to read the source code
    to better understand what is happening in every specific case.
    """

    failureException = Exception

    @classmethod
    def setUp(cls):
        cls.system = SimpleTaskManagementSystemImpl()

    @timeout(0.4)
    def test_basic_sandbox_operation(self):
        self.assertTrue(self.system.create_task(1, 'taskA', 'Initial Task A'))
        self.assertTrue(self.system.create_task(2, 'taskB', 'Initial Task B'))
        self.assertEqual(self.system.get_task(3, 'taskA'), 'Initial Task A')
        self.assertTrue(self.system.update_task(4, 'taskA', 'Updated Task A'))
        self.assertEqual(self.system.get_task(5, 'taskA'), 'Updated Task A')
        self.assertTrue(self.system.delete_task(6, 'taskA'))
        self.assertIsNone(self.system.get_task(7, 'taskA'))
        self.assertTrue(self.system.create_task(8, 'taskA', 'Recreated Task A'))
        self.assertFalse(self.system.create_task(9, 'taskA', 'Another Task A'))
        self.assertEqual(self.system.get_task(10, 'taskA'), 'Recreated Task A')
