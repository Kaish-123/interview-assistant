# Idempotent Event Processor

Lambda receives EventBridge events and must process each unique `id` only once
within a TTL window (in-memory store shared across warm invocations).

## [REQUIRED] Your Tasks

1. Implement `processor/idempotency.py` (`is_duplicate`, `mark_seen`) with TTL
   expiry and thread safety.
2. Implement `processor/handler.py` (`lambda_handler`) to suppress duplicates
   and publish first-seen events via `publisher.py`.
3. Answer the written questions in `QUESTIONS.md`.

### Sample Inputs and Outputs

**First invocation**

```json
{
  "id": "evt-abc-123",
  "source": "com.arcflow.ingest",
  "detail-type": "DataRecordIngested",
  "detail": { "record_id": "R-99", "size_bytes": 4096 }
}
```

```json
{ "status": "processed", "event_id": "evt-abc-123" }
```

**Second invocation (same id within TTL)**

```json
{ "status": "duplicate", "event_id": "evt-abc-123" }
```

## Run

```bash
pip install -r requirements.txt
pytest tests/ -v
```
