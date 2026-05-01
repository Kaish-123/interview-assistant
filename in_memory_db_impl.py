from in_memory_db import InMemoryDB

# (value, valid_from, expire_at_exclusive)
# valid_from None => no lower bound (classic set)
# expire_at None => no upper bound
FieldEntry = tuple[str, int | None, int | None]


# Snapshot field: ('p', value, start) permanent; ('t', value, remaining_ttl) TTL at backup time
SnapshotField = tuple[str, str, int | None] | tuple[str, str, int]


class InMemoryDBImpl(InMemoryDB):
    def __init__(self) -> None:
        self.store: dict[str, dict[str, FieldEntry]] = {}
        self._backups: list[tuple[int, dict[str, dict[str, SnapshotField]]]] = []

    @staticmethod
    def _valid_at(entry: FieldEntry, t: int) -> bool:
        _, start, end = entry
        if start is not None and t < start:
            return False
        if end is not None and t >= end:
            return False
        return True

    def set(self, key: str, field: str, value: str) -> None:
        if key not in self.store:
            self.store[key] = {}
        self.store[key][field] = (value, None, None)

    def get(self, key: str, field: str) -> str | None:
        if key not in self.store or field not in self.store[key]:
            return None
        return self.store[key][field][0]

    def delete(self, key: str, field: str) -> bool:
        if key not in self.store or field not in self.store[key]:
            return False
        del self.store[key][field]
        if not self.store[key]:
            del self.store[key]
        return True

    def scan(self, key: str) -> list[str]:
        if key not in self.store:
            return []
        record = self.store[key]
        return [f"{f}({record[f][0]})" for f in sorted(record)]

    def scan_by_prefix(self, key: str, prefix: str) -> list[str]:
        if key not in self.store:
            return []
        record = self.store[key]
        return [
            f"{f}({record[f][0]})"
            for f in sorted(f for f in record if f.startswith(prefix))
        ]

    def set_at(self, key: str, field: str, value: str, timestamp: int) -> None:
        if key not in self.store:
            self.store[key] = {}
        self.store[key][field] = (value, timestamp, None)

    def set_at_with_ttl(
        self, key: str, field: str, value: str, timestamp: int, ttl: int
    ) -> None:
        if key not in self.store:
            self.store[key] = {}
        self.store[key][field] = (value, timestamp, timestamp + ttl)

    def delete_at(self, key: str, field: str, timestamp: int) -> bool:
        if key not in self.store or field not in self.store[key]:
            return False
        entry = self.store[key][field]
        if not self._valid_at(entry, timestamp):
            return False
        del self.store[key][field]
        if not self.store[key]:
            del self.store[key]
        return True

    def get_at(self, key: str, field: str, timestamp: int) -> str | None:
        if key not in self.store or field not in self.store[key]:
            return None
        entry = self.store[key][field]
        if not self._valid_at(entry, timestamp):
            return None
        return entry[0]

    def scan_at(self, key: str, timestamp: int) -> list[str]:
        if key not in self.store:
            return []
        record = self.store[key]
        return [
            f"{f}({record[f][0]})"
            for f in sorted(record)
            if self._valid_at(record[f], timestamp)
        ]

    def scan_by_prefix_at(
        self, key: str, prefix: str, timestamp: int
    ) -> list[str]:
        if key not in self.store:
            return []
        record = self.store[key]
        return [
            f"{f}({record[f][0]})"
            for f in sorted(f for f in record if f.startswith(prefix))
            if self._valid_at(record[f], timestamp)
        ]

    def backup(self, timestamp: int) -> int:
        snapshot: dict[str, dict[str, SnapshotField]] = {}
        count = 0
        for key, record in self.store.items():
            snap_record: dict[str, SnapshotField] = {}
            for field, entry in record.items():
                if not self._valid_at(entry, timestamp):
                    continue
                val, start, end = entry
                if end is None:
                    snap_record[field] = ("p", val, start)
                else:
                    remaining = end - timestamp
                    snap_record[field] = ("t", val, remaining)
            if snap_record:
                snapshot[key] = snap_record
                count += 1
        self._backups.append((timestamp, snapshot))
        return count

    def restore(self, timestamp: int, timestamp_to_restore: int) -> None:
        best_snap: dict[str, dict[str, SnapshotField]] | None = None
        best_ts = -1
        for b_ts, snap in self._backups:
            if b_ts <= timestamp_to_restore and b_ts >= best_ts:
                best_ts = b_ts
                best_snap = snap
        self.store = {}
        if not best_snap:
            return
        for key, rec in best_snap.items():
            self.store[key] = {}
            for field, data in rec.items():
                kind = data[0]
                if kind == "p":
                    _, val, start = data
                    self.store[key][field] = (val, start, None)
                else:
                    _, val, remaining = data
                    self.store[key][field] = (val, timestamp, timestamp + remaining)
