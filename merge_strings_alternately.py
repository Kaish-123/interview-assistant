def merge_strings_alternately(strings):
    """Merge K strings by taking one character from each in round-robin order."""
    result = []
    max_len = max(len(s) for s in strings)

    for i in range(max_len):
        for s in strings:
            if i < len(s):
                result.append(s[i])

    return "".join(result)


if __name__ == "__main__":
    # Example 1
    s1 = ["abc", "edf", "zyx"]
    print(merge_strings_alternately(s1))  # aezbdycfx

    # Example 2 (varying lengths)
    s2 = ["abc", "def", "ysz", "sa"]
    print(merge_strings_alternately(s2))  # adysbesacfz
