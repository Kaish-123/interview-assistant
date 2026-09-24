from datetime import datetime, timedelta

from share_call_slots.slots import (
    IST,
    evening_date_for,
    format_whatsapp,
    free_slots,
    window_for_ist_evening,
)


def test_full_window_when_calendar_is_empty():
    start, end = window_for_ist_evening(datetime(2026, 9, 12, tzinfo=IST))
    assert start.hour == 17
    assert end.hour == 5
    slots = free_slots(start, end, [])
    assert slots == [(start, end)]


def test_busy_meeting_leaves_exact_free_gaps():
    start, end = window_for_ist_evening(datetime(2026, 9, 12, tzinfo=IST))
    meeting = (
        datetime(2026, 9, 12, 19, 0, tzinfo=IST),
        datetime(2026, 9, 12, 20, 0, tzinfo=IST),
    )
    slots = free_slots(start, end, [meeting])
    assert slots[0] == (start, meeting[0])
    assert slots[1] == (meeting[1], end)


def test_example_overnight_gaps():
    start, end = window_for_ist_evening(datetime(2026, 9, 12, tzinfo=IST))
    busy = [
        (datetime(2026, 9, 13, 1, 30, tzinfo=IST), datetime(2026, 9, 13, 2, 30, tzinfo=IST)),
        (datetime(2026, 9, 13, 3, 15, tzinfo=IST), datetime(2026, 9, 13, 4, 0, tzinfo=IST)),
    ]
    slots = free_slots(start, end, busy)
    assert slots == [
        (start, datetime(2026, 9, 13, 1, 30, tzinfo=IST)),
        (datetime(2026, 9, 13, 2, 30, tzinfo=IST), datetime(2026, 9, 13, 3, 15, tzinfo=IST)),
        (datetime(2026, 9, 13, 4, 0, tzinfo=IST), end),
    ]


def test_tiny_gap_under_15_minutes_is_dropped():
    start, end = window_for_ist_evening(datetime(2026, 9, 12, tzinfo=IST))
    busy = [
        (start, start + timedelta(hours=3)),
        (start + timedelta(hours=3, minutes=10), end),
    ]
    assert free_slots(start, end, busy) == []


def test_before_5am_uses_the_night_already_in_progress():
    now = datetime(2026, 9, 12, 1, 11, tzinfo=IST)
    day = evening_date_for(now)
    start, end = window_for_ist_evening(day)
    assert start == datetime(2026, 9, 11, 17, 0, tzinfo=IST)
    assert end == datetime(2026, 9, 12, 5, 0, tzinfo=IST)


def test_whatsapp_lists_exact_free_times():
    start, end = window_for_ist_evening(datetime(2026, 9, 12, tzinfo=IST))
    slots = [
        (start, datetime(2026, 9, 13, 1, 30, tzinfo=IST)),
        (datetime(2026, 9, 13, 2, 30, tzinfo=IST), datetime(2026, 9, 13, 3, 15, tzinfo=IST)),
    ]
    text = format_whatsapp([(start, slots)], window_start=start, window_end=end)
    assert "5:00 PM – 1:30 AM IST" in text
    assert "2:30 AM – 3:15 AM IST" in text
    assert "saudagercash14@gmail.com" in text
