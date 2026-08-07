from typing import List


class WordList:
    """Provided interface — may read from a file/DB in production."""

    def get_word_list(self) -> List[str]:
        return ["banana", "abdbdb", "cat", "mom", "tot"]


def are_substitution_ciphers(s1: str, s2: str) -> bool:
    if len(s1) != len(s2):
        return False

    map_s1_to_s2 = {}
    map_s2_to_s1 = {}

    for char1, char2 in zip(s1, s2):
        if char1 in map_s1_to_s2 and map_s1_to_s2[char1] != char2:
            return False
        if char2 in map_s2_to_s1 and map_s2_to_s1[char2] != char1:
            return False
        map_s1_to_s2[char1] = char2
        map_s2_to_s1[char2] = char1

    return True


def _cipher_pattern(word: str) -> tuple:
    """Canonical pattern shared by all substitution-cipher equivalents.

    Example: banana / cololo / abdbdb → (0, 1, 2, 1, 2, 1)
    """
    first_seen = {}
    pattern = []
    next_id = 0
    for ch in word:
        if ch not in first_seen:
            first_seen[ch] = next_id
            next_id += 1
        pattern.append(first_seen[ch])
    return tuple(pattern)


class CipherPuzzleHelper:
    """Returns dictionary words that are substitution ciphers of a user word."""

    def __init__(self, word_list: WordList):
        self._by_pattern = {}
        for word in word_list.get_word_list():
            pattern = _cipher_pattern(word)
            self._by_pattern.setdefault(pattern, []).append(word)

    def get_cipher_list(self, word: str) -> List[str]:
        return list(self._by_pattern.get(_cipher_pattern(word), []))


if __name__ == "__main__":
    helper = CipherPuzzleHelper(WordList())

    assert helper.get_cipher_list("cololo") == ["banana", "abdbdb"]
    assert helper.get_cipher_list("pop") == ["mom", "tot"]
    assert helper.get_cipher_list("dog") == ["cat"]
    print("All tests passed.")
