import heapq
from collections import deque


def data_structure(trace):
    """
    Returns:
        A set containing zero or more of the strings "stack",
        "queue", or "priority", indicating which data structures
        the trace can represent
    """
    result = set()
    if _matches_stack(trace):
        result.add("stack")
    if _matches_queue(trace):
        result.add("queue")
    if _matches_priority(trace):
        result.add("priority")
    return result


def _matches_stack(trace):
    stack = []
    for op, value in trace:
        if op == "insert":
            stack.append(value)
        elif op == "pop":
            if not stack or stack[-1] != value:
                return False
            stack.pop()
        else:
            return False
    return True


def _matches_queue(trace):
    queue = deque()
    for op, value in trace:
        if op == "insert":
            queue.append(value)
        elif op == "pop":
            if not queue or queue[0] != value:
                return False
            queue.popleft()
        else:
            return False
    return True


def _matches_priority(trace):
    # Min-priority queue: always pop the smallest current value.
    heap = []
    for op, value in trace:
        if op == "insert":
            heapq.heappush(heap, value)
        elif op == "pop":
            if not heap or heap[0] != value:
                return False
            heapq.heappop(heap)
        else:
            return False
    return True


def run_tests():
    """ You should implement some tests here. """
    trace = [("insert", 5), ("insert", 10), ("pop", 5)]
    assert data_structure(trace) == {"queue", "priority"}
    assert data_structure([]) == {"stack", "queue", "priority"}
    assert data_structure([("pop", 5)]) == set()
    assert data_structure([("insert", 5), ("pop", 5), ("insert", 0), ("pop", 0)]) == {
        "stack",
        "queue",
        "priority",
    }

    # Stack only: LIFO pop of most recent (not min, not oldest)
    assert data_structure([("insert", 1), ("insert", 2), ("pop", 2)]) == {"stack"}

    # Queue only (not stack, not min-priority): pop oldest when it is not min
    assert data_structure(
        [("insert", 2), ("insert", 1), ("pop", 2)]
    ) == {"queue"}

    # Stack only: pop newest when it is not min and not oldest
    assert data_structure(
        [("insert", 1), ("insert", 3), ("insert", 2), ("pop", 2)]
    ) == {"stack"}

    # Priority only: pop min that is neither newest nor oldest
    assert data_structure(
        [("insert", 3), ("insert", 1), ("insert", 2), ("pop", 1)]
    ) == {"priority"}

    # All three when ops force the same sequence
    assert data_structure(
        [("insert", 1), ("insert", 2), ("pop", 1), ("pop", 2)]
    ) == {"queue", "priority"}

    # Pure stack sequence
    assert data_structure(
        [("insert", 1), ("insert", 2), ("pop", 2), ("pop", 1)]
    ) == {"stack"}

    # Duplicate values
    assert data_structure(
        [("insert", 5), ("insert", 5), ("pop", 5), ("pop", 5)]
    ) == {"stack", "queue", "priority"}

    # Pop wrong value after one insert
    assert data_structure([("insert", 1), ("pop", 2)]) == set()

    # Interleaved ops that stay consistent for all
    assert data_structure(
        [
            ("insert", 7),
            ("pop", 7),
            ("insert", 3),
            ("insert", 4),
            ("pop", 3),
            ("pop", 4),
        ]
    ) == {"queue", "priority"}

    # Empty after pops then invalid pop
    assert data_structure(
        [("insert", 1), ("pop", 1), ("pop", 1)]
    ) == set()

    # Single insert, no pop — still valid for all (structure non-empty is fine)
    assert data_structure([("insert", 42)]) == {
        "stack",
        "queue",
        "priority",
    }

    # Negative and zero values with priority
    assert data_structure(
        [("insert", 0), ("insert", -5), ("pop", -5)]
    ) == {"stack", "priority"}

    print("Success!")


if __name__ == "__main__":
    run_tests()
