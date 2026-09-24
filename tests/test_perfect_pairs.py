from get_perfect_pairs_count import getPerfectPairsCount, getPerfectPairsCountBisect


def brute(arr):
    n = len(arr)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            x, y = arr[i], arr[j]
            a, b = abs(x), abs(y)
            if max(a, b) <= 2 * min(a, b):
                count += 1
    return count


def check(arr, expected=None):
    got = getPerfectPairsCount(arr)
    alt = getPerfectPairsCountBisect(arr)
    if expected is None:
        expected = brute(arr)
    assert got == expected == alt, (arr, got, alt, expected)
    return got


def test_samples():
    assert check([2, 5, -3], 2) == 2
    assert check([-9, 6, -2, 1], 2) == 2
    assert check([2, 1, 0], 1) == 1


def test_zeros_and_boundary():
    assert check([0, 0], 1) == 1
    assert check([0, 0, 0], 3) == 3
    assert check([0, 1], 0) == 0
    assert check([3, 6], 1) == 1
    assert check([3, 7], 0) == 0
    assert check([5, 5, 5], 3) == 3
    assert check([-5, 5, -5, 5], 6) == 6
    assert check([1, -1, 2, -2], 6) == 6
    assert check([-10**9, 10**9, -(10**9) // 2], None)


def test_random_small():
    import random

    rng = random.Random(42)
    for _ in range(80):
        n = rng.randint(2, 40)
        arr = [rng.randint(-30, 30) for _ in range(n)]
        check(arr)


def test_large_n_no_timeout():
    n = 20000
    arr = list(range(n))
    got = getPerfectPairsCount(arr)
    assert got == getPerfectPairsCountBisect(arr)
    assert got > 0
