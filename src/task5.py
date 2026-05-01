import pandas as pd

from ._common import parse_price


def listing_with_best_expected_revenue(
    df_listings: pd.DataFrame, df_reviews: pd.DataFrame
) -> int:
    """
    Expected revenue estimate for each listing (filtered to minimum_nights <= 7):
      - Only 60% of guests leave a review => expected_guests = reviews_count / 0.6
      - Each guest stays exactly minimum_nights nights
      - expected_revenue = price_per_night * expected_guests * minimum_nights

    "Last 12 months" is evaluated relative to the current runtime date.

    Returns the (0-based) DataFrame index label of the best listing (max revenue).
    """
    df = df_listings.copy()
    df["price"] = parse_price(df["price"])

    eligible = df[df["minimum_nights"] <= 7].copy()
    if eligible.empty:
        return -1

    # Filter reviews to last 12 months relative to "now".
    reviews = df_reviews.copy()
    reviews["date"] = pd.to_datetime(reviews["date"], errors="coerce")
    cutoff = pd.Timestamp.now() - pd.DateOffset(months=12)
    recent_reviews = reviews[reviews["date"] >= cutoff]

    review_counts = recent_reviews.groupby("listing_id").size()

    # Map counts back to eligible listings (missing => 0 reviews).
    eligible_reviews_count = eligible["id"].map(review_counts).fillna(0).astype(float)

    expected_guests = eligible_reviews_count / 0.6
    expected_revenue = eligible["price"] * expected_guests * eligible["minimum_nights"]

    # If everything is equal/NaN, idxmax returns the first label.
    best_idx = expected_revenue.idxmax()
    return int(best_idx)


__all__ = ["listing_with_best_expected_revenue"]

