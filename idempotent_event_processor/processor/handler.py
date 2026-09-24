import threading
from processor.idempotency import IdempotencyStore
from processor import publisher

_store = IdempotencyStore(ttl_seconds=300)
_handler_lock = threading.Lock()


def lambda_handler(event: dict, context=None) -> dict:
    event_id = event['id']
    with _handler_lock:
        if _store.is_duplicate(event_id):
            return {"status": "duplicate", "event_id": event_id}

        _store.mark_seen(event_id)

    publisher.publish_event(event_id, event['detail'])
    return {"status": "processed", "event_id": event_id}
