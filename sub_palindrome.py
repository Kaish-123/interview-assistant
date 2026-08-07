def palindrome(s):
    """Return the count of distinct palindromic substrings in s."""
    n = len(s)
    if n == 0:
        return 0

    # Eertree (palindromic tree): O(n) distinct palindrome counting.
    nodes = [{'next': {}, 'len': -1, 'link': 0}, {'next': {}, 'len': 0, 'link': 0}]
    last = 1
    count = 0

    for i, ch in enumerate(s):
        cur = last
        while True:
            curlen = nodes[cur]['len']
            if i - 1 - curlen >= 0 and s[i - 1 - curlen] == ch:
                break
            cur = nodes[cur]['link']

        if ch in nodes[cur]['next']:
            last = nodes[cur]['next'][ch]
            continue

        new_len = nodes[cur]['len'] + 2
        new_id = len(nodes)
        nodes.append({'next': {}, 'len': new_len, 'link': 0})
        nodes[cur]['next'][ch] = new_id

        if new_len == 1:
            nodes[new_id]['link'] = 1
        else:
            link = nodes[cur]['link']
            while True:
                linklen = nodes[link]['len']
                if i - 1 - linklen >= 0 and s[i - 1 - linklen] == ch:
                    break
                link = nodes[link]['link']
            nodes[new_id]['link'] = nodes[link]['next'][ch]

        last = new_id
        count += 1

    return count


if __name__ == '__main__':
    import os
    import time

    if 'OUTPUT_PATH' in os.environ:
        fptr = open(os.environ['OUTPUT_PATH'], 'w')
        s = input().strip()
        result = palindrome(s)
        fptr.write(str(result) + '\n')
        fptr.close()
    else:
        tests = [
            ("aabaa", 5),
            ("mokkori", 7),
            ("abcddcbabcdcdcaadcdcbabcdddcb", 18),
            ("a", 1),
            ("aa", 2),
            ("aaaa", 4),
            ("abcde", 5),
            ("abba", 4),
        ]
        for s, expected in tests:
            got = palindrome(s)
            status = "OK" if got == expected else "FAIL"
            print(f"{status}: {s!r} -> {got} (expected {expected})")

        s = "a" * 5000
        start = time.time()
        got = palindrome(s)
        elapsed = time.time() - start
        print(f"perf n=5000: {got} in {elapsed:.2f}s")
