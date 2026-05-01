import pandas as pd

from ._common import parse_price


def prof_nonprof_host_price_diff(
    df_listings: pd.DataFrame, df_reviews: pd.DataFrame
) -> float:
    """
    Professional host: host_id that has listings in more than 5 different
    neighbourhood_cleansed locations.
    Return: (professional_host_avg_price - non_professional_host_avg_price).
    """
    df = df_listings.copy()
    df["price"] = parse_price(df["price"])

    location_counts = df.groupby("host_id")["neighbourhood_cleansed"].nunique()
    professional_hosts = location_counts[location_counts > 5].index

    prof_mean = df[df["host_id"].isin(professional_hosts)]["price"].mean()
    non_prof_mean = df[~df["host_id"].isin(professional_hosts)]["price"].mean()

    # If there are no professional hosts, treat their mean price as 0.0.
    prof_mean_val = 0.0 if pd.isna(prof_mean) else float(prof_mean)
    non_prof_mean_val = 0.0 if pd.isna(non_prof_mean) else float(non_prof_mean)
    return prof_mean_val - non_prof_mean_val


__all__ = ["prof_nonprof_host_price_diff"]

