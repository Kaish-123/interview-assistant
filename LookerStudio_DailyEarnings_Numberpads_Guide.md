# 3 Scorecards: Yesterday / Today / Tomorrow Earnings (10 AM–8 AM IST)

**Day rule:** One “day” = **10:00 AM IST** to **7:59 AM IST next day** (8 AM = start of next day).

---

## Before you start

1. **Set timezone:** **File** → **Report settings** → set **Timezone** to **Asia/Kolkata**.
2. Your data source must be **CallCalendarSheet** with fields **Start Time** (date & time) and **Earnings** (number).  
   If your date column has another name, you’ll use that name in the formulas below.

---

## Part 1: Create 3 calculated fields

**Where:** Right-hand **Data** panel → under your **CallCalendarSheet** data source → click **+ Add a field**.

Create these three fields one by one.

---

### Field 1: Report Custom Today

| What to set | Value |
|-------------|--------|
| **Name** | `Report Custom Today` |
| **Data type** | Date & Time |
| **Formula** | Copy-paste exactly below |

**Formula (copy everything below):**

```
CASE
  WHEN HOUR(CURRENT_DATETIME("Asia/Kolkata")) < 8 THEN DATETIME_SUB(DATETIME_TRUNC(CURRENT_DATETIME("Asia/Kolkata"), DAY), INTERVAL 1 DAY)
  ELSE DATETIME_TRUNC(CURRENT_DATETIME("Asia/Kolkata"), DAY)
END
```

Click **Save**.

---

### Field 2: Custom Day

| What to set | Value |
|-------------|--------|
| **Name** | `Custom Day` |
| **Data type** | Date & Time |
| **Formula** | Copy-paste below (if your date column is not "Start Time", replace `Start Time` with its exact name) |

**Formula (copy everything below):**

```
CASE
  WHEN HOUR(Start Time) < 8 THEN DATETIME_SUB(DATETIME_TRUNC(Start Time, DAY), INTERVAL 1 DAY)
  ELSE DATETIME_TRUNC(Start Time, DAY)
END
```

Click **Save**.

---

### Field 3: Earning Day Bucket

| What to set | Value |
|-------------|--------|
| **Name** | `Earning Day Bucket` |
| **Data type** | Text |
| **Formula** | Copy-paste below |

**Formula (copy everything below):**

```
CASE
  WHEN Custom Day = DATETIME_SUB(Report Custom Today, INTERVAL 1 DAY) THEN "Yesterday"
  WHEN Custom Day = Report Custom Today THEN "Today"
  WHEN Custom Day = DATETIME_ADD(Report Custom Today, INTERVAL 1 DAY) THEN "Tomorrow"
  ELSE "Other"
END
```

Click **Save**.

---

## Part 2: Create the 3 scorecards

**Where:** Top menu **Add a chart** → **Scorecard**. Add **three** scorecards (you can duplicate one scorecard twice to save time).

For **each** scorecard:

1. Select the scorecard on the canvas.
2. In the **Data** panel (right side):
   - **Metric:** choose **Earnings** → set aggregation to **Sum** (or use existing “Sum of Earnings” if you have it).
   - **Filter:** add a chart filter so only the right “day” is included (see table below).
3. In **Style** (or **Setup**): set the **Title** as in the table.

| # | Scorecard title | Filter to add |
|---|-----------------|---------------|
| 1 | **Yesterday's earnings** | Include: **Earning Day Bucket** → equals → **Yesterday** |
| 2 | **Today's earnings** | Include: **Earning Day Bucket** → equals → **Today** |
| 3 | **Tomorrow's scheduled earnings** | Include: **Earning Day Bucket** → equals → **Tomorrow** |

---

### How to add the filter on each scorecard

1. With the scorecard selected, in the **Data** panel find **Filter** (or “Chart filter” / filter icon).
2. Click **Add a filter** (or **+**).
3. **Create filter:** e.g. name it “Yesterday only”.
4. In the filter definition:
   - **Include** → **Earning Day Bucket** → **equals** → type **Yesterday** (exact text, no extra spaces).
5. Click **Save** and assign this filter to the scorecard.

Repeat for the second scorecard with **Today**, and the third with **Tomorrow**.

---

## Quick checklist

- [ ] Report timezone = **Asia/Kolkata**
- [ ] Created field **Report Custom Today** (Date & Time) with the first formula
- [ ] Created field **Custom Day** (Date & Time) with the second formula (and correct **Start Time** name if different)
- [ ] Created field **Earning Day Bucket** (Text) with the third formula
- [ ] Scorecard 1: Metric = Sum(Earnings), Filter = Earning Day Bucket = **Yesterday**, Title = Yesterday's earnings
- [ ] Scorecard 2: Metric = Sum(Earnings), Filter = Earning Day Bucket = **Today**, Title = Today's earnings
- [ ] Scorecard 3: Metric = Sum(Earnings), Filter = Earning Day Bucket = **Tomorrow**, Title = Tomorrow's scheduled earnings

---

## If something goes wrong

