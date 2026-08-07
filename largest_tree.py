from collections import defaultdict
from typing import Dict, List


def largestTree(immediateParent: Dict[int, int]) -> int:
    """
    Return the root id of the largest tree in the forest described by
    immediateParent (child -> parent). On a tie, return the smallest root id.
    """
    if not immediateParent:
        return 0

    children: Dict[int, List[int]] = defaultdict(list)
    nodes = set()

    for child, parent in immediateParent.items():
        children[parent].append(child)
        nodes.add(child)
        nodes.add(parent)

    # Roots are nodes that never appear as a child.
    roots = [n for n in nodes if n not in immediateParent]

    def subtree_size(root: int) -> int:
        size = 1
        stack = [root]
        while stack:
            node = stack.pop()
            for child in children[node]:
                size += 1
                stack.append(child)
        return size

    best_root = None
    best_size = -1
    for root in roots:
        size = subtree_size(root)
        if size > best_size or (size == best_size and (best_root is None or root < best_root)):
            best_size = size
            best_root = root

    return best_root


if __name__ == "__main__":
    assert largestTree({1: 2, 3: 4}) == 2
    assert largestTree({1: 2, 3: 4, 5: 4}) == 4  # sizes 2 vs 3
    assert largestTree({2: 1, 3: 1, 4: 2}) == 1
    print("ok")
