"""
GenAI Claim Summary pilot — quick analysis on the synthetic data
visible in the assessment screenshots (plus documented dirty rows).
"""

from __future__ import annotations

import pandas as pd

# Rows clearly readable from the Synthetic Data sheet (C001–C014),
# plus later dirty rows called out in the screenshots for DQ demo.
raw = [
    # claim_id, lob, complexity, group, genai, expected, observed, cycle, quality, error, adj_exp, feedback
    ("C001", "Auto", "Low", "Pilot", 1, 25, 14, 8, 5, 0, 3, 5),
    ("C002", "Auto", "Low", "Pilot", 1, 25, 18, 9, 4, 0, 1, 4),
    ("C003", "Auto", "Medium", "Pilot", 1, 40, 25, 15, 4, 0, 5, 4),
    ("C004", "Auto", "Medium", "Pilot", 0, 40, 43, 18, None, None, 7, None),
    ("C005", "Property", "Medium", "Pilot", 1, 50, 35, 20, 3, 1, 2, 3),
    ("C006", "Property", "High", "Pilot", 1, 75, 70, 33, 2, 1, 8, 2),
    ("C007", "BI", "High", "Pilot", 0, 90, 92, 48, None, None, 12, None),
    ("C008", "AB", "Medium", "Control", 0, 60, 62, 35, None, None, 4, None),
    ("C009", "AB", "Medium", "Pilot", 1, 60, 45, 28, 4, 0, 6, 4),
    ("C010", "Property", "Low", "Control", 0, 30, 32, 12, None, None, 2, None),
    ("C011", "Auto", "Low", "Control", 0, 25, 26, 10, None, None, 1, None),
    ("C012", "BI", "High", "Pilot", 1, 90, 65, 44, 4, 0, 10, 4),
    ("C013", "Auto", "Low", "Pilot", 1, 25, -5, 7, 5, 0, None, None),  # invalid observed
    ("C014", "Property", "Medium", "Pilot", 1, -50, 30, 19, 4, 0, None, None),  # invalid expected
    # Documented dirty examples from later rows (partial fields for DQ flags)
    ("C015", "Auto", "Low", "Pilot", 1, 25, 20, -3, 4, 0, None, None),  # invalid cycle
    ("C016", "Auto", "Medium", "Pilot", 1, 40, 28, 16, 7, 0, None, None),  # quality out of range
    ("C017", "AB", "Medium", "Pilot", "yes", None, 40, 20, 4, 0, None, None),  # bad genai + missing expected
    ("C018", "Auto", "Medium", "Pilot", 1, "forty", 28, 16, 4, 0, None, None),  # text expected
    ("C019", "Property", "Low", "Control", 0, 30, 31, 11, None, "FALSE", None, None),  # text error flag
    ("C020", "Unknown", "Low", "Pilot", 1, 25, 18, 9, 4, 0, None, None),  # invalid LOB
    ("C021", "Auto", "Urgent", "Pilot", 1, 40, 30, 14, 4, 0, None, None),  # invalid complexity
    ("C022", "BI", "High", "Test", 0, 90, 95, 50, None, None, None, None),  # invalid group
    ("C023", "Property", "Medium", "Pilot", 1, 50, 5000, 22, 3, 1, None, None),  # outlier observed
]

cols = [
    "claim_id",
    "line_of_business",
    "complexity",
    "group_type",
    "genai_summary_used",
    "expected_manual_review_min",
    "observed_review_min",
    "cycle_days",
    "summary_quality_score",
    "material_error_flag",
    "adjuster_experience_years",
    "user_feedback_rating",
]
df = pd.DataFrame(raw, columns=cols)

VALID_LOB = {"Auto", "Property", "BI", "AB"}
VALID_COMPLEXITY = {"Low", "Medium", "High"}
VALID_GROUP = {"Pilot", "Control"}


def standardize_binary(val):
    if pd.isna(val):
        return pd.NA
    if isinstance(val, (int, float)) and val in (0, 1):
        return int(val)
    s = str(val).strip().lower()
    if s in {"1", "yes", "true", "y"}:
        return 1
    if s in {"0", "no", "false", "n"}:
        return 0
    return pd.NA


def to_number(val):
    if pd.isna(val):
        return pd.NA
    if isinstance(val, (int, float)):
        return val
    word_map = {"forty": 40, "thirty": 30, "twenty": 20, "fifty": 50}
    s = str(val).strip().lower()
    if s in word_map:
        return word_map[s]
    try:
        return float(s)
    except ValueError:
        return pd.NA


clean = df.copy()
clean["genai_summary_used"] = clean["genai_summary_used"].map(standardize_binary)
clean["material_error_flag"] = clean["material_error_flag"].map(standardize_binary)
clean["expected_manual_review_min"] = clean["expected_manual_review_min"].map(to_number)
clean["observed_review_min"] = clean["observed_review_min"].map(to_number)
clean["cycle_days"] = clean["cycle_days"].map(to_number)
clean["summary_quality_score"] = clean["summary_quality_score"].map(to_number)

