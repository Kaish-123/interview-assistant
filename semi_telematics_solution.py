import pandas as pd
import numpy as np

filepath = "/home/coderpad/data/semi_da_sample.csv"

# ---- Part 2: load & inspect ----
df = pd.read_csv(filepath)
print(df.head(10))

# Normalize common column aliases after inspecting the file
colmap = {}
for c in df.columns:
    cl = c.lower().strip()
    if cl in {"timestamp", "time", "event_time", "datetime", "date_time", "ts", "recorded_at"}:
        colmap[c] = "timestamp"
    elif cl in {"truck_id", "truck", "vin", "vehicle_id", "truck_name", "vehicle", "asset_id"}:
        colmap[c] = "truck_id"
    elif cl in {"signal_name", "signal", "name", "metric", "channel"}:
        colmap[c] = "signal_name"
    elif cl in {"value", "signal_value", "val", "reading", "measurement"}:
        colmap[c] = "value"

df = df.rename(columns=colmap)
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
df["value"] = pd.to_numeric(df["value"], errors="coerce")
df = df.dropna(subset=["timestamp", "truck_id", "signal_name"])

# ---- Part 3: unique signals, trucks, duration ----
unique_signals = sorted(df["signal_name"].dropna().unique().tolist())
print("\nUnique signal_name values:")
print(unique_signals)

n_trucks = df["truck_id"].nunique()
print(f"Number of unique trucks: {n_trucks}")

duration_minutes = (df["timestamp"].max() - df["timestamp"].min()).total_seconds() / 60.0
print(f"Total duration of data sample (minutes): {duration_minutes}")

# Resolve speed / odometer-like signal names (case-insensitive substring match)
signals_lower = {s.lower(): s for s in unique_signals}


def find_signal(keywords):
    for kw in keywords:
        if kw in signals_lower:
            return signals_lower[kw]
    for s in unique_signals:
        sl = s.lower()
        for kw in keywords:
            if kw in sl:
                return s
    return None


speed_signal = find_signal(
    ["speed", "vehicle_speed", "wheel_based_vehicle_speed", "gps_speed", "velocity"]
)
odo_signal = find_signal(
    [
        "odometer",
        "odo",
        "total_vehicle_distance",
        "high_resolution_total_vehicle_distance",
        "total_distance",
        "mileage",
        "distance",
    ]
)

# ---- Part 4: longest-distance truck → avg speed while in motion ----
odo = (
    df[df["signal_name"] == odo_signal]
    .dropna(subset=["value"])
    .sort_values(["truck_id", "timestamp"])
)
# Cumulative odometer: distance = max - min per truck
distance_by_truck = odo.groupby("truck_id")["value"].agg(lambda s: s.max() - s.min())
# Edge: empty / all-NaN
distance_by_truck = distance_by_truck.replace([np.inf, -np.inf], np.nan).dropna()
if distance_by_truck.empty:
    raise ValueError(f"No usable distance data from signal '{odo_signal}'")

longest_truck = distance_by_truck.idxmax()
print(f"\nTruck with longest distance traveled: {longest_truck}")
print(f"Distance traveled: {distance_by_truck.loc[longest_truck]}")

speed = (
    df[(df["signal_name"] == speed_signal) & (df["truck_id"] == longest_truck)]
    .dropna(subset=["value"])
    .sort_values("timestamp")
)

# "In motion" => speed > 0 (excludes idle / stopped samples)
in_motion = speed.loc[speed["value"] > 0, "value"]
avg_speed_in_motion = float(in_motion.mean()) if not in_motion.empty else np.nan
print(f"Average speed when in motion: {avg_speed_in_motion}")

# ---- Part 5: largest consecutive speed jump (same truck) ----
# Jump = increase between consecutive time-ordered measurements
jumps = speed["value"].diff().dropna()
largest_jump = float(jumps.max()) if not jumps.empty else np.nan
print(f"Largest jump in speed between consecutive measurements: {largest_jump}")
