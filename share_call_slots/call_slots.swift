import AppKit
import EventKit
import Foundation

let ist = TimeZone(identifier: "Asia/Kolkata")!
let minSlot: TimeInterval = 30 * 60
let buffer: TimeInterval = 15 * 60
let windowLength: TimeInterval = 12 * 60 * 60

func parseDays() -> Int {
    var days = 3
    var idx = 1
    let args = CommandLine.arguments
    while idx < args.count {
        let arg = args[idx]
        if arg == "--days", idx + 1 < args.count, let value = Int(args[idx + 1]), value > 0 {
            days = min(value, 14)
            idx += 2
            continue
        }
        if arg.hasPrefix("--days="), let value = Int(arg.dropFirst(7)), value > 0 {
            days = min(value, 14)
        }
        idx += 1
    }
    return days
}

func startOfISTDay(_ date: Date) -> Date {
    var calendar = Calendar(identifier: .gregorian)
    calendar.timeZone = ist
    return calendar.startOfDay(for: date)
}

func window(forISTEvening day: Date) -> (Date, Date) {
    let start = startOfISTDay(day).addingTimeInterval(17 * 60 * 60)
    return (start, start.addingTimeInterval(windowLength))
}

func mergeBusy(windowStart: Date, windowEnd: Date, busy: [(Date, Date)]) -> [(Date, Date)] {
    var clamped: [(Date, Date)] = []
    for (rawStart, rawEnd) in busy {
        let start = max(rawStart, windowStart)
        let end = min(rawEnd.addingTimeInterval(buffer), windowEnd)
        if end > start {
            clamped.append((start, end))
        }
    }
    clamped.sort { $0.0 < $1.0 }
    var merged: [(Date, Date)] = []
    for span in clamped {
        if let last = merged.last, span.0 <= last.1 {
            merged.removeLast()
            merged.append((last.0, max(last.1, span.1)))
        } else {
            merged.append(span)
        }
    }
    return merged
}

func freeSlots(windowStart: Date, windowEnd: Date, busy: [(Date, Date)]) -> [(Date, Date)] {
    var cursor = windowStart
    var free: [(Date, Date)] = []
    for (start, end) in mergeBusy(windowStart: windowStart, windowEnd: windowEnd, busy: busy) {
        if start.timeIntervalSince(cursor) >= minSlot {
            free.append((cursor, start))
        }
        cursor = max(cursor, end)
    }
    if windowEnd.timeIntervalSince(cursor) >= minSlot {
        free.append((cursor, windowEnd))
    }
    return free
}

func formatIST(_ date: Date, template: String) -> String {
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.timeZone = ist
    formatter.dateFormat = template
    return formatter.string(from: date)
}

func buildMessage(days: [(Date, [(Date, Date)])]) -> String {
    var lines = [
        "Available for calls",
        "Calendar: saudagercash14@gmail.com",
        "Window: 5:00 PM – 5:00 AM IST",
        "(6:30 AM – 6:30 PM US Central)",
        "",
        "Pick a slot and reply here.",
        "",
    ]
    var any = false
    for (day, slots) in days {
        guard !slots.isEmpty else { continue }
        any = true
        lines.append("*\(formatIST(day, template: "EEE, d MMM"))*")
        for (start, end) in slots {
            lines.append(
                "• \(formatIST(start, template: "h:mm a")) – \(formatIST(end, template: "h:mm a")) IST"
            )
        }
        lines.append("")
    }
    if !any {
        lines.append("No free slots in this window.")
    }
    return lines.joined(separator: "\n").trimmingCharacters(in: .whitespacesAndNewlines) + "\n"
}

func requestAccess(_ store: EKEventStore) -> Bool {
    let semaphore = DispatchSemaphore(value: 0)
    var granted = false
    if #available(macOS 14.0, *) {
        store.requestFullAccessToEvents { ok, _ in
            granted = ok
            semaphore.signal()
        }
    } else {
        store.requestAccess(to: .event) { ok, _ in
            granted = ok
            semaphore.signal()
        }
    }
    _ = semaphore.wait(timeout: .now() + 30)
    return granted
}

func loadBusy(store: EKEventStore, start: Date, end: Date) -> [(Date, Date)] {
    let calendars = store.calendars(for: .event)
    let predicate = store.predicateForEvents(withStart: start, end: end, calendars: calendars)
    return store.events(matching: predicate).compactMap { event in
        if event.status == .canceled { return nil }
        if event.availability == .free { return nil }
        return (event.startDate, event.endDate)
    }
}

let dayCount = parseDays()
let store = EKEventStore()
guard requestAccess(store) else {
    fputs("Calendar access was denied. Enable Calendar for Terminal/Shortcuts in System Settings → Privacy & Security → Calendars.\n", stderr)
    exit(1)
}

var calendar = Calendar(identifier: .gregorian)
calendar.timeZone = ist
let today = startOfISTDay(Date())
let rangeStart = today.addingTimeInterval(-12 * 60 * 60)
let rangeEnd = today.addingTimeInterval(TimeInterval((dayCount + 2) * 24 * 60 * 60))
let busy = loadBusy(store: store, start: rangeStart, end: rangeEnd)

var perDay: [(Date, [(Date, Date)])] = []
for offset in 0..<dayCount {
    guard let day = calendar.date(byAdding: .day, value: offset, to: today) else { continue }
    let (windowStart, windowEnd) = window(forISTEvening: day)
    perDay.append((day, freeSlots(windowStart: windowStart, windowEnd: windowEnd, busy: busy)))
}

let message = buildMessage(days: perDay)
print(message, terminator: "")
NSPasteboard.general.clearContents()
NSPasteboard.general.setString(message, forType: .string)

if CommandLine.arguments.contains("--whatsapp") {
    var allowed = CharacterSet.urlQueryAllowed
    allowed.remove(charactersIn: ":/?#[]@!$&'()*+,;=")
    let encoded = message.addingPercentEncoding(withAllowedCharacters: allowed) ?? ""
    if let url = URL(string: "whatsapp://send?text=\(encoded)") {
        NSWorkspace.shared.open(url)
    }
}
