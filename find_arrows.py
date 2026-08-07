import math


def string_to_square_block(s):
    size = int(math.sqrt(len(s)))
    block = [['' for _ in range(size)] for _ in range(size)]
    index = 0
    for i in range(size):
        for j in range(size):
            block[i][j] = s[index]
            index += 1
    return block


def find_arrows_up_right(block):
    """
    Find all arrows pointing up to the right in the block.

    An arrow is an isosceles right triangle with:
      - the same letter on all three corners
      - the 90-degree corner at the top-right
      - any size (side length >= 1)

    For right-angle at (r, c) and side length L:
      top-left:     (r,     c - L)
      top-right:    (r,     c)      <-- 90-degree corner
      bottom-right: (r + L, c)
    """
    n = len(block)
    arrows = []

    for r in range(n):
        for c in range(n):
            # L is the side length in steps; must fit left and down
            max_L = min(c, n - 1 - r)
            for L in range(1, max_L + 1):
                letter = block[r][c]
                top_left = block[r][c - L]
                bottom_right = block[r + L][c]
                if letter == top_left == bottom_right:
                    arrows.append({
                        'letter': letter,
                        'size': L,
                        'top_left': (r, c - L),
                        'top_right': (r, c),
                        'bottom_right': (r + L, c),
                    })

    return arrows


if __name__ == "__main__":
    input_string = "ABDBAAACCFBAEBCDABAFDCEEA"
    square_block = string_to_square_block(input_string)

    print("Block:")
    for row in square_block:
        print(' '.join(row))

    arrows = find_arrows_up_right(square_block)

    print(f"\nFound {len(arrows)} arrow(s) pointing up to the right:\n")
    for i, arrow in enumerate(arrows, 1):
        print(
            f"{i}. Letter '{arrow['letter']}' "
            f"(size {arrow['size']}) — "
            f"corners: TL{arrow['top_left']}, "
            f"TR{arrow['top_right']} (90°), "
            f"BR{arrow['bottom_right']}"
        )
