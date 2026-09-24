from itertools import combinations

from get_minimum_conflicts import (
    brute_minimum_conflicts,
    getMinimumConflicts,
    merge_inversions,
)


def all_merges(primary: str, secondary: str):
    n, m = len(primary), len(secondary)
    for idx in combinations(range(n + m), n):
        p_pos = set(idx)
        p = s = 0
        out = []
        for pos in range(n + m):
            if pos in p_pos:
                out.append(primary[p])
                p += 1
            else:
                out.append(secondary[s])
                s += 1
        yield "".join(out)


def brute_enum(primary: str, secondary: str) -> int:
    return min(merge_inversions(merged) for merged in all_merges(primary, secondary))


def check(primary: str, secondary: str, expected=None):
    got = getMinimumConflicts(primary, secondary)
    if expected is not None:
        assert got == expected, (primary, secondary, got, expected)
    if len(primary) + len(secondary) <= 12:
        enum = brute_enum(primary, secondary)
        rec = brute_minimum_conflicts(primary, secondary)
        assert got == enum == rec, (primary, secondary, got, enum, rec)
    return got


def test_samples():
    assert check("zc", "d", 2) == 2
    assert check("dae", "add", 1) == 1
    assert check("aaa", "abb", 0) == 0


def test_single_and_equal():
    assert check("a", "b", 0) == 0
    assert check("b", "a", 0) == 0
    assert check("a", "a", 0) == 0
    assert check("z", "a", 0) == 0
    assert check("abc", "abc", 0) == 0
    assert check("aaa", "aaa", 0) == 0


def test_internal_inversions_must_count():
    assert check("ba", "a", 1) == 1
    assert check("cba", "a", 3) == 3
    assert check("ba", "ba", 3) == 3


def test_concatenation_vs_interleave():
    assert check("az", "by") == check("by", "az")
    assert check("z", "yxw") == check("yxw", "z")
    assert check("abc", "xyz", 0) == 0
    assert check("xyz", "abc", 0) == 0


def test_all_decreasing():
    assert check("cba", "cba") == brute_enum("cba", "cba")
    assert check("dcba", "e") == brute_enum("dcba", "e")


def test_mixed_letters():
    cases = [
        ("a", "z"),
        ("za", "yb"),
        ("m", "n"),
        ("ab", "ba"),
        ("ba", "ab"),
        ("abc", "cba"),
        ("dae", "add"),
        ("zzz", "aaa"),
        ("aaa", "zzz"),
        ("azaz", "baba"),
        ("dcba", "abcd"),
        ("hello", "world"),
        ("zzzz", "zzzz"),
        ("abcd", "abdc"),
        ("b", "ca"),
        ("ca", "b"),
        ("mb", "na"),
        ("da", "c"),
        ("zc", "d"),
        ("aaab", "bbbc"),
    ]
    for p, s in cases:
        check(p, s)


def test_symmetric():
    for p, s in [("dae", "add"), ("zc", "d"), ("ba", "ab"), ("xyz", "abc")]:
        assert getMinimumConflicts(p, s) == getMinimumConflicts(s, p)


def test_long_no_conflict():
    p = "a" * 1000
    s = "b" * 1000
    assert getMinimumConflicts(p, s) == 0
    assert getMinimumConflicts(s, p) == 0


def test_long_forced_inversions():
    p = "c" * 200 + "a" * 200
    s = "b" * 200
    got = getMinimumConflicts(p, s)
    # Best merge is all b's first: each primary c-before-a inversion (200*200)
    # plus each b before each a (200*200). c vs b is not an inversion.
    assert got == 200 * 200 + 200 * 200


def test_worst_case_speed():
    p = ("zyxwvutsrqponmlkjihgfedcba" * 40)[:1000]
    s = ("abcdefghijklmnopqrstuvwxyz" * 40)[:1000]
    got = getMinimumConflicts(p, s)
    assert got >= 0
    assert isinstance(got, int)
