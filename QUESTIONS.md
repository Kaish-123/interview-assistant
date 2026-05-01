# Written answers

## Question 1 — Tableau Dashboard Design

**Charts**

- **Funnel bar or conversion funnel chart (weekly):** Distinct users (or sessions) at each stage—page view → add to cart → checkout → purchase—with week on the x-axis or as small multiples. Shows where the largest absolute drops occur week over week.
- **Stage-to-stage conversion rates:** Bar chart or line chart of conversion from each step to the next (e.g., view→cart, cart→checkout, checkout→purchase) by week and segment. Highlights which transition worsened even when top-of-funnel volume is stable.
- **Page view to purchase trend:** Line chart of the Task 1 metric (purchase users ÷ page view users × 100) over time, optionally with reference lines or goals. Gives a single health metric for the full funnel.
- **Segment comparison:** Side-by-side bars or small multiples for `user_segment` (new, returning, VIP) showing funnel counts or conversion rates for the selected week. Surfaces whether a drop is global or segment-specific.

**Filters**

- **Week (or date range):** Aligns the dashboard to “weekly” tracking and lets the PM compare this week to last week or the same week last year.
- **User segment:** Isolates new vs returning vs VIP behavior; drop-offs often differ by segment (e.g., new users stall at cart).
- **Optional: device, region, campaign, or product category** if those dimensions exist in the warehouse—helps attribute a spike or dip to a specific slice.

**How this helps identify drop-offs**

The funnel visualization shows *where* volume leaves the funnel; stage-to-stage rates show *which transition* broke versus the prior week. Segment and weekly filters prevent mistaking a seasonal blip for a product issue and show whether fixes should target one cohort. The headline page-view-to-purchase trend answers whether overall funnel efficiency is improving while the team iterates.

---

## Question 2 — S3 Data Organization

**Layout**

- **Bucket prefix by environment and dataset**, e.g. `s3://company-analytics-prod/events/` (and `-dev` / `-staging` separately).
- **Hive-style partitioning** aligned to how you load and query:  
  `.../events/user_segment=<segment>/event_date=YYYY-MM-DD/`  
  or first by date then segment:  
  `.../events/event_date=YYYY-MM-DD/user_segment=<segment>/`.
- **File format:** Columnar **Parquet** (Snappy or Zstd compression) for the analytics path into Redshift; optional **JSON Lines** landing zone if raw ingestion must preserve exact payloads before normalization.

**Trade-offs**

- **Partitioning by `event_date` (daily):** **Query performance** is strong for Redshift COPY, Spectrum, or Athena—pruning skips irrelevant days. **Cost** stays predictable because you read fewer objects. Too many tiny files per day (if micro-batches are huge in count) can hurt listing and small-file overhead; **compaction** (e.g., hourly → daily rollups) balances that.
- **Adding `user_segment` under date:** Better for segment-scoped jobs (only scan one segment’s paths). **Cost** can rise slightly if many queries need full cross-segment scans (more list operations unless the catalog handles partition pruning well). Good when segment-level pipelines are common.
- **Wider partitions (e.g., month-only):** Fewer objects, lower S3 request cost and simpler listing; **worse** for incremental daily loads and for queries that only need a week—you scan extra data unless you use a columnar format with good row-group pruning.
- **Storage class / lifecycle:** Move old partitions to **Infrequent Access** or **Glacier** for **cost** savings on cold history; **trade-off** is higher latency and retrieval cost if analytics suddenly need deep history.

Overall: partition primarily by **event date** (daily), store **Parquet**, use a consistent key layout documented for the Redshift COPY manifest or Spectrum tables, and add secondary partition keys (like segment) only when query patterns justify the extra path complexity.
