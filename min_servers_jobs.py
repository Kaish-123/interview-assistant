"""
Minimum servers to schedule daily jobs (one job per server at a time).

Each job: (start_minute, duration_minutes) with start in [0, 1439].
If start + duration exceeds 1440, the job wraps past midnight.

Answer = maximum number of jobs running at any single minute (interval graph
chromatic number equals max clique for intervals on a line; on a circle we
split wrapped jobs into segments).
"""

from __future__ import annotations

MINUTES_PER_DAY = 1440


def min_servers(jobs: list[tuple[int, int]]) -> int:
    """
    Return the minimum number of servers needed (max concurrent jobs).

    Uses a sweep line over [0, 1440): +1 at segment start, -1 at segment end
    for half-open intervals [a, b). Wrapped jobs become two segments.
    Durations >= 1440 are handled via full-day layers plus a remainder arc.
    """
    full_layers = 0
    events: list[tuple[int, int]] = []

    for s, d in jobs:
        if d <= 0:
            continue
        s = s % MINUTES_PER_DAY
        full_layers += d // MINUTES_PER_DAY
        rem = d % MINUTES_PER_DAY
        if rem == 0:
            continue

        end = s + rem
        if end <= MINUTES_PER_DAY:
            events.append((s, 1))
            events.append((end, -1))
        else:
            # [s, 1440) and [0, end - 1440)
            events.append((s, 1))
            events.append((MINUTES_PER_DAY, -1))
            events.append((0, 1))
            events.append((end - MINUTES_PER_DAY, -1))

    # Merge deltas at the same coordinate; process ends (-1) before starts (+1)
    # at the same minute so [a,b) and [b,c) do not double-count b.
    if not events:
        return full_layers

    events.sort(key=lambda x: (x[0], x[1]))

    current = full_layers
    best = full_layers
    i = 0
    n = len(events)
    while i < n:
        pos = events[i][0]
        delta = 0
        while i < n and events[i][0] == pos:
            delta += events[i][1]
            i += 1
        current += delta
        best = max(best, current)

    return best


if __name__ == "__main__":
    # Example 1: expect 2
    ex1 = [(60, 120), (150, 60), (0, 90)]
    assert min_servers(ex1) == 2, ex1

    # Example 2: expect 2
    ex2 = [(1320, 360), (1380, 60)]
    assert min_servers(ex2) == 2, ex2

    print("min_servers examples OK:", min_servers(ex1), min_servers(ex2))
