# Problem Name is &&& First NonRepeating &&& PLEASE DO NOT REMOVE THIS LINE.

"""
Instructions to candidate.
 1) Run this code in the REPL to observe its behaviour. The
    execution entry point is main().
 2) Consider adding some additional tests in doTestsPass().
 3) Implement findFirst(input_str) correctly.
 4) If time permits, some possible follow-ups.
"""

from collections import Counter

"""
Finds the first character that does not repeat anywhere in the input string
If all characters are repeated, return 0
Given "apple", the answer is "a"
Given "racecars", the answer is "e"
Given "ababdc", the answer is "d"
"""
def findFirst(input_str):
    if not input_str:
        return 0

    counts = Counter(input_str)
    for ch in input_str:
        if counts[ch] == 1:
            return ch
    return 0


"""
Returns True if all tests pass. Otherwise returns False
"""
def doTestsPass():
    doPass = True
    tests = {
        # provided cases
        "racecars": "e",
        "apple": "a",
        "ababdc": "d",
        # edge cases
        "": 0,                    # empty string
        "a": "a",                 # single character
        "aa": 0,                  # all characters repeat
        "aabbcc": 0,              # all characters repeat
        "aabbccd": "d",           # unique char at the end
        "xxyyz": "z",             # unique char at the end
        "Abc": "A",               # case-sensitive: A != a
        "aAbBc": "a",             # first unique among mixed case
        "1122334": "4",           # digits
        "!!@@#": "#",             # special characters
        "a b a": "b",             # spaces repeat; b is unique
        " a ": "a",               # unique char between spaces
        "swiss": "w",             # classic example
    }
    for input_str, expected in tests.items():
        result = findFirst(input_str)
        if result != expected:
            print(
                "Test Failed: {0!r} expected: {1!r} actual: {2!r}".format(
                    input_str, expected, result
                )
            )
            doPass = False

    return doPass


if __name__ == "__main__":
    result = doTestsPass()

    if result:
        print("All tests pass\n")
    else:
        print("Tests fail\n")
