"""Minimum merge conflicts when interleaving two commit sequences.

Preserve the order of each branch. A conflict is an inversion: a lower-priority
commit (later letter) appears before a higher-priority commit (earlier letter).
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple


def _inversions(s: str) -> int:
    freq = [0] * 26
    inv = 0
    for ch in s:
        idx = ord(ch) - 97
        inv += sum(freq[idx + 1 :])
        freq[idx] += 1
    return inv


def _prefix_greater(s: str) -> List[List[int]]:
    """greater[i][c] = how many chars in s[:i] are strictly greater than chr(97+c)."""
    n = len(s)
    freq = [0] * 26
    greater = [[0] * 26 for _ in range(n + 1)]
    for i, ch in enumerate(s, start=1):
        freq[ord(ch) - 97] += 1
        running = 0
        for c in range(25, -1, -1):
            greater[i][c] = running
            running += freq[c]
    return greater


def getMinimumConflicts(primary: str, secondary: str) -> int:
    """Return the minimum inversion count over all order-preserving merges.

    n, m <= 1000. Time O(n*m), space O(n*m).
    """
    n = len(primary)
    m = len(secondary)
    p_gt = _prefix_greater(primary)
    s_gt = _prefix_greater(secondary)

    inf = 10**18
    dp = [[inf] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0

    for i in range(n + 1):
        for j in range(m + 1):
            cur = dp[i][j]
            if cur >= inf:
                continue
            if i < n:
                add = s_gt[j][ord(primary[i]) - 97]
                nxt = cur + add
                if nxt < dp[i + 1][j]:
                    dp[i + 1][j] = nxt
            if j < m:
                add = p_gt[i][ord(secondary[j]) - 97]
                nxt = cur + add
                if nxt < dp[i][j + 1]:
                    dp[i][j + 1] = nxt

    return _inversions(primary) + _inversions(secondary) + dp[n][m]


def merge_inversions(merged: str) -> int:
    return _inversions(merged)


def brute_minimum_conflicts(primary: str, secondary: str) -> int:
    """Enumerate every interleaving. Use only for small strings."""

    @lru_cache(maxsize=None)
    def dfs(i: int, j: int) -> Tuple[int, str]:
        if i == len(primary) and j == len(secondary):
            return 0, ""
        best = 10**18
        best_s = ""
        if i < len(primary):
            rest_inv, rest = dfs(i + 1, j)
            cand = primary[i] + rest
            inv = merge_inversions(cand)
            if inv < best:
                best, best_s = inv, cand
        if j < len(secondary):
            rest_inv, rest = dfs(i, j + 1)
            cand = secondary[j] + rest
            inv = merge_inversions(cand)
            if inv < best:
                best, best_s = inv, cand
        return best, best_s

    return dfs(0, 0)[0]
