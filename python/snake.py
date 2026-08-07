from point import Point
import random


class SnakeGame:
  def __init__(self, rows, cols, initial_snake, initial_direction):
    """
    Initialize the Snake Game.

    Args:
    - rows (int): Number of rows on the board.
    - cols (int): Number of columns on the board.
    - initial_snake (list of Point): Initial snake positions (tail first, head last).
    - initial_direction (int): Initial direction (0=up, 1=right, 2=down, 3=left).
    """
    if not isinstance(rows, int) or not isinstance(cols, int):
      raise TypeError("rows and cols must be integers")
    if rows <= 0 or cols <= 0:
      raise ValueError("rows and cols must be positive")

    if not isinstance(initial_snake, list):
      raise TypeError(
        "initial_snake must be a list of Point objects, got {}".format(type(initial_snake).__name__)
      )
    if len(initial_snake) == 0:
      raise ValueError("initial_snake cannot be empty")

    for i, segment in enumerate(initial_snake):
      if not isinstance(segment, Point):
        raise TypeError(
          "initial_snake[{}] must be a Point, got {}".format(i, type(segment).__name__)
        )

    if not isinstance(initial_direction, int) or initial_direction not in (0, 1, 2, 3):
      raise ValueError("initial_direction must be an integer from 0 to 3")

    self.rows = rows
    self.cols = cols
    self.snake = list(initial_snake)
    self.direction = initial_direction
    self.score = 0

    for i, segment in enumerate(self.snake):
      if not (0 <= segment.row < self.rows and 0 <= segment.col < self.cols):
        raise ValueError(
          "initial_snake[{}] at ({}, {}) is outside the board".format(
            i, segment.row, segment.col
          )
        )

    self.apple = self.generate_apple()

  def generate_apple(self):
    """Generate a new apple position randomly on the board."""
    occupied = set(self.snake)
    while True:
      apple = Point(
        random.randint(0, self.rows - 1),
        random.randint(0, self.cols - 1),
      )
      if apple not in occupied:
        return apple

  def input(self, command):
    """
    Change the direction of the snake based on user input.

    Args:
    - command (int): New direction command (0=up, 1=right, 2=down, 3=left).
    """
    if not isinstance(command, int) or command not in (0, 1, 2, 3):
      return

    # Ignore opposite direction
    if abs(command - self.direction) == 2:
      return

    self.direction = command

  def tick(self):
    """
    Update the game state by moving the snake in the current direction.

    Returns:
    - bool: True if game continues, False if game over.
    """
    head = self.snake[-1]

    if self.direction == 0:  # Up
      new_head = Point(head.row - 1, head.col)
    elif self.direction == 1:  # Right
      new_head = Point(head.row, head.col + 1)
    elif self.direction == 2:  # Down
      new_head = Point(head.row + 1, head.col)
    else:  # Left
      new_head = Point(head.row, head.col - 1)

    if (
      new_head.row < 0
      or new_head.row >= self.rows
      or new_head.col < 0
      or new_head.col >= self.cols
    ):
      return False

    ate_apple = new_head == self.apple
    body = self.snake if ate_apple else self.snake[:-1]
    if new_head in body:
      return False

    self.snake.append(new_head)

    if ate_apple:
      self.score += 1
      self.apple = self.generate_apple()
    else:
      self.snake.pop(0)

    return True
