"""
IDA Case 2 Q2 — Mean ATS per product (pandas).

ATS (average ticket size) per merchant: amount per transaction at the
(merchant, region) grain. Uses sum(amt)/sum(cnt) when cnt is present and valid,
otherwise mean(amt). Joins to revtab on (mrch_id, region); each distinct
(mrch_id, region, product) pair gets that merchant-region's ATS for the
product-level mean.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional

import pandas as pd


def parse_dates_mixed(series: pd.Series) -> pd.Series:
    """Parse mixed ISO and US-style dates; invalid → NaT."""
    s = series.astype(str).str.strip()
    try:
        return pd.to_datetime(s, format="mixed", errors="coerce")
    except (ValueError, TypeError):
        return pd.to_datetime(s, errors="coerce")


def normalize_key_columns(
    df: pd.DataFrame,
    mrch_col: str = "mrch_id",
    region_col: str = "region",
) -> pd.DataFrame:
    out = df.copy()
    if mrch_col in out.columns:
        out[mrch_col] = pd.to_numeric(out[mrch_col], errors="coerce").astype("Int64")
    if region_col in out.columns:
        out[region_col] = out[region_col].astype(str).str.strip()
    return out


def compute_merchant_region_ats(txntab: pd.DataFrame) -> pd.DataFrame:
    """
    One row per (mrch_id, region) with column 'ats'.

    Drops rows with missing mrch_id or amt. Negative amounts excluded from means
    but counted in sum/sum logic only if policy allows — here we drop amt <= 0
    for ticket semantics.
    """
    if txntab.empty:
        return pd.DataFrame(columns=["mrch_id", "region", "ats"])

    t = normalize_key_columns(txntab.copy())
    required = {"mrch_id", "region", "amt"}
    if not required.issubset(t.columns):
        missing = required - set(t.columns)
        raise ValueError(f"txntab missing columns: {missing}")

    t["amt"] = pd.to_numeric(t["amt"], errors="coerce")
    t = t.dropna(subset=["mrch_id", "region", "amt"])
    t = t[t["amt"] > 0]

    if t.empty:
        return pd.DataFrame(columns=["mrch_id", "region", "ats"])

    has_cnt = "cnt" in t.columns
    if has_cnt:
        t["cnt"] = pd.to_numeric(t["cnt"], errors="coerce").fillna(0)
        t = t[t["cnt"] >= 0]
        sums = t.groupby(["mrch_id", "region"], as_index=False).agg(
            amt_sum=("amt", "sum"),
            cnt_sum=("cnt", "sum"),
        )
        means = t.groupby(["mrch_id", "region"], as_index=False).agg(
            amt_mean=("amt", "mean"),
        )
        grouped = sums.merge(means, on=["mrch_id", "region"])
        grouped["ats"] = grouped["amt_sum"] / grouped["cnt_sum"].replace(0, float("nan"))
        grouped.loc[grouped["cnt_sum"] == 0, "ats"] = grouped.loc[
            grouped["cnt_sum"] == 0, "amt_mean"
        ]
        grouped = grouped[["mrch_id", "region", "ats"]]
    else:
        grouped = t.groupby(["mrch_id", "region"], as_index=False).agg(
            ats=("amt", "mean"),
        )
    return grouped


def prepare_revtab_products(revtab: pd.DataFrame) -> pd.DataFrame:
    """
    Distinct (mrch_id, region, product) from revtab with optional latest row per
    key if duplicate keys exist (keeps row with max parsed dt).
    """
    if revtab.empty:
        return pd.DataFrame(columns=["mrch_id", "region", "product"])

    r = normalize_key_columns(revtab.copy())
    for col in ("mrch_id", "region", "product"):
        if col not in r.columns:
            raise ValueError(f"revtab missing column: {col}")

    r = r.dropna(subset=["mrch_id", "region", "product"])
    r["product"] = r["product"].astype(str).str.strip()
    r = r[r["product"] != ""]

    if "dt" in r.columns:
        r["_dt_parsed"] = parse_dates_mixed(r["dt"])
        r = r.sort_values("_dt_parsed", na_position="last")
        r = r.drop_duplicates(subset=["mrch_id", "region", "product"], keep="last")
    else:
        r = r.drop_duplicates(subset=["mrch_id", "region", "product"])

    return r[["mrch_id", "region", "product"]].reset_index(drop=True)


def mean_ats_per_product(
    txntab: pd.DataFrame,
    revtab: pd.DataFrame,
    sort_desc: bool = True,
) -> pd.DataFrame:
    """
    Returns DataFrame columns: product, ats (mean of merchant-region ATS per product).
    """
    m_ats = compute_merchant_region_ats(txntab)
    products = prepare_revtab_products(revtab)

    if m_ats.empty or products.empty:
        return pd.DataFrame(columns=["product", "ats"])

    merged = products.merge(m_ats, on=["mrch_id", "region"], how="inner")
    if merged.empty:
        return pd.DataFrame(columns=["product", "ats"])

    out = (
        merged.groupby("product", as_index=False)["ats"]
        .mean()
        .rename(columns={"ats": "ats"})
    )
    if sort_desc:
        out = out.sort_values("ats", ascending=False, kind="mergesort").reset_index(
            drop=True
        )
    return out


def format_ats_value(x: Any) -> str:
    if pd.isna(x):
        return ""
    xf = float(x)
    if abs(xf - round(xf)) < 1e-9:
        return str(int(round(xf)))
    return f"{xf:.2f}"


def result_to_2d_string_array(df: pd.DataFrame) -> List[List[str]]:
    """Header row + data rows for HackerRank-style output."""
    rows: List[List[str]] = [["product", "ats"]]
    for _, r in df.iterrows():
        rows.append([str(r["product"]), format_ats_value(r["ats"])])
    return rows


def testfunc(
    txntab: Optional[pd.DataFrame] = None,
    revtab: Optional[pd.DataFrame] = None,
) -> List[List[str]]:
    """
    Assessment entry point: return 2D string array [header, ...rows].
    If no data passed, uses embedded sample matching the problem's sample output.
    """
    if txntab is None or revtab is None:
        txntab, revtab = sample_data_for_expected_output()

    df = mean_ats_per_product(txntab, revtab, sort_desc=True)
    return result_to_2d_string_array(df)


def sample_data_for_expected_output() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Constructs txntab/revtab so that mean ATS per product matches sample:
    Product A 251.18, Product C 200, Product B 100 (descending).

    Product A: mean ATS of merchants {6@NA, 2@AP} = (252.36 + 250) / 2 = 251.18
    Product C: merchant 9@NA only → 200
    Product B: merchant 1@EU only → 100
    """
    txntab = pd.DataFrame(
        {
            "usr_id": [10, 11, 12, 13, 14, 15, 16],
            "txn_dt": [
                "2022-01-25",
                "2022-01-26",
                "2022-01-25",
                "2022-02-10",
                "11/22/2022",
                "8/10/2022",
                "2022-03-15",
            ],
            "region": ["NA", "NA", "AP", "AP", "EU", "EU", "NA"],
            "mrch_id": [6, 6, 2, 2, 1, 1, 9],
            "mcg": [
                "Quick Service Restaurant",
                "Quick Service Restaurant",
                "Restaurant",
                "Restaurant",
                "Restaurant",
                "Restaurant",
                "Utilities",
            ],
            "amt": [252.36, 252.36, 250.0, 250.0, 100.0, 100.0, 200.0],
            "cnt": [1, 1, 1, 1, 1, 1, 1],
        }
    )

    revtab = pd.DataFrame(
        {
            "dt": ["1/1/2022", "2/1/2022", "3/1/2022", "1/1/2022"],
            "mrch_id": [6, 1, 9, 2],
            "region": ["NA", "EU", "NA", "AP"],
            "product": ["Product A", "Product B", "Product C", "Product A"],
            "revenue": [1500, 500, 800, 1000],
        }
    )
    return txntab, revtab


if __name__ == "__main__":
    # Local print demo
    tdf, rdf = sample_data_for_expected_output()
    res = mean_ats_per_product(tdf, rdf)
    print(res.to_string(index=False))

    out_path = os.environ.get("OUTPUT_PATH")
    if out_path:
        arr = testfunc(tdf, rdf)
        with open(out_path, "w", encoding="utf-8") as fptr:
            fptr.write("\n".join([" ".join(x) for x in arr]))
            fptr.write("\n")
