"""
Test suite for the idempotent event processor.

Tests verify observable behaviour (return values, SNS call counts) without
revealing implementation details.
"""

import time
import threading
import pytest
from unittest.mock import patch

import processor.handler as handler_module
from processor.handler import lambda_handler
from processor.idempotency import IdempotencyStore


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

SAMPLE_EVENT = {
    "id": "evt-abc-123",
    "source": "com.arcflow.ingest",
    "detail-type": "DataRecordIngested",
    "detail": {"record_id": "R-99", "size_bytes": 4096},
}


def make_event(event_id: str) -> dict:
    return {**SAMPLE_EVENT, "id": event_id}


@pytest.fixture(autouse=True)
def reset_handler_store():
    """Give each test a fresh store so state cannot bleed between tests."""
    handler_module._store = IdempotencyStore(ttl_seconds=300)
    yield


# ---------------------------------------------------------------------------
# Handler - first-seen events
# ---------------------------------------------------------------------------

class TestHandlerFirstSeen:
    def test_returns_processed_status(self):
        with patch("processor.handler.publisher.publish_event"):
            result = lambda_handler(SAMPLE_EVENT)
        assert result["status"] == "processed"

    def test_returns_correct_event_id(self):
        with patch("processor.handler.publisher.publish_event"):
            result = lambda_handler(SAMPLE_EVENT)
        assert result["event_id"] == "evt-abc-123"

    def test_publishes_to_sns_exactly_once(self):
        with patch("processor.handler.publisher.publish_event") as mock_pub:
            lambda_handler(SAMPLE_EVENT)
        mock_pub.assert_called_once()


# ---------------------------------------------------------------------------
# Handler - duplicate events
# ---------------------------------------------------------------------------

class TestHandlerDuplicate:
    def test_returns_duplicate_status(self):
        with patch("processor.handler.publisher.publish_event"):
            lambda_handler(SAMPLE_EVENT)
            result = lambda_handler(SAMPLE_EVENT)
        assert result["status"] == "duplicate"

    def test_returns_correct_event_id_on_duplicate(self):
        with patch("processor.handler.publisher.publish_event"):
            lambda_handler(SAMPLE_EVENT)
            result = lambda_handler(SAMPLE_EVENT)
        assert result["event_id"] == "evt-abc-123"

    def test_does_not_publish_on_duplicate(self):
        with patch("processor.handler.publisher.publish_event") as mock_pub:
            lambda_handler(SAMPLE_EVENT)
            lambda_handler(SAMPLE_EVENT)
        assert mock_pub.call_count == 1

    def test_many_duplicates_publish_only_once(self):
        with patch("processor.handler.publisher.publish_event") as mock_pub:
            for _ in range(5):
                lambda_handler(SAMPLE_EVENT)
        assert mock_pub.call_count == 1


# ---------------------------------------------------------------------------
# Handler - distinct events
# ---------------------------------------------------------------------------

class TestHandlerDistinctEvents:
    def test_different_ids_both_processed(self):
        with patch("processor.handler.publisher.publish_event") as mock_pub:
            r1 = lambda_handler(make_event("evt-001"))
            r2 = lambda_handler(make_event("evt-002"))
        assert r1["status"] == "processed"
        assert r2["status"] == "processed"
        assert mock_pub.call_count == 2

    def test_duplicate_only_suppresses_matching_id(self):
        with patch("processor.handler.publisher.publish_event") as mock_pub:
            lambda_handler(make_event("evt-001"))
            lambda_handler(make_event("evt-001"))  # duplicate
            lambda_handler(make_event("evt-002"))  # different id - should publish
        assert mock_pub.call_count == 2


# ---------------------------------------------------------------------------
# IdempotencyStore - unit tests
# ---------------------------------------------------------------------------

class TestIdempotencyStore:
    def test_unseen_event_is_not_duplicate(self):
        store = IdempotencyStore(ttl_seconds=60)
        assert store.is_duplicate("evt-new") is False

    def test_seen_event_is_duplicate(self):
        store = IdempotencyStore(ttl_seconds=60)
        store.mark_seen("evt-1")
        assert store.is_duplicate("evt-1") is True

    def test_expired_entry_is_not_duplicate(self):
        store = IdempotencyStore(ttl_seconds=1)
        store.mark_seen("evt-expiring")
        time.sleep(1.1)
        assert store.is_duplicate("evt-expiring") is False

    def test_re_marking_after_expiry_is_treated_as_new(self):
        store = IdempotencyStore(ttl_seconds=1)
        store.mark_seen("evt-expiring")
        time.sleep(1.1)
        store.mark_seen("evt-expiring")
        assert store.is_duplicate("evt-expiring") is True

    def test_different_ids_tracked_independently(self):
        store = IdempotencyStore(ttl_seconds=60)
        store.mark_seen("evt-A")
        assert store.is_duplicate("evt-A") is True
        assert store.is_duplicate("evt-B") is False


# ---------------------------------------------------------------------------
# Concurrency - handler processes each unique id exactly once
# ---------------------------------------------------------------------------

class TestConcurrency:
    def test_concurrent_calls_with_same_id_process_exactly_once(self):
        processed = []
        duplicates = []

        def invoke():
            with patch("processor.handler.publisher.publish_event"):
                result = lambda_handler(make_event("evt-concurrent"))
                if result["status"] == "processed":
                    processed.append(1)
                else:
                    duplicates.append(1)

        threads = [threading.Thread(target=invoke) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(processed) == 1
        assert len(duplicates) == 19
