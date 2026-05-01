import pandas as pd

from ._common import host_since_to_year, parse_t_f_bool, choose_second_largest_by_abs


def host_attribute_with_second_highest_correlation_to_reviews(
    df_listings: pd.DataFrame, df_reviews: pd.DataFrame
) -> str:
    """
    Find the host attribute with the second-strongest (by abs value) Pearson
    correlation with number_of_reviews.
    """
    df = df_listings.copy()

    target_col = "number_of_reviews"

    # Convert host attributes to numeric values for correlation.
    attr_values = {}

    # Order matters for tie-breaking.
    host_attrs_in_order = [
        "host_since",
        "host_listings_count",
        "host_identity_verified",
        "calculated_host_listings_count",
        "host_is_superhost",
    ]

    attr_values["host_since"] = host_since_to_year(df["host_since"])
    attr_values["host_listings_count"] = pd.to_numeric(df["host_listings_count"], errors="coerce")
    attr_values["host_identity_verified"] = parse_t_f_bool(df["host_identity_verified"])
    attr_values["calculated_host_listings_count"] = pd.to_numeric(
        df["calculated_host_listings_count"], errors="coerce"
    )
    attr_values["host_is_superhost"] = parse_t_f_bool(df["host_is_superhost"])

    y = pd.to_numeric(df[target_col], errors="coerce")

    scored = []
    for attr in host_attrs_in_order:
        x = attr_values[attr]
        corr = x.corr(y)
        if pd.notna(corr):
            scored.append((abs(float(corr)), attr))

    # If ties occur, sorting is stable => original order in `host_attrs_in_order` is kept.
    scored.sort(key=lambda t: t[0], reverse=True)
    if len(scored) < 2:
        return ""
    return scored[1][1]


__all__ = ["host_attribute_with_second_highest_correlation_to_reviews"]

