import re
from typing import Iterable, Optional

import pandas as pd


def parse_price(series: pd.Series) -> pd.Series:
    """
    Convert Airbnb-style price strings like "$1,500.00" into floats.
    """
    # Remove currency symbol and thousands separators.
    cleaned = series.astype(str).str.replace(r"[\$,]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def parse_t_f_bool(series: pd.Series) -> pd.Series:
    """
    Convert 't'/'f' (as strings) to 1/0. Leaves numeric/bool values untouched.
    """
    if pd.api.types.is_bool_dtype(series):
        return series.astype(int)

    # Handle object dtype like 't'/'f'
    s = series
    if not pd.api.types.is_numeric_dtype(s):
        s = s.astype(str).str.strip().str.lower()
        mapping = {"t": 1, "f": 0, "true": 1, "false": 0}
        s = s.map(mapping)
        return pd.to_numeric(s, errors="coerce")

    return s.astype(int)


def host_since_to_year(series: pd.Series) -> pd.Series:
    """
    Convert host_since values into a numeric year for correlation.
    """
    dt = pd.to_datetime(series, errors="coerce")
    return dt.dt.year.astype(float)


def choose_second_largest_by_abs(
    items: Iterable[str],
    values_by_key: dict,
    *,
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Pick the item whose abs(corr) is the second largest.
    Ties are resolved by the iteration order in `items`.
    """
    scored = []
    for k in items:
        v = values_by_key.get(k)
        if v is None:
            continue
        if pd.isna(v):
            continue
        scored.append((abs(float(v)), k))

    if len(scored) < 2:
        return default

    # Stable sort: iterate order is preserved for ties because python sort is stable.
    scored_sorted = sorted(scored, key=lambda t: t[0], reverse=True)
    return scored_sorted[1][1]

