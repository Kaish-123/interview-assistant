"""
Cars on a Bridge - Codility-style task.
Find the minimum number of drivers that must turn back so the bridge is never overloaded.
Bridge: max weight U, at most 2 cars at a time. Cars enter in order; when a new car enters,
the oldest leaves (FIFO). So at any time total weight of cars on bridge must be <= U.

Equivalent: maximize the number of cars that can cross (in order) such that
every consecutive pair in the chosen subsequence has sum <= U and each car <= U.
Answer = N - (max number that can cross).
"""


def solution(U, weight):
    n = len(weight)
    if n == 0:
        return 0

    # dp[i] = maximum length of a valid crossing subsequence ending at index i
    # Valid: each car <= U, and for every consecutive pair (a,b) in the subsequence, a+b <= U
    dp = [0] * n

    for i in range(n):
        if weight[i] > U:
            dp[i] = 0  # this car can never cross (even alone)
            continue
        best = 0
        for k in range(i):
            if weight[k] + weight[i] <= U and dp[k] > best:
                best = dp[k]
        dp[i] = 1 + best

    max_cross = max(dp) if dp else 0
    return n - max_cross


# --- Tests (from problem / your failing cases) ---
if __name__ == "__main__":
    assert solution(9, [5, 3, 8, 1, 8, 7, 7, 6]) == 4, "Example 1"
    assert solution(7, [7, 6, 5, 2, 7, 4, 5, 4]) == 5, "Example 2"
    assert solution(7, [3, 4, 3, 1]) == 0, "Example 3"
    assert solution(2, [3, 7, 5, 5, 6, 3, 9, 10, 8, 4]) == 10, "Example 4"
    print("All tests passed.")