- **All scorecards show 0:** Check that **Start Time** and **Earnings** names in the Data panel match what you used. Set report/data timezone to **Asia/Kolkata**. Add a table with columns **Custom Day** and **Earning Day Bucket** to confirm they show values and Yesterday/Today/Tomorrow.
- **Formula error “Unknown field”:** Your date column may be named differently (e.g. “Start Time ” or “1/31/2024 14:00:00”). In the **Custom Day** formula, replace `Start Time` with that exact name from the Data panel.
- **Wrong numbers:** Ensure **Start Time** is stored or interpreted in IST (data source timezone **Asia/Kolkata** if available).

Done. The three numberpads will update automatically whenever the report is opened or refreshed, using your 10 AM–8 AM IST day.

---

# Table: Earnings by day for selected month (same 10 AM–8 AM IST day)

This table shows **earnings for each custom day** (10 AM IST to 8 AM IST next day) in the **current month by default**, with an option to **change the month** so you can see any month’s daily earnings.

**You must have already created the field `Custom Day`** (Part 1, Field 2 above). No new formulas are required if you have that.

---

## Step 1: Set the report date dimension and default range

1. Go to **File** → **Report settings** (or **Resource** → **Report settings**).
2. Find **Date range** (or **Default date range**).
3. Set **Date dimension** to **Custom Day** (use the dropdown and pick your calculated field **Custom Day**).
4. Set **Default date range** to **This month** (so the report opens with the current month).
5. Save/close settings.

This makes the whole report filter by **Custom Day** when a date range is applied, and default to current month.

---

## Step 2: Add a date range control (month selector)

1. **Add a chart** (or **Insert** menu) → **Controls** → **Date range control**.
2. Place it above or beside where you want the table (e.g. top of the page).
3. With the control selected, open the **Setup** or **Data** panel.
4. Set **Date dimension** to **Custom Day** (same as report).
5. In **Default date range**, choose **This month** (or keep “Same as report” if you set it in Step 1).
6. Optional: In **Style**, give it a label like “Select month” or “Month”.

Users will use this control to change the month (or pick a custom range); the table will show only days in that range.

---

## Step 3: Add the table

1. **Add a chart** → **Table**.
2. Place it below the date range control.
3. With the table selected, in the **Data** panel set:

| What to set | Value |
|-------------|--------|
| **Dimension** | **Custom Day** (this is each “day” in 10 AM–8 AM IST) |
| **Metric** | **Earnings** with aggregation **Sum** |

4. Optional: Add a second metric (e.g. **Record count** or **Event ID** → Count) to show number of events per day.
5. In **Style** (or **Setup**):
   - Set **Title** to e.g. “Earnings by day (10 AM–8 AM IST)”.
   - Format **Custom Day** as you like (e.g. “Feb 15, 2026” or “15 Feb”): click the dimension in the table setup and choose **Date** format.

The table will automatically respect the report date range (and the date range control), so only days in the selected month (or range) appear.

---

## Step 4: Make sure the table uses the report date range

1. Select the **table**.
2. In the **Data** panel, look for **Date range** or **Filter by date range**.
3. Ensure the table uses the **report date range** (e.g. “Use report date range” or the same **Custom Day** dimension). If you see a dropdown for which date range/dimension the chart uses, set it to **Custom Day** so it matches the control.

If the table doesn’t update when you change the control, the table may be using a different date dimension—set it to **Custom Day** and “Use report date range” (or equivalent).

---

## Quick checklist (table)

- [ ] Report date dimension = **Custom Day**, default range = **This month**
- [ ] **Date range control** added; date dimension = **Custom Day**; default = This month
- [ ] **Table** added with dimension **Custom Day**, metric **Sum(Earnings)**
- [ ] Table uses report date range / **Custom Day** so changing the control updates the table

---

## How to use it

- **By default:** Report opens with **This month**; table shows one row per custom day in the current month and total earnings for that day.
- **Change month:** Use the date range control: choose “Last month”, “Last 30 days”, or **Custom range** and pick the first and last day of the month you want (e.g. 1 Feb 2026 to 28 Feb 2026). The table will show earnings for each day in that month, with “day” still meaning 10 AM IST to 8 AM IST next day.

---

# Make the page / canvas longer (more content area)

To get a **longer page** (taller canvas) so you can add more content:

1. **Edit mode:** Make sure the report is in **Edit** mode (pencil icon or **Edit** button).
2. **Open Layout:** Click on a **blank area** of the canvas (not on any chart, scorecard, or control). In the **right-hand panel**, open the **Layout** tab (or use **Theme and layout** in the toolbar).
3. **Canvas size:** Find **Canvas size** (under report layout / page).
4. **Set custom size:** Choose **Custom** (or "Custom size") and set:
   - **Width:** e.g. keep as is (e.g. 1200) or set up to **2000** px.
   - **Height:** increase to the length you want, e.g. **2000**, **3000**, or up to **10,000** px (max). Example: **1200 × 3000** gives a much longer scrollable page.
5. **Apply:** The canvas updates; you can scroll down and place more components.

**Per-page size (optional):** To change only the current page: **Page** → **Current page settings** → right panel **Style** → **Canvas size**. Set a custom height for that page (default is "Auto" = uses report layout).

**Limits:** Min 10×10 px; max **2000 px wide × 10,000 px high**.
