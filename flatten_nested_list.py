"""Flatten an arbitrarily nested list into a single-level list."""

from __future__ import annotations

from copy import deepcopy
from pprint import pformat
from typing import Any, Callable, Iterable, List


def flatten(nested: Iterable[Any]) -> List[Any]:
    """Return a new list with all nested lists expanded in order.

    Example:
        [1, [2, [3, 4]], 5] -> [1, 2, 3, 4, 5]

    Non-list values (including tuples, strings, and None) are kept as-is.
    The input is not modified.
    """
    result: List[Any] = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


IP = [1, [2, [3, 4]], 5]
OP = [1, 2, 3, 4, 5]


def differences(
    expected: Any,
    actual: Any,
    path: str = "output",
) -> List[str]:
    found: List[str] = []

    if isinstance(expected, list) and isinstance(actual, list):
        for index in range(min(len(expected), len(actual))):
            found.extend(
                differences(expected[index], actual[index], f"{path}[{index}]")
            )
        for index in range(len(actual), len(expected)):
            found.append(
                f"{path}[{index}]: missing; expected {expected[index]!r}"
            )
        for index in range(len(expected), len(actual)):
            found.append(
                f"{path}[{index}]: unexpected; got {actual[index]!r}"
            )
        return found

    if expected != actual:
        found.append(f"{path}: expected {expected!r}, got {actual!r}")
    return found


def check(
    action: Callable[[], Any],
    expected: Any,
    check_name: str,
    test_input: Any,
) -> Any:
    print(f"Check: {check_name}")
    print("Input / operation:")
    print(pformat(test_input, sort_dicts=False))
    print("Expected output:")
    print(pformat(expected, sort_dicts=False))

    try:
        actual = action()
    except Exception as error:
        print("Actual output:")
        print(f"{type(error).__name__}: {error}")
        print("Result: FAIL")
        raise AssertionError(
            f"{check_name} failed; see diagnostics above"
        ) from error

    print("Actual output:")
    print(pformat(actual, sort_dicts=False))
    found = differences(expected, actual)
    if not found:
        print("Result: PASS - actual output matches expected output.")
        return actual

    print("Result: FAIL")
    for item in found:
        print(f"- {item}")
    raise AssertionError(f"{check_name} failed; see diagnostics above")


def run_checks() -> None:
    original = deepcopy(IP)

    check(lambda: flatten(IP), OP, "Main example", IP)
    check(lambda: IP, original, "Input mutation check", "IP after flatten(IP)")
    check(lambda: flatten([]), [], "Empty input", [])
    check(lambda: flatten([1, 2, 3]), [1, 2, 3], "Already flat", [1, 2, 3])
    check(
        lambda: flatten([[[1]], [2, [3, [4]]]]),
        [1, 2, 3, 4],
        "Deeper nesting",
        [[[1]], [2, [3, [4]]]],
    )


if __name__ == "__main__":
    run_checks()
    print("All flatten checks passed")
