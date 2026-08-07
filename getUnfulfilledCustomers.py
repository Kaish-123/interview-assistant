#!/bin/python3

import os
from collections import defaultdict


def getUnfulfilledCustomers(requests, totalInventory):
    """
    Allocate inventory by highest bid first.
    Same bid -> round-robin one item at a time, earliest timestamp first.
    Return sorted customer IDs that received zero items.
    """
    if not requests:
        return []

    got_any = {req[0]: False for req in requests}

    bid_groups = defaultdict(list)
    for customer_id, quantity, bid_amount, timestamp in requests:
        bid_groups[bid_amount].append((timestamp, customer_id, quantity))

    for bid in sorted(bid_groups.keys(), reverse=True):
        if totalInventory <= 0:
            break

        # Earliest timestamp first; stable for equal timestamps
        group = sorted(bid_groups[bid])
        remaining = {cid: qty for _, cid, qty in group}
        order = [cid for _, cid, _ in group]

        while totalInventory > 0:
            active = [cid for cid in order if remaining[cid] > 0]
            if not active:
                break

            k = len(active)
            # Max full rounds we can give every active customer
            batches = min(min(remaining[cid] for cid in active), totalInventory // k)

            if batches > 0:
                for cid in active:
                    remaining[cid] -= batches
                    got_any[cid] = True
                totalInventory -= batches * k
                # Recalculate active (some may be finished)
                continue

            # Not enough for a full round: give 1 each in timestamp order
            for cid in active:
                if totalInventory <= 0:
                    break
                remaining[cid] -= 1
                got_any[cid] = True
                totalInventory -= 1
            break  # inventory exhausted after partial round

    return sorted(cid for cid, ok in got_any.items() if not ok)


if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')

    requests_rows = int(input().strip())
    requests_columns = int(input().strip())

    requests = []
    for _ in range(requests_rows):
        requests.append(list(map(int, input().rstrip().split())))

    totalInventory = int(input().strip())

    result = getUnfulfilledCustomers(requests, totalInventory)

    fptr.write('\n'.join(map(str, result)))
    fptr.write('\n')

    fptr.close()
