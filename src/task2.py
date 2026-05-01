import pandas as pd

from ._common import parse_price


def review_score_with_highest_correlation_to_price(
    df_listings: pd.DataFrame, df_reviews: pd.DataFrame
) -> str:
    # df_reviews unused for this task.
    df = df_listings.copy()
    df["price"] = parse_price(df["price"])

    review_score_cols = [
        "review_scores_rating",
        "review_scores_accuracy",
        "review_scores_cleanliness",
        "review_scores_checkin",
        "review_scores_communication",
        "review_scores_location",
        "review_scores_value",
    ]

    abs_corr_by_col = {}
    for col in review_score_cols:
        corr = df[col].corr(df["price"])
        abs_corr_by_col[col] = abs(corr) if pd.notna(corr) else float("-inf")

    # Preserve list order for tie-breaking by constructing a Series in that order.
    abs_corr_series = pd.Series([abs_corr_by_col[c] for c in review_score_cols], index=review_score_cols)
    best_col = abs_corr_series.idxmax()
    return str(best_col)


__all__ = ["review_score_with_highest_correlation_to_price"]

