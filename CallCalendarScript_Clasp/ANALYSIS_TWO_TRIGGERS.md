# Analysis: Two Trigger Entry Points in Your Wrapper

You have **two** functions that run on **Calendar – Changed**. Both live in (or next to) your wrapper. Here’s what each does and which one is “working fine.”

---

## 1. The two triggers (what runs when calendar changes)

| Trigger function | Event | Error rate (from your Triggers page) |
|------------------|--------|--------------------------------------|
| **syncCalendarAndCalculateEarnings** | Calendar – Changed | **0%** |
| **syncAndPrice_Rolling** | Calendar – Changed | 1.87% |

So when a calendar change happens, **both** run (one after the other). The one that’s “working fine” (no errors) is **syncCalendarAndCalculateEarnings**.

---

## 2. What each path does

### Path A: `syncCalendarAndCalculateEarnings()` (0% errors — **this one is working fine**)

**Flow:**

1. **fetchCalendarEventsIL_Optimized()**  
   - Syncs calendar → sheet (add/update events).  
   - Implemented in another file (e.g. `CalendarILOpt.gs` or `New_CalendarIncrementalLoad.gs`).

2. **calculateEarningsIL_Optimized()**  
   - Reads **CallCalendarSheet** and **KeywordMapping**.  
   - Date range: **Jan 1, 2024 – Mar 1, 2026** (fixed).  
   - For each row: if in range, not manual, and **earnings empty** → match title to keywords and set earnings (default 10000).  
   - Writes **only** the rows it processed (full row A–F).  
   - **Skips** rows that already have earnings.

**Characteristics:**

- Fixed date window (2024–2026).  
- Only fills **empty** earnings; does not overwrite existing.  
- Manual-update logic: skip if manual = “yes”.  
- One keyword match per title (first match wins).  
- No row deletion (does not remove events that left the calendar window).

---

### Path B: `syncAndPrice_Rolling()` (1.87% errors)

**Flow (all in one place, CALSYNC namespace):**

1. **syncWindow_()**  
   - Rolling window: **today − 400 days** to **today + 365 days**.  
   - Fetches calendar events in that window.  
   - **Adds** new events, **updates** existing (ID, Title, Start, End).  
   - **Deletes** sheet rows for events that are **no longer** in the window (event removed or moved out).

2. **loadKeywordMap_()**  
   - Same idea: KeywordMapping → keyword → price.

3. **recalcEarningsForWindow_()**  
   - Only rows whose **Start time** is in the rolling window.  
   - Respects Manual Update (yes/y/true/1).  
   - **Overwrites** earnings for non-manual rows (even if already filled).  
   - Default price 10000; first keyword match wins.

**Characteristics:**

- Rolling window (always “last 400 days + next 365 days”).  
- **Deletes** rows when events leave the window.  
- **Recomputes** earnings every run for all non-manual rows in window.  
- Namespaced (CALSYNC), no global name clashes.  
- Slightly more complex (sync + delete + price in one flow).

---

## 3. Side-by-side comparison

| Aspect | syncCalendarAndCalculateEarnings (Path A) | syncAndPrice_Rolling (Path B) |
|--------|------------------------------------------|-------------------------------|
| **Error rate** | **0%** | 1.87% |
| **Calendar sync** | fetchCalendarEventsIL_Optimized (incremental add/update) | syncWindow_ (add/update + delete out-of-window) |
| **Date range** | Fixed: 2024–2026 | Rolling: today ± 400/365 days |
| **Earnings** | Only **empty** cells | **Overwrites** all non-manual in window |
| **Row deletion** | No | Yes (events out of window) |
| **Manual update** | yes | yes/y/true/1 |
| **Default price** | 10000 | 10000 |
| **Where logic lives** | Wrapper + other .gs files | Same file (CALSYNC) |

---

## 4. Which one is “working fine” and why

- **syncCalendarAndCalculateEarnings** has **0% errors** and is the one that’s “working fine” in practice.  
- **syncAndPrice_Rolling** has **1.87% errors** — so occasionally it fails (e.g. quota, time, or data edge cases).

Both run on the same event, so:

- Path A runs first (or second), syncs with `fetchCalendarEventsIL_Optimized`, then fills empty earnings with `calculateEarningsIL_Optimized`.  
- Path B then runs and can **overwrite** those earnings (and delete rows) because it recalculates all non-manual rows in its rolling window and removes out-of-window events.

So the “working fine” behavior you see (correct earnings, no errors) is coming from **Path A**. Path B can still change the sheet (overwrite earnings, delete rows) and sometimes errors.

---

## 5. Recommendation for enhancements

- **Treat Path A as the main, working path:**  
  - **syncCalendarAndCalculateEarnings** → **fetchCalendarEventsIL_Optimized** → **calculateEarningsIL_Optimized**.  
- **Do enhancements there** (e.g. new keyword rules, date range, or “only update certain rows”) so you don’t depend on the path that has 1.87% errors.  
- **Optional:** If you don’t need rolling window + delete + overwrite behavior, you could **disable or remove** the **syncAndPrice_Rolling** trigger later to avoid duplicate work and those errors.  
- **Keep trigger names unchanged** so existing triggers keep firing; only change the **implementation** inside the functions if needed.

---

## 6. Summary

| Question | Answer |
|----------|--------|
| Which trigger is “working fine”? | **syncCalendarAndCalculateEarnings** (0% errors). |
| What does it run? | **fetchCalendarEventsIL_Optimized** (sync) then **calculateEarningsIL_Optimized** (earnings for empty cells in 2024–2026). |
| What about the other one? | **syncAndPrice_Rolling** (1.87% errors) does rolling sync + delete + full earnings recalc; can overwrite what Path A wrote. |
| Where to add enhancements? | In the **Path A** flow (e.g. `calculateEarningsIL_Optimized` or the sync function), and keep triggers as they are. |

When you’re ready, share the **requirement** (e.g. “only update earnings for X” or “new keyword rule”) and we can implement it in Path A without touching the trigger names.
