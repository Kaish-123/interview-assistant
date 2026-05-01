"""
Data loading utilities.

The unit tests pass DataFrames directly, so these functions are typically not
invoked in the test suite. They exist to match the expected module structure
for the task stubs.
"""

from __future__ import annotations

import pandas as pd


LISTINGS_URL = "https://storage.googleapis.com/public-data-337819/listings.csv"
REVIEWS_URL = "https://storage.googleapis.com/public-data-337819/reviews.csv"


def load_listings_data() -> pd.DataFrame:
    """
    Load the Airbnb listings dataset as a DataFrame.
    """
    return pd.read_csv(LISTINGS_URL)


def load_reviews_data() -> pd.DataFrame:
    """
    Load the Airbnb reviews dataset as a DataFrame.
    """
    return pd.read_csv(REVIEWS_URL)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load listings and reviews as a tuple (df_listings, df_reviews).
    """
    return load_listings_data(), load_reviews_data()

