#!/usr/bin/env python3
"""Read Apple Calendar, print IST call slots, copy them, optionally open WhatsApp."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from slots import IST, evening_date_for, format_whatsapp, free_slots, window_for_ist_evening

JXA = r"""
ObjC.import("EventKit")
ObjC.import("Foundation")

function iso(date) {
  const fmt = $.NSISO8601DateFormatter.alloc.init
  fmt.formatOptions = $.NSISO8601DateFormatWithInternetDateTime + $.NSISO8601DateFormatWithFractionalSeconds
  return ObjC.unwrap(fmt.stringFromDate(date))
}

function run(argv) {
  const startISO = argv[0]
  const endISO = argv[1]
  const store = $.EKEventStore.alloc.init
  const allCalendars = store.calendarsForEntityType($.EKEntityTypeEvent)
  const wanted = "saudagercash14@gmail.com"
  const calendars = $.NSMutableArray.alloc.init
  for (let i = 0; i < allCalendars.count; i++) {
    const cal = allCalendars.objectAtIndex(i)
    const title = ObjC.unwrap(cal.title) || ""
    if (title === wanted || title.indexOf(wanted) >= 0) {
      calendars.addObject(cal)
    }
  }
  if (calendars.count === 0) {
    throw new Error("Calendar saudagercash14@gmail.com was not found")
  }
  const fmt = $.NSISO8601DateFormatter.alloc.init
  fmt.formatOptions = $.NSISO8601DateFormatWithInternetDateTime
  const start = fmt.dateFromString(startISO)
  const end = fmt.dateFromString(endISO)
  if (start === null || end === null) {
    throw new Error("Could not parse date range")
  }
  const predicate = store.predicateForEventsWithStartDateEndDateCalendars(start, end, calendars)
  const events = store.eventsMatchingPredicate(predicate)
  const lines = []
  for (let i = 0; i < events.count; i++) {
    const event = events.objectAtIndex(i)
    if (event.status === 2) continue
    if (event.availability === 1) continue
    lines.push(iso(event.startDate) + "\t" + iso(event.endDate))
  }
  return lines.join("\n")
}
"""


def parse_iso(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text).astimezone(IST)


def load_busy(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    auth = subprocess.run(
        [
            "osascript",
            "-l",
            "JavaScript",
            "-e",
            """
ObjC.import("EventKit")
const store = $.EKEventStore.alloc.init
const status = $.EKEventStore.authorizationStatusForEntityType($.EKEntityTypeEvent)
const calendars = store.calendarsForEntityType($.EKEntityTypeEvent)
JSON.stringify({status: Number(status), calendars: Number(calendars.count)})
""",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        info = json.loads(auth.stdout.strip().splitlines()[-1])
    except Exception:
        info = {"status": -1, "calendars": 0}
    if int(info.get("calendars") or 0) <= 0:
        raise RuntimeError(
            "This Python helper cannot read Apple Calendar from Cursor/Terminal yet "
            "(no EventKit permission).\n\n"
            "Use the installed Shortcut instead:\n"
            "  Mac: open Shortcuts and run “Share Call Slots”\n"
            "  iPhone: wait for iCloud sync, or AirDrop\n"
            f"    {Path(__file__).resolve().parent / 'out' / 'Share Call Slots.shortcut'}"
        )
    result = subprocess.run(
        [
            "osascript",
            "-l",
            "JavaScript",
            "-e",
            JXA,
            "--",
            start.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ"),
            end.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout).strip()
        raise RuntimeError(
            "Could not read Apple Calendar. Allow Calendar access for Terminal "
            f"in System Settings → Privacy & Security → Calendars.\n{err}"
        )
    busy: list[tuple[datetime, datetime]] = []
    for line in result.stdout.splitlines():
        if "\t" not in line:
            continue
        raw_start, raw_end = line.split("\t", 1)
        busy.append((parse_iso(raw_start), parse_iso(raw_end)))
    return busy


def build_message(days: int = 1) -> str:
    now = datetime.now(IST)
    day = evening_date_for(now)
    window_start, window_end = window_for_ist_evening(day)
    busy = load_busy(window_start - timedelta(hours=12), window_end + timedelta(hours=12))
    slots = free_slots(window_start, window_end, busy)
    return format_whatsapp([(day, slots)], window_start=window_start, window_end=window_end)


def copy_to_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)


def open_whatsapp(text: str) -> None:
    encoded = urllib.parse.quote(text, safe="")
    subprocess.run(["open", f"whatsapp://send?text={encoded}"], check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Share free call slots from Apple Calendar")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--whatsapp", action="store_true")
    args = parser.parse_args()
    try:
        message = build_message(max(1, min(args.days, 14)))
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    sys.stdout.write(message)
    copy_to_clipboard(message)
    if args.whatsapp:
        open_whatsapp(message)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
