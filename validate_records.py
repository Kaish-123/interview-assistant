"""
Data Engineer Live Coding — record validation (~12 min task)
"""
from collections import Counter
from datetime import datetime


records = [
    {"user_id": "u001", "event_ts": "2024-01-15 08:32:00", "event_type": "click", "revenue": "12.50"},
    {"user_id": None, "event_ts": "2024-01-15 08:33:00", "event_type": "purchase", "revenue": "99.00"},
    {"user_id": "u003", "event_ts": "2024-01-15 08:34:00", "event_type": "click", "revenue": None},
    {"user_id": "u003", "event_ts": "2024-01-15 08:34:00", "event_type": "click", "revenue": None},  # duplicate
    {"user_id": "u004", "event_ts": "2099-01-01 00:00:00", "event_type": "purchase", "revenue": "200.00"},  # future ts
    {"user_id": "u005", "event_ts": "2024-01-15 08:36:00", "event_type": "purchase", "revenue": "-5.00"},  # negative
    {"user_id": "u006", "event_ts": "2024-01-15 08:37:00", "event_type": "purchase", "revenue": "abc"},  # bad type
    {"user_id": "u007", "event_ts": "2024-01-15 08:38:00", "event_type": "click", "revenue": "3.25"},  # clean
]

TS_FORMAT = "%Y-%m-%d %H:%M:%S"


def _dedupe_key(record):
    return (record.get("user_id"), record.get("event_ts"), record.get("event_type"))


def validate_records(records, now=None):
    """
    Validate event records and split into valid vs rejected.

    Returns:
        (valid_records, rejected_records)
        Each rejected record includes a 'rejection_reason' field (str or list[str]).
    """
    now = now or datetime.now()
    valid = []
    rejected = []

    key_counts = Counter(_dedupe_key(r) for r in records)
    seen_keys = set()

    for record in records:
        reasons = []

        if record.get("user_id") is None:
            reasons.append("null user_id")

        key = _dedupe_key(record)
        if key_counts[key] > 1:
            if key in seen_keys:
                reasons.append("duplicate")
            seen_keys.add(key)

        try:
            event_ts = datetime.strptime(record["event_ts"], TS_FORMAT)
            if event_ts > now:
                reasons.append("future timestamp")
        except (KeyError, TypeError, ValueError):
            pass  # not in spec; skip malformed timestamps

        revenue = record.get("revenue")
        try:
            if float(revenue) < 0:
                reasons.append("negative revenue")
        except (TypeError, ValueError):
            reasons.append("type mismatch on revenue")

        if reasons:
            rejected_record = {**record, "rejection_reason": reasons[0] if len(reasons) == 1 else reasons}
            rejected.append(rejected_record)
        else:
            valid.append(record)

    return valid, rejected


def print_summary(records, valid, rejected):
    """Print total counts and a breakdown by rejection type."""
    reason_counts = Counter()
    for record in rejected:
        reason = record["rejection_reason"]
        if isinstance(reason, list):
            reason_counts.update(reason)
        else:
            reason_counts[reason] += 1

    print(f"\nTotal: {len(records)} | Valid: {len(valid)} | Rejected: {len(rejected)}")
    print("\n--- REJECTION BREAKDOWN ---")
    for reason, count in sorted(reason_counts.items()):
        print(f"  {reason}: {count}")


if __name__ == "__main__":
    valid, rejected = validate_records(records)

    print_summary(records, valid, rejected)

    print("\n--- VALID RECORDS ---")
    for r in valid:
        print(r)

    print("\n--- REJECTED RECORDS ---")
    for r in rejected:
        print(r)
