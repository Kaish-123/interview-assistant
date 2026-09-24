# Idempotent Event Processor — Written Answers

## Question 1 – EventBridge

```yaml
ProcessorRule:
  Type: AWS::Events::Rule
  Properties:
    EventBusName: !Ref DomainEventBus
    EventPattern:
      detail-type:
        - "DataRecordIngested"
    Targets:
      - Arn: !GetAtt ProcessorFunction.Arn
        Id: "ProcessorTarget"
        RetryPolicy:
          MaximumRetryAttempts: 3
```

Your in-memory idempotency store resets on each cold start. Under what
conditions can EventBridge's retry behaviour still cause duplicate processing
even with the store in place, and what architectural change would eliminate
this class of duplication entirely?

### Answer

**When duplicates can still happen**

EventBridge retries the *same* event (same `id`) when the Lambda invocation
fails, times out, or is throttled — up to `MaximumRetryAttempts: 3`. The
in-memory store only survives while that particular Lambda *container* stays
warm. Duplicate processing still occurs when:

1. The first attempt published to SNS (or partially completed), then the
   invocation failed / timed out afterward → EventBridge retries.
2. The retry lands on a **new cold-started container** (scale-out, recycling,
   or the previous container already gone) → empty store → the event is treated
   as first-seen again → SNS publish happens a second time.
3. Two containers are warm at once (concurrency > 1) and each processes the
   same retry / duplicate delivery independently — memory is not shared across
   containers.

So retries + cold starts (or multi-container concurrency) defeat an in-memory
guard even though the EventBridge `id` is stable.

**Architectural fix that eliminates this class of duplication**

Move the idempotency record to a **durable, shared store** keyed by EventBridge
`id` (or a business key), with a TTL attribute — typically **DynamoDB** with a
conditional `PutItem` (`attribute_not_exists(pk)`), or DynamoDB + Powertools
Idempotency, or similar. Every container, cold or warm, consults the same
table before publishing. Optionally combine with:

- Marking “in progress / completed” before side effects, and
- Making the SNS publish itself idempotent (deduplication id on FIFO topics),

so retries after a crash cannot double-publish.

---

## Question 2 – SNS / SQS

The SNS topic receiving processed events has three SQS subscribers consuming
at different throughput rates. During a traffic spike, one subscriber's queue
backs up significantly while others remain healthy.

What SNS and SQS configuration options would you evaluate to prevent the slow
subscriber from affecting the overall pipeline, and what are the visibility
trade-offs of each option?

### Answer

SNS fan-out already delivers independently per subscription, so a backed-up
SQS queue does **not** block delivery to the other queues. The risk is usually
**message retention / loss on the slow path**, **cost**, and **cross-cutting
limits** — not the healthy subscribers being starved by SNS.

Options to evaluate:

1. **Per-subscription SQS tuning for the slow consumer**
   - Raise `VisibilityTimeout` to match processing time (avoid poison requeues).
   - Raise consumer concurrency / scale the worker fleet.
   - Optionally raise `MaximumMessageSize` / batch size only if helpful.
   - **Trade-off:** Isolates impact to that subscriber; backlog remains visible
     via `ApproximateNumberOfMessages`; no change to other subscribers.

2. **SQS redrive policy (DLQ) + maxReceiveCount**
   - Failed / repeatedly unprocessed messages leave the main queue for a DLQ.
   - **Trade-off:** Protects the main queue from poison messages and keeps
     processing moving; you lose “all messages still on the primary queue”
     visibility unless you monitor the DLQ separately.

3. **SNS subscription filter policies**
   - Send only relevant message subsets to the slow subscriber so its volume
     drops.
   - **Trade-off:** Better isolation and less backlog; reduced visibility of
     the full event stream for that consumer (by design).

4. **Raw message delivery / separate topics per consumer tier**
   - Split hot vs cold consumers onto different topics or accounts.
   - **Trade-off:** Strong isolation and independent quotas; more infra and
     harder to see one unified fan-out topology.

5. **SNS delivery / retry policy and SQS encryption / IAM (usually secondary)**
   - SNS→SQS retries are per subscription; healthy subscriptions keep receiving.
   - Confirm the slow queue’s retention period (`MessageRetentionPeriod`, up to
     14 days) is long enough for catch-up so spike traffic is not dropped.
   - **Trade-off:** Longer retention improves durability visibility of the
     backlog but increases storage cost; shorter retention can silently drop
     messages after expiry.

**Bottom line:** Prefer isolating the slow path with its own SQS scaling, DLQ,
filters, and retention — do not couple healthy consumers to the slow one’s
throughput. Monitor each queue’s depth and age independently (CloudWatch) so
backlog on one subscription does not hide failures or look like a pipeline-wide
outage.
