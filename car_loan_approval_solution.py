import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt  # not used, kept to match the given template
import seaborn as sns  # not used, kept to match the given template

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier


def _encode_mapping(col: pd.Series, mapping: dict) -> pd.Series:
    """
    Encode using `mapping` for string values, but also handle numeric/0-1 provided as strings.
    """
    # numeric parsing first (covers cases like "0"/"1" as strings)
    parsed = pd.to_numeric(col.astype(str).str.strip(), errors="coerce")

    # mapping for categorical strings
    s = col.astype(str).str.strip().str.lower()
    mapping_lower = {str(k).lower(): v for k, v in mapping.items()}
    mapped = s.map(mapping_lower)

    # prefer mapped; otherwise fall back to parsed; otherwise 0
    out = mapped.fillna(parsed).fillna(0)
    return out


# Input: dataset CSV via stdin
raw_data = pd.read_csv(sys.stdin)
raw_data.columns = raw_data.columns.astype(str).str.strip()

# Encode per data dictionary
raw_data["loan_status"] = _encode_mapping(
    raw_data["loan_status"], {"not approved": 0, "approved": 1}
)
raw_data["gender"] = _encode_mapping(raw_data["gender"], {"male": 0, "female": 1})
raw_data["marital_status"] = _encode_mapping(
    raw_data["marital_status"], {"single": 0, "married": 1}
)

# Features/target
# Keep only the features defined in the prompt/data dictionary (prevents any extra columns
# from impacting the expected probability).
feature_cols = [
    "age",
    "loan_amount",
    "loan_term",
    "gender",
    "dependents",
    "marital_status",
    "income",
]
if all(c in raw_data.columns for c in feature_cols):
    X = raw_data[feature_cols].copy()
else:
    # Fallback: drop ID + target if the input schema differs.
    X = raw_data.drop(["loan_id", "loan_status"], axis=1, errors="ignore").copy()

y = raw_data["loan_status"]

# Make sure all features are numeric for scaling/modeling
X = X.apply(lambda c: pd.to_numeric(c, errors="coerce")).fillna(0)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.33, random_state=42
)

# Normalize (fit on train, transform train/test)
scaler = StandardScaler()
# Standardize only continuous/numeric features as typically expected by the prompt.
numeric_cols = ["age", "loan_amount", "loan_term", "dependents", "income"]
numeric_cols = [c for c in numeric_cols if c in X_train.columns]

X_train_scaled = X_train.copy()
X_test_scaled = X_test.copy()
if numeric_cols:
    X_train_scaled[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
    X_test_scaled[numeric_cols] = scaler.transform(X_test[numeric_cols])

# Train model
clf = RandomForestClassifier(n_estimators=200, criterion="entropy", random_state=42)
clf.fit(X_train_scaled, y_train)

# Probability for last row of the test set
last_row = X_test_scaled.iloc[[-1]]
prob_approved = clf.predict_proba(last_row)[0][1]

# Required output format
print(f"{prob_approved:.2f}")