# Validity flags
clean["valid_time"] = (
    clean["expected_manual_review_min"].notna()
    & clean["observed_review_min"].notna()
    & (clean["expected_manual_review_min"] > 0)
    & (clean["observed_review_min"] > 0)
    & (clean["observed_review_min"] < 500)  # drop extreme outliers like 5000
)
clean["valid_categories"] = (
    clean["line_of_business"].isin(VALID_LOB)
    & clean["complexity"].isin(VALID_COMPLEXITY)
    & clean["group_type"].isin(VALID_GROUP)
)
clean["valid_quality"] = clean["summary_quality_score"].between(1, 5)
clean["time_saved"] = clean["expected_manual_review_min"] - clean["observed_review_min"]

print("=" * 72)
print("DATA QUALITY FLAGS (examples)")
print("=" * 72)
issues = []
for _, r in df.iterrows():
    flags = []
    if isinstance(r.observed_review_min, (int, float)) and r.observed_review_min is not None:
        if r.observed_review_min < 0:
            flags.append("negative observed_review_min")
        if r.observed_review_min >= 500:
            flags.append("extreme observed_review_min outlier")
    if isinstance(r.expected_manual_review_min, (int, float)) and r.expected_manual_review_min is not None:
        if r.expected_manual_review_min < 0:
            flags.append("negative expected_manual_review_min")
    if isinstance(r.cycle_days, (int, float)) and r.cycle_days is not None and r.cycle_days < 0:
        flags.append("negative cycle_days")
    if isinstance(r.genai_summary_used, str):
        flags.append(f"non-binary genai_summary_used={r.genai_summary_used!r}")
    if isinstance(r.expected_manual_review_min, str):
        flags.append(f"non-numeric expected={r.expected_manual_review_min!r}")
    if isinstance(r.material_error_flag, str):
        flags.append(f"non-binary material_error_flag={r.material_error_flag!r}")
    if r.line_of_business not in VALID_LOB:
        flags.append(f"invalid LOB={r.line_of_business!r}")
    if r.complexity not in VALID_COMPLEXITY:
        flags.append(f"invalid complexity={r.complexity!r}")
    if r.group_type not in VALID_GROUP:
        flags.append(f"invalid group_type={r.group_type!r}")
    if isinstance(r.summary_quality_score, (int, float)) and r.summary_quality_score is not None:
        if not (1 <= r.summary_quality_score <= 5):
            flags.append(f"out-of-range quality={r.summary_quality_score}")
    if flags:
        issues.append((r.claim_id, "; ".join(flags)))

for cid, msg in issues:
    print(f"  {cid}: {msg}")
print(f"\nTotal flagged rows: {len(issues)} / {len(df)}")

analysis = clean[clean["valid_time"] & clean["valid_categories"] & clean["genai_summary_used"].notna()].copy()

print("\n" + "=" * 72)
print("CORE METRICS (after cleaning invalid times/categories)")
print("=" * 72)
print(f"Rows used: {len(analysis)} / {len(df)}")

for label, mask in [
    ("GenAI used = 1", analysis["genai_summary_used"] == 1),
    ("GenAI used = 0", analysis["genai_summary_used"] == 0),
]:
    sub = analysis.loc[mask]
    print(f"\n{label} (n={len(sub)})")
    print(f"  mean time saved (min):   {sub['time_saved'].mean():.1f}")
    print(f"  median time saved (min): {sub['time_saved'].median():.1f}")
    print(f"  mean observed (min):     {sub['observed_review_min'].mean():.1f}")
    print(f"  mean expected (min):     {sub['expected_manual_review_min'].mean():.1f}")

genai = analysis[analysis["genai_summary_used"] == 1]
q = genai[genai["valid_quality"]]
err = genai[genai["material_error_flag"].notna()]
print("\nGenAI quality / risk")
print(f"  avg quality score (1-5): {q['summary_quality_score'].mean():.2f} (n={len(q)})")
print(f"  pct quality >= 4:        {(q['summary_quality_score'] >= 4).mean() * 100:.1f}%")
print(
    f"  material error rate:     {err['material_error_flag'].mean() * 100:.1f}% "
    f"({int(err['material_error_flag'].sum())}/{len(err)})"
)

print("\n" + "=" * 72)
print("BY line_of_business x complexity (cleaned)")
print("=" * 72)
g = analysis.groupby(["line_of_business", "complexity"], dropna=False)
summary = g.agg(
    num_claims=("claim_id", "count"),
    num_genai=("genai_summary_used", "sum"),
    avg_time_saved=("time_saved", "mean"),
)
summary["pct_genai"] = (summary["num_genai"] / summary["num_claims"] * 100).round(1)
genai_only = analysis[analysis["genai_summary_used"] == 1]
q_err = (
    genai_only.groupby(["line_of_business", "complexity"])
    .agg(
        avg_quality=("summary_quality_score", lambda s: s[s.between(1, 5)].mean()),
        material_error_rate=("material_error_flag", "mean"),
    )
)
out = summary.join(q_err, how="left")
print(out.round(2).to_string())

print("\n" + "=" * 72)
print("RECOMMENDATION: Continue testing / expand carefully — do not full-scale yet.")
print("=" * 72)
