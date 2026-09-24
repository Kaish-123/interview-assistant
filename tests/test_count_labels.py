import unittest

from count_labels import count_labels, run_checks


class TestCountLabels(unittest.TestCase):
    def test_main_example(self):
        labels = [" PASS ", "fail", "pass", "", " Fail ", "SKIP"]
        self.assertEqual(
            count_labels(labels),
            {"pass": 2, "fail": 2, "skip": 1},
        )

    def test_does_not_mutate_input(self):
        labels = [" PASS ", "fail", "pass", "", " Fail ", "SKIP"]
        original = list(labels)
        count_labels(labels)
        self.assertEqual(labels, original)
        self.assertIsNot(count_labels(labels), labels)

    def test_empty_input(self):
        self.assertEqual(count_labels([]), {})

    def test_blank_labels(self):
        self.assertEqual(count_labels(["", " ", "\t"]), {})

    def test_all_whitespace_variants_ignored(self):
        self.assertEqual(
            count_labels(["", " ", "\t", "\n", "\r", "\r\n", "\v", "\f", "  \t\n  "]),
            {},
        )

    def test_case_and_surrounding_whitespace(self):
        mixed_labels = [
            " Alpha ",
            "ALPHA",
            "beta",
            " Beta ",
            "BETA",
            "gamma",
        ]
        self.assertEqual(
            count_labels(mixed_labels),
            {"alpha": 2, "beta": 3, "gamma": 1},
        )

    def test_arbitrary_labels(self):
        labels = ["first", "second", "first", "third", "second"]
        self.assertEqual(
            count_labels(labels),
            {"first": 2, "second": 2, "third": 1},
        )

    def test_single_label(self):
        self.assertEqual(count_labels(["ok"]), {"ok": 1})

    def test_already_normalized(self):
        self.assertEqual(count_labels(["pass", "fail"]), {"pass": 1, "fail": 1})

    def test_preserves_internal_whitespace(self):
        labels = ["hello world", " Hello World ", "hello  world"]
        self.assertEqual(
            count_labels(labels),
            {"hello world": 2, "hello  world": 1},
        )

    def test_newlines_around_label(self):
        self.assertEqual(count_labels(["\nPASS\n", " pass "]), {"pass": 2})

    def test_mixed_blanks_and_values(self):
        labels = ["", " A ", " ", "a", "\t", "B"]
        self.assertEqual(count_labels(labels), {"a": 2, "b": 1})

    def test_punctuation_and_digits(self):
        labels = ["OK!", "ok!", " Test1 ", "TEST1", "123"]
        self.assertEqual(
            count_labels(labels),
            {"ok!": 2, "test1": 2, "123": 1},
        )

    def test_unicode_case(self):
        self.assertEqual(count_labels(["Café", "CAFÉ", " café "]), {"café": 3})

    def test_does_not_hardcode_known_labels(self):
        labels = ["red", "BLUE", " Red ", "green"]
        self.assertEqual(count_labels(labels), {"red": 2, "blue": 1, "green": 1})

    def test_first_seen_key_order(self):
        result = count_labels([" Z ", "a", "z", "A"])
        self.assertEqual(list(result.keys()), ["z", "a"])
        self.assertEqual(result, {"z": 2, "a": 2})

    def test_repeated_same_label(self):
        self.assertEqual(count_labels(["x"] * 10), {"x": 10})

    def test_assessment_harness(self):
        run_checks()


if __name__ == "__main__":
    unittest.main()
