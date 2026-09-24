"""Generate a uniform integer in [X, Y] using only a fair coin.

A coin has two outcomes, so n = Y - X + 1 is not uniform unless n is a
power of 2. Build a k-bit number (k = ceil(log2(n))), map it to [0, 2^k),
and retry when the draw falls in the leftover region [n, 2^k). Every accepted
value then has probability 1 / 2^k, so the result is uniform on [X, Y].
"""

from __future__ import annotations

import random
from typing import Callable

CoinFlip = Callable[[], str]


def flip_coin() -> str:
    return random.choice(["heads", "tails"])


def _bit(flip: CoinFlip) -> int:
    return 1 if flip() == "heads" else 0


def rand_range(x: int, y: int, *, flip: CoinFlip = flip_coin) -> int:
    """Return a uniform random integer in [min(x, y), max(x, y)], inclusive.

    Uses only `flip` (heads/tails). Rejection sampling keeps the distribution
    unbiased when the span is not a power of 2.
    """
    if x > y:
        x, y = y, x
    n = y - x + 1
    if n == 1:
        return x

    k = (n - 1).bit_length()  # smallest k with 2**k >= n
    while True:
        value = 0
        for _ in range(k):
            value = (value << 1) | _bit(flip)
        if value < n:
            return x + value
