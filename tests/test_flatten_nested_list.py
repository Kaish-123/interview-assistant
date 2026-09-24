import unittest

from flatten_nested_list import flatten, run_checks


class TestFlattenNestedList(unittest.TestCase):
    def test_main_example(self):
        self.assertEqual(flatten([1, [2, [3, 4]], 5]), [1, 2, 3, 4, 5])

    def test_does_not_mutate_input(self):
        nested = [1, [2, [3, 4]], 5]
        original = [1, [2, [3, 4]], 5]
        flatten(nested)
        self.assertEqual(nested, original)

    def test_empty(self):
        self.assertEqual(flatten([]), [])

    def test_already_flat(self):
        self.assertEqual(flatten([1, 2, 3]), [1, 2, 3])

    def test_deeper_nesting(self):
        self.assertEqual(flatten([[[1]], [2, [3, [4]]]]), [1, 2, 3, 4])

    def test_empty_inner_lists(self):
        self.assertEqual(flatten([1, [], [2, []], 3]), [1, 2, 3])

    def test_mixed_types(self):
        self.assertEqual(
            flatten(["a", [1, [None, True]], (2, 3)]),
            ["a", 1, None, True, (2, 3)],
        )

    def test_assessment_harness(self):
        run_checks()


if __name__ == "__main__":
    unittest.main()
