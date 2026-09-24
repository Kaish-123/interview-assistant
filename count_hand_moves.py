"""Piano hand reposition count.

A hand covers 5 consecutive keys: the thumb key and the four keys to its right.
Notes are numbered left to right starting at 1. The first placement is free;
count later repositionings needed to play the sequence in order.

A stretch of notes fits one hand position iff max(stretch) - min(stretch) <= 4.
That is the only constraint — the thumb does not have to sit on the current note.
"""

from __future__ import annotations

from typing import List, Optional, Sequence


HAND_SPAN = 4  # 5 keys: [L, L+4]


def countHandMoves(notes: Optional[Sequence[int]]) -> int:
    """Return the minimum number of hand moves to play `notes`.

    Time: O(n). Space: O(1).
    Does not assume sorted notes, unique notes, or that the thumb starts
    on notes[0]. Null/empty input is 0 moves.
    """
    if not notes:
        return 0

    moveCount = 0
    start = notes[0]
    end = notes[0]

    for note in notes:
        newStart = note if note < start else start
        newEnd = note if note > end else end
        if newEnd - newStart > HAND_SPAN:
            start = note
            end = note
            moveCount += 1
        else:
            start = newStart
            end = newEnd

    return moveCount


def count_hand_moves(notes: Optional[Sequence[int]]) -> int:
    return countHandMoves(notes)


def min_moves_dp(notes: Sequence[int]) -> int:
    """O(n^2) exact check: dp[i] = min moves to play notes[:i+1]."""
    n = len(notes)
    if n == 0:
        return 0

    dp: List[int] = [0] * n
    for i in range(n):
        low = notes[i]
        high = notes[i]
        best = i  # worst: move before every note after the first
        for j in range(i, -1, -1):
            if notes[j] < low:
                low = notes[j]
            if notes[j] > high:
                high = notes[j]
            if high - low > HAND_SPAN:
                break
            prev = 0 if j == 0 else dp[j - 1] + 1
            if prev < best:
                best = prev
        dp[i] = best
    return dp[-1]
