import ast
import json
import os
from collections import defaultdict


def _parse_record(raw):
    """Return a dict record from a JSON/literal line, or None."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    line = raw.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(line)
        except (ValueError, SyntaxError):
            return None


def clean_and_summarize(transactions):
    """
    Parse transaction lines or dict rows, drop invalid rows, sum USD per client.
    Invalid: amount is None, amount not numeric, currency != \"USD\".
    Each item may be a dict or a JSON/Python literal line with keys:
    id, client, amount (nullable / must parse as number), currency.
    """
    totals = defaultdict(float)

    for raw in transactions:
        rec = _parse_record(raw)
        if rec is None:
            continue

        if not isinstance(rec, dict):
            continue
        if rec.get("currency") != "USD":
            continue

        amt = rec.get("amount")
        if amt is None:
            continue
        try:
            value = float(amt)
        except (TypeError, ValueError):
            continue

        client = rec.get("client")
        if client is None:
            continue

        totals[client] += value

    # One line per client, alphabetical by client name (common for this task type).
    return [f"{name} {totals[name]:.2f}" for name in sorted(totals)]


if __name__ == "__main__":
    fptr = open(os.environ["OUTPUT_PATH"], "w")

    transactions_count = int(input().strip())

    transactions = []

    for _ in range(transactions_count):
        transactions_item = input()
        transactions.append(transactions_item)

    result = clean_and_summarize(transactions)

    fptr.write("\n".join(result))
    fptr.write("\n")

    fptr.close()
