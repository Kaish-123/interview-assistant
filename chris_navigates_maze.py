#!/usr/bin/env python3
"""
Chris Navigates a Maze

Chris starts at (0, 0), must collect every gold coin (cell value 2),
and then reach Alex at (x, y). Moves are 4-directional through
unblocked cells (0 or 2). Blocked cells are 1.

Returns the shortest path length, or -1 if impossible.
"""

from collections import deque


def minMoves(maze, x, y):
    if not maze or not maze[0]:
        return -1

    rows = len(maze)
    cols = len(maze[0])

    if not (0 <= x < rows and 0 <= y < cols):
        return -1
    if maze[0][0] == 1 or maze[x][y] == 1:
        return -1

    coins = {}
    coin_index = 0
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 2:
                coins[(r, c)] = coin_index
                coin_index += 1

    all_mask = (1 << coin_index) - 1
    start_mask = 0
    if (0, 0) in coins:
        start_mask = 1 << coins[(0, 0)]

    if x == 0 and y == 0 and start_mask == all_mask:
        return 0

    visited = [[0] * cols for _ in range(rows)]
    visited[0][0] = 1 << start_mask

    queue = deque([(0, 0, start_mask, 0)])
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    while queue:
        r, c, mask, dist = queue.popleft()
        for dr, dc in directions:
            nr = r + dr
            nc = c + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            if maze[nr][nc] == 1:
                continue

            next_mask = mask
            coin_bit = coins.get((nr, nc))
            if coin_bit is not None:
                next_mask |= 1 << coin_bit

            bit = 1 << next_mask
            if visited[nr][nc] & bit:
                continue
            visited[nr][nc] |= bit

            next_dist = dist + 1
            if nr == x and nc == y and next_mask == all_mask:
                return next_dist
            queue.append((nr, nc, next_mask, next_dist))

    return -1


if __name__ == "__main__":
    import os

    fptr = open(os.environ["OUTPUT_PATH"], "w")

    maze_rows = int(input().strip())
    maze_columns = int(input().strip())

    maze = []
    for _ in range(maze_rows):
        maze.append(list(map(int, input().rstrip().split())))

    x = int(input().strip())
    y = int(input().strip())

    result = minMoves(maze, x, y)
    fptr.write(str(result) + "\n")
    fptr.close()
