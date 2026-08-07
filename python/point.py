class Point:
    """
    Helper class that abstracts away x and y into rows and cols
    """
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __eq__(self, other):
        if type(other) is type(self):
            return self.row == other.row and self.col == other.col
        else:
            return False

    def __repr__(self):
        return '(row: {}, col: {})'.format(self.row, self.col)

    def __str__(self):
        return '(row: {}, col: {})'.format(self.row, self.col)

    def __hash__(self):
        return self.row * 31 + self.col
