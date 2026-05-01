from events import transform_events


def test_basic_transformation():
    raw = [
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": "U2", "event_type": "purchase", "event_date": "2024-03-09"},
    ]
    result = transform_events(raw)
    assert len(result) == 2
    assert result[0]["user_id"] == "U2"
    assert result[1]["user_id"] == "U1"


def test_excludes_missing_user_id():
    raw = [
        {"user_id": None, "event_type": "add_to_cart", "event_date": "2024-03-10"},
        {"event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
    ]
    result = transform_events(raw)
    assert len(result) == 1
    assert result[0]["user_id"] == "U1"


def test_excludes_missing_event_type():
    raw = [
        {"user_id": "U1", "event_type": None, "event_date": "2024-03-10"},
        {"user_id": "U2", "event_date": "2024-03-10"},
        {"user_id": "U3", "event_type": "checkout", "event_date": "2024-03-10"},
    ]
    result = transform_events(raw)
    assert len(result) == 1
    assert result[0]["user_id"] == "U3"


def test_date_partition_added():
    raw = [
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
    ]
    result = transform_events(raw)
    assert result[0]["date_partition"] == "2024/03/10"


def test_date_partition_format():
    raw = [
        {"user_id": "U1", "event_type": "purchase", "event_date": "2024-01-05"},
    ]
    result = transform_events(raw)
    assert result[0]["date_partition"] == "2024/01/05"


def test_deduplication_keeps_first_occurrence():
    raw = [
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
    ]
    result = transform_events(raw)
    assert len(result) == 1


def test_deduplication_different_event_types_kept():
    raw = [
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": "U1", "event_type": "add_to_cart", "event_date": "2024-03-10"},
    ]
    result = transform_events(raw)
    assert len(result) == 2


def test_deduplication_different_dates_kept():
    raw = [
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-11"},
    ]
    result = transform_events(raw)
    assert len(result) == 2


def test_sorted_by_event_date_ascending():
    raw = [
        {"user_id": "U3", "event_type": "purchase", "event_date": "2024-03-12"},
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": "U2", "event_type": "checkout", "event_date": "2024-03-11"},
    ]
    result = transform_events(raw)
    dates = [r["event_date"] for r in result]
    assert dates == sorted(dates)


def test_readme_example():
    raw = [
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": None, "event_type": "add_to_cart", "event_date": "2024-03-10"},
        {"user_id": "U1", "event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": "U2", "event_type": "purchase", "event_date": "2024-03-09"},
    ]
    result = transform_events(raw)
    assert len(result) == 2
    assert result[0] == {
        "user_id": "U2",
        "event_type": "purchase",
        "event_date": "2024-03-09",
        "date_partition": "2024/03/09",
    }
    assert result[1] == {
        "user_id": "U1",
        "event_type": "page_view",
        "event_date": "2024-03-10",
        "date_partition": "2024/03/10",
    }


def test_empty_input():
    assert transform_events([]) == []


def test_all_invalid_records():
    raw = [
        {"user_id": None, "event_type": "page_view", "event_date": "2024-03-10"},
        {"user_id": "U1", "event_type": None, "event_date": "2024-03-10"},
    ]
    assert transform_events(raw) == []
