"""Question 2: count perfect pairs.

A pair (x, y) is perfect iff:
  min(|x - y|, |x + y|) <= min(|x|, |y|)
  max(|x - y|, |x + y|) >= max(|x|, |y|)

For a = |x|, b = |y|, that is equivalent to max(a, b) <= 2 * min(a, b).
"""

from __future__ import annotations

from bisect import bisect_right
from typing import List


def getPerfectPairsCount(arr: List[int]) -> int:
    """Return the number of perfect pairs (i, j) with 0 <= i < j < n.

    Time: O(n log n). Space: O(n).
    Safe for n up to 2e5 and values in [-1e9, 1e9].
    """
    a = sorted(abs(x) for x in arr)
    n = len(a)
    count = 0
    right = 0
    for left in range(n):
        if right <= left:
            right = left + 1
        limit = a[left] * 2
        while right < n and a[right] <= limit:
            right += 1
        count += right - left - 1
    return count


def getPerfectPairsCountBisect(arr: List[int]) -> int:
    """Same result via binary search; kept as a cross-check."""
    a = sorted(abs(x) for x in arr)
    count = 0
    for i, value in enumerate(a):
        j = bisect_right(a, value * 2, lo=i + 1)
        count += j - i - 1
    return count
