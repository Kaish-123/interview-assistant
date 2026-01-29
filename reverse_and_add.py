import sys


def reverse_number(value: int) -> int:
    return int(str(value)[::-1])


def is_palindrome(value: int) -> bool:
    text = str(value)
    return text == text[::-1]


def main() -> None:
    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        current = int(stripped)
        iterations = 0
        while not is_palindrome(current):
            current += reverse_number(current)
            iterations += 1
        print(f"{iterations} {current}")


if __name__ == "__main__":
    main()
