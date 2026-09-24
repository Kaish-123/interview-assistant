"""Question 1: normalize and count labels."""

from __future__ import annotations

from copy import deepcopy
from pprint import pformat
from typing import Any, Callable, Dict, List


def count_labels(labels: List[str]) -> Dict[str, int]:
    """Count normalized, non-empty labels.

    Each label is stripped of surrounding whitespace and lowercased.
    Empty results (including all-blank strings) are ignored.
    The input list is not modified.
    """
    counts: Dict[str, int] = {}
    for label in labels:
        normalized = label.strip().lower()
        if not normalized:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
    return counts


LABELS: List[str] = [
    " PASS ",
    "fail",
    "pass",
    "",
    " Fail ",
    "SKIP",
]

EXPECTED_RESULT: Dict[str, int] = {
    "pass": 2,
    "fail": 2,
    "skip": 1,
}


def differences(
    expected: Any,
    actual: Any,
    path: str = "output",
) -> List[str]:
    """Describe differences between expected and actual nested values."""
    found: List[str] = []

    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in expected:
            if key not in actual:
                found.append(f"{path}.{key}: missing; expected {expected[key]!r}")
        for key in actual:
            if key not in expected:
                found.append(f"{path}.{key}: unexpected; got {actual[key]!r}")
        for key in expected:
            if key in actual:
                found.extend(
                    differences(expected[key], actual[key], f"{path}.{key}")
                )
        return found

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
    """Run one check and always print its input, output, and result."""
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
        print(
            f"- The code raised {type(error).__name__} instead of returning a value."
        )
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
    print("What was incorrect:")
    for item in found:
        print(f"- {item}")
    raise AssertionError(f"{check_name} failed; see diagnostics above")


def run_checks() -> None:
    """Run the checks for Question 1."""
    original_labels = deepcopy(LABELS)

    check(
        lambda: count_labels(LABELS),
        EXPECTED_RESULT,
        "Main example",
        LABELS,
    )

    check(
        lambda: LABELS,
        original_labels,
        "Input mutation check",
        "LABELS after count_labels(LABELS)",
    )
    check(lambda: count_labels([]), {}, "Empty input", [])

    blank_labels = ["", " ", "\t"]
    check(
        lambda: count_labels(blank_labels),
        {},
        "Blank labels",
        blank_labels,
    )

    mixed_labels = [
        " Alpha ",
        "ALPHA",
        "beta",
        " Beta ",
        "BETA",
        "gamma",
    ]
    check(
        lambda: count_labels(mixed_labels),
        {
            "alpha": 2,
            "beta": 3,
            "gamma": 1,
        },
        "Case and surrounding whitespace",
        mixed_labels,
    )

    arbitrary_labels = ["first", "second", "first", "third", "second"]
    check(
        lambda: count_labels(arbitrary_labels),
        {"first": 2, "second": 2, "third": 1},
        "Count arbitrary labels",
        arbitrary_labels,
    )


if __name__ == "__main__":
    run_checks()
    print("All Question 1 checks passed")
