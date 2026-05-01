def transform_events(raw_events):
    """
    Transforms a list of raw event dictionaries into a cleaned, deduplicated,
    and enriched list sorted by event_date ascending.

    Steps:
    - Exclude records missing user_id or event_type
    - Add date_partition field in "YYYY/MM/DD" format from event_date "YYYY-MM-DD"
    - Deduplicate on (user_id, event_type, event_date), keeping first occurrence
    - Return sorted by event_date ascending
    """
    seen = set()
    result = []

    for rec in raw_events:
        user_id = rec.get("user_id")
        event_type = rec.get("event_type")
        if user_id is None or event_type is None:
            continue

        event_date = rec.get("event_date")
        key = (user_id, event_type, event_date)
        if key in seen:
            continue
        seen.add(key)

        date_partition = event_date.replace("-", "/")

        result.append(
            {
                "user_id": user_id,
                "event_type": event_type,
                "event_date": event_date,
                "date_partition": date_partition,
            }
        )

    result.sort(key=lambda r: r["event_date"])
    return result
