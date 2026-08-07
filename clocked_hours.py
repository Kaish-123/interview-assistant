from datetime import datetime
from collections import defaultdict


def parse_time(t: str) -> datetime:
    return datetime.strptime(t.strip(), "%H:%M")


def total_clocked_hours(records: list[tuple[int, str, str]]) -> dict[int, float]:
    """
    records: list of (emp_id, time_str, flag) where flag is 'I' or 'O'
    Returns total clocked hours per employee.
    """
    pending_in = {}
    totals = defaultdict(float)

    for emp_id, time_str, flag in records:
        if flag == "I":
            pending_in[emp_id] = parse_time(time_str)
        elif flag == "O":
            punch_in = pending_in.pop(emp_id)
            punch_out = parse_time(time_str)
            totals[emp_id] += (punch_out - punch_in).total_seconds() / 3600

    return dict(totals)


if __name__ == "__main__":
    data = [
        (114, "8:30", "I"),
        (114, "10:30", "O"),
        (114, "11:30", "I"),
        (114, "15:30", "O"),
        (115, "9:30", "I"),
        (115, "17:30", "O"),
    ]

    for emp_id, hours in sorted(total_clocked_hours(data).items()):
        print(f"Employee {emp_id}: {hours:g} hours")
