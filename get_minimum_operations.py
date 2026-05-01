def findMinimumLengthSubarray(arr, k):
    """
    Return the minimum length of a subarray containing at least k distinct
    integers. If no such subarray exists, return -1.
    """
    n = len(arr)

    if n == 0 or k <= 0:
        return -1

    freq = {}
    distinct = 0
    left = 0
    best = n + 1

    for right, value in enumerate(arr):
        prev_count = freq.get(value, 0)
        freq[value] = prev_count + 1
        if prev_count == 0:
            distinct += 1

        # Shrink while still valid to get minimum window for this right bound.
        while distinct >= k:
            best = min(best, right - left + 1)
            left_value = arr[left]
            freq[left_value] -= 1
            if freq[left_value] == 0:
                distinct -= 1
                del freq[left_value]
            left += 1

    return best if best <= n else -1
