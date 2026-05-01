import pandas as pd

from ._common import parse_t_f_bool, parse_price


def average_diff_superhost_nonsuperhost_review_score(
    df_listings: pd.DataFrame, df_reviews: pd.DataFrame
) -> float:
    """
    Average difference in review_scores_rating between superhosts and non-superhosts.
    Return: avg(superhosts) - avg(non-superhosts).
    """
    df = df_listings.copy()

    # Keep a consistent mapping from 't'/'f' to 1/0 regardless of dtype.
    superhost_mask = parse_t_f_bool(df["host_is_superhost"]) == 1

    rating_col = "review_scores_rating"
    avg_super = df.loc[superhost_mask, rating_col].mean()
    avg_non_super = df.loc[~superhost_mask, rating_col].mean()

    avg_super_val = 0.0 if pd.isna(avg_super) else float(avg_super)
    avg_non_super_val = 0.0 if pd.isna(avg_non_super) else float(avg_non_super)
    return avg_super_val - avg_non_super_val


__all__ = ["average_diff_superhost_nonsuperhost_review_score"]

