import pandas as pd

from ._common import parse_price


def neighbourhood_with_highest_median_price_diff(
    df_listings: pd.DataFrame, df_reviews: pd.DataFrame
) -> str:
    # Note: df_reviews is unused for this task, but kept for signature consistency.
    df = df_listings.copy()
    df["price"] = parse_price(df["price"])

    super_df = df[df["host_is_superhost"].astype(str).str.lower() == "t"]
    non_df = df[df["host_is_superhost"].astype(str).str.lower() == "f"]

    median_super = super_df.groupby("neighbourhood_cleansed")["price"].median()
    median_non = non_df.groupby("neighbourhood_cleansed")["price"].median()

    # Align on neighbourhood keys; missing groups become NaN and are ignored.
    diff = (median_super - median_non).abs().dropna()
    if diff.empty:
        return ""
    return str(diff.idxmax())


__all__ = ["neighbourhood_with_highest_median_price_diff"]

