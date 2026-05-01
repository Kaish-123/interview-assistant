"""
Filter employees with tenure >= 15 years and salary >= $50,000.
Designed for large datasets (e.g. 500k+ rows): vectorized ops, categorical keys, chunked reads for CSV.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

# Reference date for tenure (use date.today() in production)
AS_OF: date = date(2026, 4, 9)


def _parse_salary(s: pd.Series) -> pd.Series:
    """Strip commas/currency and coerce to nullable Int64."""
    cleaned = (
        s.astype(str)
        .str.replace(r"[\$,]", "", regex=True)
        .str.replace(r"\s+", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce").astype("Int64")


def _parse_age_years(s: pd.Series) -> pd.Series:
    """Extract first integer from strings like '34' or '34 years'."""
    extracted = s.astype(str).str.extract(r"(\d+)", expand=False)
    return pd.to_numeric(extracted, errors="coerce")


def _parse_start_date(s: pd.Series) -> pd.Series:
    """
    Parse start dates: try Excel serial (common in exports), else ISO/datetime strings.
    """
    num = pd.to_numeric(s, errors="coerce")
    mask_serial = num.notna() & (num > 20000) & (num < 80000)
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    if mask_serial.any():
        # Excel 1900 date system: origin 1899-12-30
        out.loc[mask_serial] = pd.to_datetime(
            num.loc[mask_serial], unit="D", origin="1899-12-30", errors="coerce"
        )
    rest = ~mask_serial & s.notna()
    if rest.any():
        out.loc[rest] = pd.to_datetime(s.loc[rest], errors="coerce", utc=False)
    return out.dt.normalize()


def build_sample_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    emp_data = pd.DataFrame(
        {
            "employee_id": [123, 123, 234, 456, 890, 567],
            "employee_first_name": ["chris", "chris", "todd", "jordan", "matt", "timothy"],
            "age": ["35", "35", "45", "23", "56", "34 years"],
            "salary": ["30,000", "35,000", "50,000", "25,000", "100,000", "32,000"],
            "start_date": [45658, 45931, 41275, 41366, 36161, 45353],
            "department": ["strategy"] * 2 + ["finance", "strategy", "operations", "strategy"],
            "zipcode": [95124, 95124, 90210, 92130, -91000, 98000],
        }
    )
    emp_name = pd.DataFrame(
        {
            "employee_id": [123, 234, 456, 890, 567],
            "employee_first_name": ["chris", "todd", "jordan", "matt", "timothy"],
            "employee_last_name": ["gary", "nielsen", "lawson", "johnson", "todd"],
        }
    )
    return emp_data, emp_name


def preprocess_emp_data(emp_data: pd.DataFrame) -> pd.DataFrame:
    df = emp_data.copy()
    # Invalid US zip: flag optional; drop or fix upstream — here we keep row but could filter
    df["zipcode"] = pd.to_numeric(df["zipcode"], errors="coerce").astype("Int64")
    df["zipcode_valid"] = df["zipcode"].between(10000, 99999, inclusive="both")

    df["salary_clean"] = _parse_salary(df["salary"])
    df["age_years"] = _parse_age_years(df["age"])
    df["start_date_parsed"] = _parse_start_date(df["start_date"])

    # Dedupe: same employee_id multiple rows — keep latest start (most recent record)
    df = df.sort_values(["employee_id", "start_date_parsed"], na_position="last")
    df = df.drop_duplicates(subset=["employee_id"], keep="last")

    return df


def full_name_filter(
    emp_data: pd.DataFrame,
    emp_name: pd.DataFrame,
    as_of: date = AS_OF,
    min_years: float = 15.0,
    min_salary: int = 50_000,
) -> pd.DataFrame:
    emp = preprocess_emp_data(emp_data)

    names = emp_name.drop_duplicates(subset=["employee_id"], keep="first")[
        ["employee_id", "employee_last_name"]
    ]
    merged = emp.merge(names, on="employee_id", how="inner", validate="one_to_one")

    as_of_ts = pd.Timestamp(as_of)
    tenure_years = (as_of_ts - merged["start_date_parsed"]).dt.days / 365.25

    mask = (
        merged["salary_clean"].notna()
        & (merged["salary_clean"] >= min_salary)
        & merged["start_date_parsed"].notna()
        & (tenure_years >= min_years)
    )

    out = merged.loc[mask, ["employee_id", "employee_first_name", "employee_last_name"]].copy()
    out["full_name"] = (
        out["employee_first_name"].str.strip().str.title()
        + " "
        + out["employee_last_name"].str.strip().str.title()
    )
    return out[["employee_id", "full_name"]].reset_index(drop=True)


def read_emp_tables_chunked(
    emp_data_path: str,
    emp_name_path: str,
    chunksize: int = 50_000,
) -> pd.DataFrame:
    """
    For very large emp_data: process in chunks, dedupe keys in an external store (e.g. DB)
    or merge per-chunk then dedupe globally. Here: merge each chunk to full name table, concat, dedupe.
    """
    names = pd.read_csv(emp_name_path, dtype={"employee_id": "int64"})
    names = names.drop_duplicates(subset=["employee_id"], keep="first")

    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(emp_data_path, chunksize=chunksize):
        parts.append(full_name_filter(chunk, names))
    if not parts:
        return pd.DataFrame(columns=["employee_id", "full_name"])
    return pd.concat(parts, ignore_index=True).drop_duplicates(subset=["employee_id"], keep="last")


if __name__ == "__main__":
    ed, en = build_sample_frames()
    result = full_name_filter(ed, en)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    print(result)
    print("\nTenure check (for debugging):")
    emp = preprocess_emp_data(ed)
    names = en.drop_duplicates(subset=["employee_id"], keep="first")[
        ["employee_id", "employee_last_name"]
    ]
    m = emp.merge(names, on="employee_id", how="inner")
    m["tenure_years"] = (pd.Timestamp(AS_OF) - m["start_date_parsed"]).dt.days / 365.25
    print(m[["employee_id", "salary_clean", "start_date_parsed", "tenure_years"]])
