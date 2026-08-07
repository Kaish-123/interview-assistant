# GenAI Claim Summary Pilot — Deliverables Responses

Paste each response into the **Response** column on the Deliverables sheet.

---

## ID 1 — Data quality issues

**Response:**

I found **more than five data-quality issues** that should be fixed or excluded before sharing results with leadership:

1. **Impossible negative durations**  
   Examples: `observed_review_min = -5` (C013), `expected_manual_review_min = -50` (C014), `cycle_days = -3` (C015).  
   **Why it matters:** Negatives break time-saved math and can reverse the GenAI vs control comparison.  
   **Handle:** Flag as invalid; exclude from averages until source systems confirm the correct values (or treat as missing if unrecoverable).

2. **Inconsistent coding of binary fields**  
   Examples: `genai_summary_used = "yes"` instead of `1` (C017); `material_error_flag = "FALSE"` instead of `0` (C019).  
   **Why it matters:** SQL/pandas aggregates will drop or mis-group mixed types, undercounting GenAI usage and error rates.  
   **Handle:** Standardize to 0/1 integers with an explicit mapping (`yes/true/1 → 1`, `no/false/0 → 0`); reject unknowns.

3. **Non-numeric text in numeric columns**  
   Example: `expected_manual_review_min = "forty"` (C018).  
   **Why it matters:** Cast failures remove the row from averages silently.  
   **Handle:** Parse known word numbers where safe; otherwise null and exclude from time metrics.

4. **Extreme outlier in review time**  
   Example: `observed_review_min = 5000` (C023) vs typical 14–90 minutes.  
   **Why it matters:** One bad point can dominate mean time saved and make GenAI look harmful or miraculous.  
   **Handle:** Cap or exclude using a rule (e.g., >3× IQR or >P99); report medians alongside means.

5. **Invalid / non-standard categories**  
   Examples: `line_of_business = "Unknown"` (C020), `complexity = "Urgent"` (C021), `group_type = "Test"` (C022).  
   **Why it matters:** Stratified metrics by LOB/complexity/group become unstable or misleading.  
   **Handle:** Remap if business rules exist; else hold out of stratified reporting and document separately.

6. **Out-of-range quality score**  
   Example: `summary_quality_score = 7` (C016) if the scale is 1–5.  
   **Why it matters:** Inflates average quality and hides true quality risk.  
   **Handle:** Validate against allowed range; null invalid scores.

7. **Structural missingness on GenAI-only fields**  
   `summary_quality_score`, `material_error_flag`, `summary_generated_date`, and `user_feedback_rating` are blank whenever GenAI was not used.  
   **Why it matters:** This is expected for some fields, but it means quality/error cannot be compared to a true control—only among GenAI claims.  
   **Handle:** Do not impute; report quality/error **only for GenAI-used claims**, and use review-time/cycle-time for Pilot vs Control comparisons.

8. **Stray / misaligned values in date column**  
   Examples in later rows: date-like fragments and text such as “not a date” in `summary_generated_date`.  
   **Why it matters:** Breaks date parsing and any time-trend analysis.  
   **Handle:** Parse with strict ISO/date formats; set invalid to null.

**Before reporting:** document exclusions, show n before/after cleaning, and lead with medians + cleaned means so leadership sees sensitivity to dirty rows.

---

## ID 2 — First 3 metrics

**Response:**

The first three metrics I would calculate:

1. **Average (and median) review time saved**  
   `time_saved = expected_manual_review_min − observed_review_min`, compared for GenAI-used vs not used (and Pilot vs Control).  
   **Why:** This is the core value question—does the tool reduce adjuster review effort?

2. **Material error rate among GenAI-used claims**  
   `SUM(material_error_flag) / COUNT(*)` where GenAI was used.  
   **Why:** Time savings are not useful if summaries introduce material risk; leadership needs a value-vs-risk view.

3. **Average summary quality score (and % scoring ≥4)**  
   Among GenAI-used claims with a valid 1–5 score.  
   **Why:** Complements error rate with a usability/quality signal; early warning if quality is weak on High complexity or certain LOBs.

