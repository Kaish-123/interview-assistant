"""
Minimum steps to reach the last room (treasure). From index i you jump forward
by the instruction value. Spending $1 at a room lets you use (value - 1) or
(value + 1) instead for that move, if the resulting jump stays valid and positive.
"""

from collections import deque


def find_treasure(instructions, money):
    """
    Return the minimum number of moves to reach the last index, or None if impossible.

    Time complexity: O(I * M * K) worst case where I is len(instructions), M is money,
    and K is the bounded branching factor per state (here at most 3 edges per state).
    In practice, BFS visits at most O(I * (M + 1)) distinct (position, money_left) states.

    Space complexity: O(I * (M + 1)) for the visited set and queue.
    """
    n = len(instructions)
    if n == 0:
        return None
    goal = n - 1
    if goal == 0:
        return 0

    q = deque([(0, money)])
    visited = {(0, money)}
    steps = 0

    while q:
        for _ in range(len(q)):
            pos, m = q.popleft()
            if pos == goal:
                return steps
            v = instructions[pos]

            nxt = pos + v
            if nxt == goal:
                return steps + 1
            if 0 <= nxt < n and (nxt, m) not in visited:
                visited.add((nxt, m))
                q.append((nxt, m))

            if m >= 1:
                if v - 1 >= 1:
                    nxt = pos + v - 1
                    if nxt == goal:
                        return steps + 1
                    if 0 <= nxt < n and (nxt, m - 1) not in visited:
                        visited.add((nxt, m - 1))
                        q.append((nxt, m - 1))
                nxt = pos + v + 1
                if nxt == goal:
                    return steps + 1
                if 0 <= nxt < n and (nxt, m - 1) not in visited:
                    visited.add((nxt, m - 1))
                    q.append((nxt, m - 1))
        steps += 1
    return None
