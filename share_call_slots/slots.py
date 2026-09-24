"""Free-slot math for the 5:00 PM IST – 5:00 AM IST call window."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
WINDOW_HOURS = 12
WINDOW_START = timedelta(hours=17)  # 5:00 PM IST
MIN_SLOT = timedelta(minutes=15)
BUFFER = timedelta(0)
CALL_CALENDAR = "saudagercash14@gmail.com"


def evening_date_for(now: datetime) -> datetime:
    """Date of the 5:00 PM IST start for the active or next call night."""
    local = now.astimezone(IST) if now.tzinfo else now.replace(tzinfo=IST)
    if local.hour < 5:
        local = local - timedelta(days=1)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def window_for_ist_evening(day: datetime) -> tuple[datetime, datetime]:
    """Return the 5:00 PM IST → 5:00 AM IST window starting on ``day`` (IST date)."""
    local = day.astimezone(IST) if day.tzinfo else day.replace(tzinfo=IST)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0) + WINDOW_START
    return start, start + timedelta(hours=WINDOW_HOURS)


def merge_busy(
    window_start: datetime,
    window_end: datetime,
    busy: list[tuple[datetime, datetime]],
    *,
    buffer: timedelta = BUFFER,
) -> list[tuple[datetime, datetime]]:
    clamped: list[tuple[datetime, datetime]] = []
    for start, end in busy:
        start = max(start, window_start)
        end = min(end + buffer, window_end)
        if end > start:
            clamped.append((start, end))
    clamped.sort()
    merged: list[list[datetime]] = []
    for start, end in clamped:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def free_slots(
    window_start: datetime,
    window_end: datetime,
    busy: list[tuple[datetime, datetime]],
    *,
    min_slot: timedelta = MIN_SLOT,
    buffer: timedelta = BUFFER,
) -> list[tuple[datetime, datetime]]:
    cursor = window_start
    free: list[tuple[datetime, datetime]] = []
    for start, end in merge_busy(window_start, window_end, busy, buffer=buffer):
        if start - cursor >= min_slot:
            free.append((cursor, start))
        cursor = max(cursor, end)
    if window_end - cursor >= min_slot:
        free.append((cursor, window_end))
    return free


def format_whatsapp(
    days: list[tuple[datetime, list[tuple[datetime, datetime]]]],
    *,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
) -> str:
    if window_start is None and days:
        first_slots = days[0][1]
        if first_slots:
            window_start = first_slots[0][0]
        else:
            window_start, window_end = window_for_ist_evening(days[0][0])
    if window_end is None and window_start is not None:
        window_end = window_start + timedelta(hours=WINDOW_HOURS)

    lines = [
        "Available for calls",
        f"Calendar: {CALL_CALENDAR}",
    ]
    if window_start is not None and window_end is not None:
        lines.append(
            f"Window: {window_start.strftime('%-d %b %-I:%M %p')} – "
            f"{window_end.strftime('%-d %b %-I:%M %p')} IST"
        )
    else:
        lines.append("Window: 5:00 PM – 5:00 AM IST")
    lines.extend(["", "Pick a slot and reply here.", ""])

    any_slots = False
    for _day, slots in days:
        if not slots:
            continue
        any_slots = True
        for start, end in slots:
            lines.append(
                f"• {start.strftime('%-I:%M %p')} – {end.strftime('%-I:%M %p')} IST"
            )
    if not any_slots:
        lines.append("No free slots in this window.")
    return "\n".join(lines).strip() + "\n"