These three cover **efficiency**, **risk**, and **quality**—the minimum balanced scorecard for a GenAI claims pilot.

---

## ID 3 — SQL query

**Response:**

```sql
SELECT
    line_of_business,
    complexity,
    COUNT(*) AS num_claims,
    SUM(CASE WHEN genai_summary_used = 1 THEN 1 ELSE 0 END) AS num_genai_used,
    ROUND(
        100.0 * SUM(CASE WHEN genai_summary_used = 1 THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS pct_genai_used,
    ROUND(
        AVG(
            CASE
                WHEN expected_manual_review_min > 0
                 AND observed_review_min > 0
                THEN expected_manual_review_min - observed_review_min
            END
        ),
        1
    ) AS avg_time_saved_min,
    ROUND(
        AVG(
            CASE
                WHEN genai_summary_used = 1
                 AND summary_quality_score BETWEEN 1 AND 5
                THEN summary_quality_score
            END
        ),
        2
    ) AS avg_quality_score,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN genai_summary_used = 1 AND material_error_flag = 1 THEN 1
                ELSE 0
            END
        ) / NULLIF(
            SUM(CASE WHEN genai_summary_used = 1 THEN 1 ELSE 0 END),
            0
        ),
        1
    ) AS material_error_rate_pct_among_genai
FROM synthetic_data
/* Optional: add WHERE clause after cleaning dirty rows / standardizing types */
GROUP BY line_of_business, complexity
ORDER BY line_of_business, complexity;
```

**Note:** In production I would first clean/cast `genai_summary_used` and `material_error_flag` to 0/1 and filter invalid negatives/outliers in a CTE before this aggregation.

---

## ID 4 — Estimating whether GenAI reduces review time

**Response:**

**With this pilot sample:**  
I would (1) clean invalid rows, (2) compute `time_saved` per claim, (3) compare GenAI-used vs not-used **and** Pilot vs Control, (4) check that the difference is not driven by mix (LOB/complexity), and (5) report median and mean with n. On the clean subset of early rows, GenAI claims show clear positive time savings (roughly ~10–15 minutes on average), while non-GenAI claims slightly overrun expected time. That is directional evidence of benefit, but **not causal proof**—sample size is small, assignment may not be random, and dirty rows can flip averages.

**With a larger dataset I would:**  
- Use stratified or matched comparisons (same LOB + complexity), or regression controlling for LOB, complexity, adjuster experience, and expected review minutes.  
- Prefer randomized Pilot/Control or difference-in-differences if rollout was phased.  
- Report confidence intervals / significance tests, segment by High complexity (where error risk may be higher), and track cycle days and reopen/complaint rates as secondary outcomes.  
- Monitor quality and material-error rates over time, not only average minutes saved.

---

## ID 5 — Recommendation to Claims Leadership

**Response:**

**Recommendation: Continue testing / expand the pilot carefully — do not full-scale yet.**

**What the sample suggests**
- Directionally, GenAI summaries appear to **reduce review time** versus expected manual effort on valid GenAI rows.  
- Non-GenAI rows tend to meet or slightly exceed expected review time, which supports that the savings are associated with tool use, not just easier claims.  
- Quality is mixed: several summaries score well (4–5), but **material errors appear on some Property / higher-complexity claims**, so risk is not zero.

**Why not full scale now**
- Data quality problems (negatives, text-in-numeric fields, outliers, invalid categories) mean leadership metrics are not yet trustworthy without cleaning.  
- Sample is small and short-lived; results can change with more LOBs and High-complexity volume.  
- Quality/error fields only exist for GenAI-used claims, so risk comparison to a true control is incomplete.

**What I would tell leadership**
1. Keep the pilot running with cleaner logging and validated fields.  
2. Expand next into **Auto Low/Medium** (stronger early signal, lower apparent error).  
3. Pause or gate **High-complexity / Property** until error rate and quality meet a defined threshold.  
4. Revisit scale-up when you have larger n, stable data quality, and error rate within risk appetite.

**One-liner for non-technical stakeholders:**  
*The tool looks promising for saving adjuster time, but the data is messy and error risk shows up on harder claims—keep testing with tighter controls before a broad rollout.*
