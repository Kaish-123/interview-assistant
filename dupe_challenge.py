import os
from collections import Counter


def dupe_challenge(env_vars):
    """
    Parse semicolon-separated env var names, count them, list duplicates,
    and return a deduplicated list (first occurrence wins).

    Newlines inside the input (e.g. wrapped display) are normalized to spaces
    within each token before splitting on ';'.
    """
    raw = env_vars.replace("\r", "")
    parts = []
    for chunk in raw.split(";"):
        token = " ".join(chunk.split())
        if token:
            parts.append(token)

    total = len(parts)
    counts = Counter(parts)
    duplicates = sorted(name for name, n in counts.items() if n > 1)

    seen = set()
    unique_ordered = []
    for name in parts:
        if name not in seen:
            seen.add(name)
            unique_ordered.append(name)

    # Three-line answer: total count; duplicate names; deduped list
    return (
        str(total)
        + "\n"
        + ";".join(duplicates)
        + "\n"
        + ";".join(unique_ordered)
    )


if __name__ == "__main__":
    fptr = open(os.environ["OUTPUT_PATH"], "w")
    env_vars = input()
    result = dupe_challenge(env_vars)
    fptr.write(result)
    if not result.endswith("\n"):
        fptr.write("\n")
    fptr.close()
