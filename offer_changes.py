from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _parse_timestamp(ts: Any) -> datetime | None:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        # Accept common ISO8601 'Z' suffix.
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts[:-1]).replace(tzinfo=timezone.utc)
        dt = datetime.fromisoformat(ts)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _normalize_offers(raw: Any) -> set[str]:
    if raw is None:
        return set()
    if isinstance(raw, list):
        return {str(x) for x in raw if x is not None and str(x) != ""}
    if isinstance(raw, str):
        s = raw.strip()
        if s == "" or s.lower() == "null":
            return set()
        return {s}
    return set()


@dataclass(frozen=True)
class ChangeEvent:
    user_id: str
    timestamp: str
    offer_id: str
    change: str  # "added" | "removed"


def compute_offer_change_events(events: Iterable[dict[str, Any]]) -> dict[str, list[ChangeEvent]]:
    """
    Returns per-user offer change events derived from snapshot records.

    Each change event indicates a single offer was either added or removed
    compared to the previous snapshot for that same user.
    """

    per_user: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for idx, e in enumerate(events):
        if not isinstance(e, dict):
            continue
        user_id = e.get("user_id")
        if not isinstance(user_id, str) or not user_id:
            continue
        per_user.setdefault(user_id, []).append((idx, e))

    out: dict[str, list[ChangeEvent]] = {}

    for user_id, indexed in per_user.items():
        # Sort by timestamp when valid; otherwise keep stable input order at the end.
        def key(item: tuple[int, dict[str, Any]]):
            idx, e = item
            dt = _parse_timestamp(e.get("timestamp"))
            return (dt is None, dt or datetime.max.replace(tzinfo=timezone.utc), idx)

        indexed_sorted = sorted(indexed, key=key)

        prev_offers: set[str] = set()
        user_changes: list[ChangeEvent] = []

        for _, e in indexed_sorted:
            ts = e.get("timestamp")
            ts_str = ts if isinstance(ts, str) else ""
            offers = _normalize_offers(e.get("eligible_offers"))

            added = sorted(offers - prev_offers)
            removed = sorted(prev_offers - offers)

            for offer_id in added:
                user_changes.append(
                    ChangeEvent(user_id=user_id, timestamp=ts_str, offer_id=offer_id, change="added")
                )
            for offer_id in removed:
                user_changes.append(
                    ChangeEvent(user_id=user_id, timestamp=ts_str, offer_id=offer_id, change="removed")
                )

            prev_offers = offers

        out[user_id] = user_changes

    return out


def main() -> None:
    path = Path(__file__).with_name("test_data.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Expected top-level JSON array.")

    changes = compute_offer_change_events(data)
    print(json.dumps({k: [ce.__dict__ for ce in v] for k, v in changes.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

