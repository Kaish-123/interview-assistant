"""Tests for ida_case2_q2 (edge cases + sample output)."""

import numpy as np
import pandas as pd
import pytest

import ida_case2_q2 as ida
from ida_case2_q2 import (
    compute_merchant_region_ats,
    mean_ats_per_product,
    parse_dates_mixed,
    prepare_revtab_products,
    result_to_2d_string_array,
    sample_data_for_expected_output,
)


def test_sample_output_matches_problem():
    t, r = sample_data_for_expected_output()
    out = mean_ats_per_product(t, r)
    assert list(out["product"]) == ["Product A", "Product C", "Product B"]
    assert pytest.approx(out["ats"].iloc[0], rel=1e-9) == 251.18
    assert pytest.approx(out["ats"].iloc[1], rel=1e-9) == 200.0
    assert pytest.approx(out["ats"].iloc[2], rel=1e-9) == 100.0


def test_testfunc_default_returns_grid():
    grid = ida.testfunc()
    assert grid[0] == ["product", "ats"]
    assert grid[1][0] == "Product A"
    assert grid[1][1] == "251.18"


def test_empty_txntab():
    r = pd.DataFrame(
        {
            "dt": ["1/1/2022"],
            "mrch_id": [1],
            "region": ["NA"],
            "product": ["Product A"],
            "revenue": [100],
        }
    )
    out = mean_ats_per_product(pd.DataFrame(), r)
    assert out.empty


def test_empty_revtab():
    t = pd.DataFrame(
        {
            "mrch_id": [1],
            "region": ["NA"],
            "amt": [10.0],
            "cnt": [1],
        }
    )
    out = mean_ats_per_product(t, pd.DataFrame())
    assert out.empty


def test_no_overlap_between_tables():
    t = pd.DataFrame(
        {
            "mrch_id": [99],
            "region": ["NA"],
            "amt": [50.0],
            "cnt": [1],
        }
    )
    r = pd.DataFrame(
        {
            "dt": ["1/1/2022"],
            "mrch_id": [1],
            "region": ["NA"],
            "product": ["Product A"],
            "revenue": [100],
        }
    )
    assert mean_ats_per_product(t, r).empty


def test_cnt_weighted_ats():
    t = pd.DataFrame(
        {
            "mrch_id": [1, 1],
            "region": ["NA", "NA"],
            "amt": [100.0, 300.0],
            "cnt": [1, 3],
        }
    )
    # sum amt 400 / sum cnt 4 = 100
    m = compute_merchant_region_ats(t)
    assert pytest.approx(m["ats"].iloc[0]) == 100.0


def test_cnt_zero_falls_back_to_mean():
    t = pd.DataFrame(
        {
            "mrch_id": [1, 1],
            "region": ["NA", "NA"],
            "amt": [10.0, 30.0],
            "cnt": [0, 0],
        }
    )
    m = compute_merchant_region_ats(t)
    assert pytest.approx(m["ats"].iloc[0]) == 20.0


def test_drops_non_positive_amt():
    t = pd.DataFrame(
        {
            "mrch_id": [1, 1, 1],
            "region": ["NA", "NA", "NA"],
            "amt": [10.0, -5.0, np.nan],
            "cnt": [1, 1, 1],
        }
    )
    m = compute_merchant_region_ats(t)
    assert len(m) == 1
    assert pytest.approx(m["ats"].iloc[0]) == 10.0


def test_without_cnt_column_uses_mean():
    t = pd.DataFrame(
        {
            "mrch_id": [1, 1],
            "region": ["EU", "EU"],
            "amt": [40.0, 60.0],
        }
    )
    m = compute_merchant_region_ats(t)
    assert pytest.approx(m["ats"].iloc[0]) == 50.0


def test_mixed_date_strings_parse():
    s = pd.Series(["2022-01-25", "11/22/2022", "bad"])
    d = parse_dates_mixed(s)
    assert pd.notna(d.iloc[0])
    assert pd.notna(d.iloc[1])
    assert pd.isna(d.iloc[2])


def test_duplicate_revtab_rows_deduped_by_latest_dt():
    r = pd.DataFrame(
        {
            "dt": ["1/1/2022", "6/1/2022"],
            "mrch_id": [1, 1],
            "region": ["NA", "NA"],
            "product": ["Product A", "Product A"],
            "revenue": [100, 200],
        }
    )
    p = prepare_revtab_products(r)
    assert len(p) == 1


def test_same_merchant_two_products_contributes_to_both_means():
    t = pd.DataFrame(
        {
            "mrch_id": [5, 5],
            "region": ["NA", "NA"],
            "amt": [100.0, 300.0],
            "cnt": [1, 1],
        }
    )
    r = pd.DataFrame(
        {
            "dt": ["1/1/2022", "2/1/2022"],
            "mrch_id": [5, 5],
            "region": ["NA", "NA"],
            "product": ["Product X", "Product Y"],
            "revenue": [1, 1],
        }
    )
    out = mean_ats_per_product(t, r)
    assert len(out) == 2
    assert (out["ats"] == 200.0).all()


def test_result_to_2d_string_array_integers_without_trailing_zeros():
    df = pd.DataFrame({"product": ["P"], "ats": [200.0]})
    g = result_to_2d_string_array(df)
    assert g[1][1] == "200"


def test_missing_columns_raises():
    with pytest.raises(ValueError, match="txntab missing"):
        compute_merchant_region_ats(pd.DataFrame({"mrch_id": [1]}))
