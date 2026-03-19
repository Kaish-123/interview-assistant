#!/usr/bin/env python3
"""
Read All Letters - Minimum operations to read all unread letters.
1 = unread, 0 = read.
Operations: open letter (from list), move to next/prev letter, return to list.
"""
import os


def solve(ar):
    """
    Count minimum operations by simulating left-to-right:
    - At list, see unread -> +1 (open letter), then we're viewing that letter.
    - Viewing letter, see next unread -> +1 (move to next letter).
    - Viewing letter, see 0 -> +1 (return to list), then we're at list.
    """
    n = len(ar)
    operations = 0
    at_letter = False  # True if we're currently viewing a letter (after opening one)

    for i in range(n):
        if ar[i] == 1:
            if at_letter:
                operations += 1   # move to next letter
            else:
                operations += 1   # open letter from list
            at_letter = True
        else:
            if at_letter:
                operations += 1   # return to list
            at_letter = False

    return operations


if __name__ == '__main__':
    fptr = open(os.environ.get('OUTPUT_FILE_PATH', '/dev/stdout'), 'w')

    ar_count = int(input().strip())
    ar = list(map(int, input().rstrip().split()))

    outcome = solve(ar)
    fptr.write(str(outcome) + '\n')
    fptr.close()
