from bisect import bisect_left


def findTotalEfficiency(arr, pairs):
    n = len(arr)
    if n == 0:
        return 0

    # Difference array: how many pairs cover each index
    diff = [0] * (n + 1)
    for start, end in pairs:
        diff[start] += 1
        diff[end + 1] -= 1

    freq = [0] * n
    cur = 0
    for i in range(n):
        cur += diff[i]
        freq[i] = cur

    # efficient = arr[i] repeated freq[i] times (never materialize fully)
    covered = [(arr[i], freq[i]) for i in range(n) if freq[i] > 0]
    if not covered:
        return 0

    covered.sort()
    values = []
    prefix = []
    running = 0
    for val, f in covered:
        running += f
        values.append(val)
        prefix.append(running)

    total_efficiency = 0
    for i, value in enumerate(arr):
        if freq[i] > 0:
            continue
        # count of elements in efficient strictly < value
        idx = bisect_left(values, value)
        if idx > 0:
            total_efficiency += prefix[idx - 1]

    return total_efficiency
