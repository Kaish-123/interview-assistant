import pandas as pd

from ._common import parse_price


def price_premium_for_entire_homes(
    df_listings: pd.DataFrame, df_reviews: pd.DataFrame
) -> float:
    """
    For each neighbourhood, compute:
      median(price | room_type == 'Entire home/apt') - median(price | other room types)
    and then average these premiums across neighbourhoods that have both groups.
    """
    df = df_listings.copy()
    df["price"] = parse_price(df["price"])

    is_entire = df["room_type"].astype(str).str.lower() == "entire home/apt"

    entire_median = df[is_entire].groupby("neighbourhood_cleansed")["price"].median()
    other_median = df[~is_entire].groupby("neighbourhood_cleansed")["price"].median()

    premium_by_neighbourhood = (entire_median - other_median).dropna()
    if premium_by_neighbourhood.empty:
        return 0.0
    return float(premium_by_neighbourhood.mean())


__all__ = ["price_premium_for_entire_homes"]

