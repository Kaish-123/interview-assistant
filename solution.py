from typing import List
from collections import defaultdict
from datetime import datetime, timedelta
import os
import re

LOG_ROOT = "/var/logs/server"
CURRENT_DATE = datetime.strptime("15/Sep/2021:00:00:00 +0000", "%d/%b/%Y:%H:%M:%S %z")
WINDOW = timedelta(minutes=15)
TS_FMT = "%d/%b/%Y:%H:%M:%S %z"

# [timestamp] "METHOD PATH PROTOCOL" IP STATUS SIZE
LINE_RE = re.compile(
    r'^\[([^\]]+)\]\s+"(\S+)\s+\S+\s+\S+"\s+(\S+)\s+(\d{3})\s+\d+\s*$'
)


def solution(threshold: int, duration: int) -> List[str]:
    start_date = CURRENT_DATE - timedelta(days=duration)
    ip_times = defaultdict(list)

    if not os.path.isdir(LOG_ROOT):
        return []

    for root, _, files in os.walk(LOG_ROOT):
        for name in files:
            if not name.endswith(".log"):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        m = LINE_RE.match(line)
                        if not m:
                            continue
                        ts_str, method, ip, status = (
                            m.group(1),
                            m.group(2),
                            m.group(3),
                            int(m.group(4)),
                        )
                        if method != "POST" or not (200 <= status <= 299):
                            continue
                        try:
                            ts = datetime.strptime(ts_str, TS_FMT)
                        except ValueError:
                            continue
                        if start_date <= ts <= CURRENT_DATE:
                            ip_times[ip].append(ts)
            except OSError:
                continue

    suspicious = []
    for ip, times in ip_times.items():
        times.sort()
        left = 0
        for right in range(len(times)):
            while times[right] - times[left] > WINDOW:
                left += 1
            # more than `threshold` requests within a 15-minute window
            if right - left + 1 > threshold:
                suspicious.append(ip)
                break

    return sorted(suspicious)


if __name__ == "__main__":
    print(solution(5, 30))
