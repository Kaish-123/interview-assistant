import random
import unittest

from count_hand_moves import countHandMoves, min_moves_dp


def naive_thumb_on_note(notes):
    """The screenshot algorithm: always pin the thumb on the current left key."""
    if not notes:
        return 0
    move_count = 0
    start = notes[0]
    for note in notes:
        end = start + 4
        if note < start or note > end:
            start = note
            move_count += 1
    return move_count


class TestCountHandMoves(unittest.TestCase):
    def test_given_examples(self):
        self.assertEqual(countHandMoves([1, 2, 3, 4, 5, 4, 3, 2, 1]), 0)
        self.assertEqual(countHandMoves([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]), 1)

    def test_does_not_assume_thumb_on_first_note(self):
        # Screenshot code starts covering [10, 14] and moves on every descent.
        notes = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        self.assertEqual(naive_thumb_on_note(notes), 9)
        self.assertEqual(countHandMoves(notes), 1)

    def test_empty_and_null(self):
        self.assertEqual(countHandMoves([]), 0)
        self.assertEqual(countHandMoves(None), 0)

    def test_single_note(self):
        self.assertEqual(countHandMoves([1]), 0)
        self.assertEqual(countHandMoves([100]), 0)

    def test_exactly_one_span(self):
        self.assertEqual(countHandMoves([1, 5]), 0)
        self.assertEqual(countHandMoves([5, 1]), 0)
        self.assertEqual(countHandMoves([1, 5, 1, 5]), 0)

    def test_just_outside_span(self):
        self.assertEqual(countHandMoves([1, 6]), 1)
        self.assertEqual(countHandMoves([6, 1]), 1)

    def test_repeated_notes(self):
        self.assertEqual(countHandMoves([3, 3, 3, 3]), 0)

    def test_multiple_moves(self):
        self.assertEqual(countHandMoves([1, 6, 11]), 2)
        self.assertEqual(countHandMoves([1, 5, 9, 13]), 1)
        self.assertEqual(countHandMoves([1, 5, 6, 10]), 1)

    def test_oscillating_then_jump(self):
        self.assertEqual(countHandMoves([2, 6, 2, 6, 10]), 1)

    def test_matches_dp_on_random(self):
        rng = random.Random(42)
        for _ in range(200):
            n = rng.randint(0, 40)
            notes = [rng.randint(1, 30) for _ in range(n)]
            self.assertEqual(
                countHandMoves(notes),
                min_moves_dp(notes),
                notes,
            )


if __name__ == "__main__":
    unittest.main()
