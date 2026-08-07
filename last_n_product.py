from functools import reduce
import operator
from typing import Iterable, Union

Number = Union[int, float]


def last_n_product(numbers: Iterable[Number], n: int) -> Number:
    """
    Return the multiplicative product of the last n numbers.

    Edge cases:
    - n <= 0: returns 1 (empty product)
    - fewer than n numbers: uses all available numbers
    - empty input: returns 1
    - zeros and negatives: handled by normal multiplication
    """
    if n <= 0:
        return 1

    nums = list(numbers)
    if not nums:
        return 1

    tail = nums[-n:]
    return reduce(operator.mul, tail, 1)


if __name__ == "__main__":
    # Example from the problem
    assert last_n_product([1, 2, 3], 3) == 6

    # Edge cases
    assert last_n_product([], 3) == 1
    assert last_n_product([5], 3) == 5
    assert last_n_product([1, 2, 3, 4], 2) == 12
    assert last_n_product([1, 0, 3], 3) == 0
    assert last_n_product([-2, 3, -4], 3) == 24
    assert last_n_product([1, 2, 3], 0) == 1
    assert last_n_product([1, 2, 3], -1) == 1

    print("All tests passed.")
