import unittest
from collections import Counter

from rand_range_from_coin import rand_range


def sequence_flip(outcomes):
    it = iter(outcomes)

    def flip():
        return next(it)

    return flip


class TestRandRangeFromCoin(unittest.TestCase):
    def test_single_value_needs_no_flips(self):
        def boom():
            raise AssertionError("should not flip when X == Y")

        self.assertEqual(rand_range(5, 5, flip=boom), 5)
        self.assertEqual(rand_range(-3, -3, flip=boom), -3)

    def test_swaps_when_bounds_are_reversed(self):
        flip = sequence_flip(["tails"])  # bit 0 -> 0
        self.assertEqual(rand_range(4, 3, flip=flip), 3)

    def test_two_outcomes_map_directly(self):
        self.assertEqual(rand_range(10, 11, flip=sequence_flip(["tails"])), 10)
        self.assertEqual(rand_range(10, 11, flip=sequence_flip(["heads"])), 11)

    def test_power_of_two_range_uses_all_bit_strings(self):
        # n = 4, k = 2: TT=0, TH=1, HT=2, HH=3
        cases = [
            (["tails", "tails"], 0),
            (["tails", "heads"], 1),
            (["heads", "tails"], 2),
            (["heads", "heads"], 3),
        ]
        for flips, expected in cases:
            with self.subTest(flips=flips):
                self.assertEqual(rand_range(0, 3, flip=sequence_flip(flips)), expected)

    def test_rejects_out_of_range_then_retries(self):
        # n = 3, k = 2. HH (3) is rejected; next TH (1) is accepted.
        flip = sequence_flip(["heads", "heads", "tails", "heads"])
        self.assertEqual(rand_range(0, 2, flip=flip), 1)

    def test_inclusive_negative_range(self):
        flip = sequence_flip(["tails", "tails"])  # 0
        self.assertEqual(rand_range(-2, 1, flip=flip), -2)
        flip = sequence_flip(["heads", "heads"])  # 3
        self.assertEqual(rand_range(-2, 1, flip=flip), 1)

    def test_stays_within_bounds(self):
        rng = __import__("random").Random(0)

        def flip():
            return "heads" if rng.random() < 0.5 else "tails"

        for _ in range(500):
            value = rand_range(-4, 7, flip=flip)
            self.assertGreaterEqual(value, -4)
            self.assertLessEqual(value, 7)

    def test_empirical_uniform_on_non_power_of_two(self):
        rng = __import__("random").Random(1)

        def flip():
            return "heads" if rng.random() < 0.5 else "tails"

        lo, hi = 2, 8  # n = 7, not a power of 2
        n = hi - lo + 1
        samples = 20000
        counts = Counter(rand_range(lo, hi, flip=flip) for _ in range(samples))
        self.assertEqual(set(counts), set(range(lo, hi + 1)))
        expected = samples / n
        chi2 = sum((counts[v] - expected) ** 2 / expected for v in range(lo, hi + 1))
        # df = 6; critical value at p=0.001 is ~22.46
        self.assertLess(chi2, 22.46)

    def test_rejection_does_not_bias_three_way_range(self):
        # Exhaust every 2-bit string: reject 11, keep 00/01/10 equally.
        outcomes = [
            ("tails", "tails"),
            ("tails", "heads"),
            ("heads", "tails"),
            ("heads", "heads"),
        ]
        accepted = []
        for bits in outcomes:
            try:
                accepted.append(rand_range(0, 2, flip=sequence_flip(bits)))
            except StopIteration:
                pass  # rejected draw ran out of bits
        self.assertEqual(sorted(accepted), [0, 1, 2])
        self.assertEqual(len(accepted), 3)


if __name__ == "__main__":
    unittest.main()
