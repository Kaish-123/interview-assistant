# My Document – Learnings, Challenges, Assumptions & Deployment

## Assumptions

1. **Data source**: All analysis is based on the provided NYC jobs CSV. “US market” in KPI 6 is interpreted as **this NYC job market** (no external US salary data was used).

2. **Salary normalization**: For “Salary Frequency” other than Annual (e.g. Hourly, Daily), annual salary is approximated as: Hourly × 2080, Daily × 260, otherwise the midpoint of the range is used as-is.

3. **Degree level**: “Higher degree” in KPI 3 is derived from text in “Minimum Qual Requirements”: baccalaureate/bachelor/graduate/master/phd/degree → level 2; high school/equivalent → level 1; else 0 (unknown). No external education taxonomy was used.

4. **Last 2 years (KPI 5)**: Based on the maximum “Posting Date” year in the dataset; “last 2 years” = that year and the previous year.

5. **Skills (KPI 6)**: Skills are parsed from “Preferred Skills” only (comma/semicolon split, trimmed, length 3–80). Phrases with at least 2 postings are kept; “highest paid” = top by average annual salary.

6. **Feature removal**: Columns dropped in processing (e.g. Recruitment Contact, Work Location 1, To Apply, Hours/Shift, Post Until, Posting Updated) were chosen for high null/redundancy or low value for salary/category analytics, not for modeling only.

---

## Learnings

- **Schema**: All CSV columns are read as string; salary and numeric fields need explicit casting and null handling (e.g. empty string, non-numeric).
- **Dates**: “Posting Date” is ISO-like (`yyyy-MM-dd`); other date columns may be null. Using `to_date` with the same format keeps parsing consistent.
- **Job Category**: Many nulls; kept as-is and included in aggregations (e.g. “(blank)” in visualizations) so counts and KPIs reflect raw data.
- **Preferred Skills**: Free text with varied punctuation; simple split on `,` and `;` plus length filters gave a reasonable skill list for KPI 6 without NLP.

---

## Challenges & Considerations

1. **Encoding/special characters**: Some cells contain non-ASCII or curly quotes; Spark read the CSV without failing, but downstream text mining (e.g. skills, degree parsing) could be refined with explicit encoding or cleanup.

2. **KPI 6 – “Highest paid skills in the US market”**: The dataset is NYC-only. The solution reports highest-paid skills **in this dataset** and documents the assumption. A true “US market” view would require an external dataset or API.

3. **Correlation (KPI 3)**: Degree is inferred from text (keyword-based). A more robust approach would use an NER or classification model; for this assessment, the simple 0/1/2 level was sufficient to show a positive association with salary when present.

4. **Docker vs local**: The notebook uses paths like `/dataset/nyc-jobs.csv` and `/dataset/nyc-jobs-processed` to match the Docker volume mounts. If run locally (e.g. on Mac without Docker), paths would need to point to the actual dataset and output directories.

5. **PySpark 2.4.5**: The image uses Spark 2.x; API used (e.g. `to_date`, `row_number`, `explode`) is compatible. For Spark 3.x, only minor API checks would be needed.

---

## Deployment – Proposal

### Option A: Docker Compose (as in INSTALL.md)

- Use the provided `docker-compose.yml` and run:
  - `docker compose -f ./docker-compose.yml --project-name my_assesment up`
- Jupyter is on port 8888; open the notebook and run all cells.
- Output: processed Parquet under `/dataset/nyc-jobs-processed` (inside the container; same volume as `./dataset` on host if mapped).

### Option B: Scheduled/CI run (e.g. Airflow or GitHub Actions)

1. **Containerized job**: Package the notebook execution in a script (e.g. `run_assessment.py` that builds the same Spark session, runs the same logic, and writes to a chosen path).
2. **Trigger**:  
   - **Airflow**: DAG with a `DockerOperator` or `SparkSubmitOperator` that runs the job on a schedule or on file arrival.  
   - **GitHub Actions**: Workflow that checks out repo, starts Docker Compose, runs `jupyter nbconvert --execute assesment_notebook.ipynb` (or the script above), then uploads artifacts (e.g. Parquet or reports).
3. **Input/Output**: Mount or copy `nyc-jobs.csv` into the job environment; write processed data and any reports to a shared store (S3, GCS, or artifact storage).

### Option C: Local / Mac (no Docker)

1. Install PySpark and dependencies (e.g. `pip install pyspark matplotlib`).
2. Point the notebook to local paths, e.g. `./dataset/nyc-jobs.csv` and `./dataset/nyc-jobs-processed`.
3. Run the notebook in Jupyter or export to a Python script and run with a local Spark session.

---

## How to Trigger the Code

- **Interactive**: Open the Jupyter notebook in the browser (after `docker compose up`) and run “Run All”.
- **Command-line (inside container)**:
  - `docker exec -it jupyter bash` then e.g. `jupyter nbconvert --execute --to notebook /notebook/assesment_notebook.ipynb` or run a wrapper script that uses the same logic.
- **Scheduled**: Use one of the deployment options above (Airflow, GitHub Actions, or cron with a script that launches the same pipeline and writes to the target path).

---

## Summary

The solution provides data exploration, six KPIs (with visualizations), a reusable processing pipeline (cleaning, three feature-engineering steps, and feature removal), test cases, and writes processed data to Parquet. Assumptions and limitations (especially NYC-only data and keyword-based degree/skills) are documented so reviewers can align with expectations and extend the work (e.g. real US salary data, better NLP for skills/degree) if needed.
