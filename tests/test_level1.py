import inspect
import os
import sys
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from simple_task_management_system_impl import SimpleTaskManagementSystemImpl


class Level1Tests(unittest.TestCase):
    """
    The test suit below includes 10 tests for Level 1.

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
    def test_level_1_case_01_basic_task_creation(self):
        self.assertTrue(self.system.create_task(1, 'task1', 'Write documentation'))
        self.assertEqual(self.system.get_task(2, 'task1'), 'Write documentation')

    @timeout(0.4)
    def test_level_1_case_02_duplicate_task_creation_fails(self):
        self.assertTrue(self.system.create_task(1, 'task2', 'Initial description'))
        self.assertFalse(self.system.create_task(2, 'task2', 'Duplicate description'))
        self.assertEqual(self.system.get_task(3, 'task2'), 'Initial description')

    @timeout(0.4)
    def test_level_1_case_03_update_existing_task(self):
        self.assertTrue(self.system.create_task(1, 'task3', 'Original description'))
        self.assertTrue(self.system.update_task(2, 'task3', 'Updated description'))
        self.assertEqual(self.system.get_task(3, 'task3'), 'Updated description')

    @timeout(0.4)
    def test_level_1_case_04_update_nonexistent_task_fails(self):
        self.assertFalse(self.system.update_task(1, 'nonexistent', 'Some description'))

    @timeout(0.4)
    def test_level_1_case_05_get_nonexistent_task_returns_null(self):
        self.assertIsNone(self.system.get_task(1, 'missing_task'))

    @timeout(0.4)
    def test_level_1_case_06_delete_existing_task(self):
        self.assertTrue(self.system.create_task(1, 'task4', 'To be deleted'))
        self.assertTrue(self.system.delete_task(2, 'task4'))
        self.assertIsNone(self.system.get_task(3, 'task4'))

    @timeout(0.4)
    def test_level_1_case_07_delete_nonexistent_task_fails(self):
        self.assertFalse(self.system.delete_task(1, 'never_existed'))

    @timeout(0.4)
    def test_level_1_case_08_recreate_after_deletion(self):
        self.assertTrue(self.system.create_task(1, 'task5', 'First version'))
        self.assertEqual(self.system.get_task(2, 'task5'), 'First version')
        self.assertTrue(self.system.delete_task(3, 'task5'))
        self.assertIsNone(self.system.get_task(4, 'task5'))
        self.assertTrue(self.system.create_task(5, 'task5', 'Second version'))
        self.assertEqual(self.system.get_task(6, 'task5'), 'Second version')

    @timeout(0.4)
    def test_level_1_case_09_multiple_operations_sequence(self):
        self.assertTrue(self.system.create_task(1, 'taskA', 'Description A'))
        self.assertTrue(self.system.create_task(2, 'taskB', 'Description B'))
        self.assertTrue(self.system.create_task(3, 'taskC', 'Description C'))
        self.assertEqual(self.system.get_task(4, 'taskB'), 'Description B')
        self.assertTrue(self.system.update_task(5, 'taskA', 'New Description A'))
        self.assertTrue(self.system.delete_task(6, 'taskC'))
        self.assertEqual(self.system.get_task(7, 'taskA'), 'New Description A')
        self.assertIsNone(self.system.get_task(8, 'taskC'))
        self.assertFalse(self.system.update_task(9, 'taskC', 'Cannot update deleted'))

    @timeout(0.4)
    def test_level_1_case_10_comprehensive_crud_operations(self):
        self.assertTrue(self.system.create_task(1, 'task1', 'Task 1'))
        self.assertTrue(self.system.create_task(2, 'task2', 'Task 2'))
        self.assertTrue(self.system.create_task(3, 'task3', 'Task 3'))
        self.assertFalse(self.system.create_task(4, 'task1', 'Duplicate'))
        self.assertTrue(self.system.update_task(5, 'task2', 'Updated Task 2'))
        self.assertEqual(self.system.get_task(6, 'task1'), 'Task 1')
        self.assertEqual(self.system.get_task(7, 'task2'), 'Updated Task 2')
        self.assertTrue(self.system.delete_task(8, 'task3'))
        self.assertFalse(self.system.delete_task(9, 'task3'))
        self.assertIsNone(self.system.get_task(10, 'task3'))
        self.assertTrue(self.system.create_task(11, 'task4', 'Task 4'))
        self.assertEqual(self.system.get_task(12, 'task4'), 'Task 4')
