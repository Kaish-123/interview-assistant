import unittest

from chris_navigates_maze import minMoves


class TestChrisNavigatesMaze(unittest.TestCase):
    def test_sample(self):
        maze = [[0, 2, 1], [1, 2, 0], [1, 0, 0]]
        self.assertEqual(minMoves(maze, 2, 2), 4)

    def test_no_coins_direct_path(self):
        maze = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.assertEqual(minMoves(maze, 2, 2), 4)

    def test_already_at_alex_no_coins(self):
        maze = [[0, 0], [0, 0]]
        self.assertEqual(minMoves(maze, 0, 0), 0)

    def test_already_at_alex_start_has_only_coin(self):
        maze = [[2, 0], [0, 0]]
        self.assertEqual(minMoves(maze, 0, 0), 0)

    def test_alex_at_start_must_collect_and_return(self):
        maze = [[0, 2], [0, 0]]
        self.assertEqual(minMoves(maze, 0, 0), 2)

    def test_start_blocked(self):
        maze = [[1, 0], [0, 0]]
        self.assertEqual(minMoves(maze, 1, 1), -1)

    def test_alex_blocked(self):
        maze = [[0, 0], [0, 1]]
        self.assertEqual(minMoves(maze, 1, 1), -1)

    def test_unreachable_alex(self):
        maze = [[0, 1], [1, 0]]
        self.assertEqual(minMoves(maze, 1, 1), -1)

    def test_unreachable_coin(self):
        maze = [[0, 1, 2], [0, 1, 1], [0, 0, 0]]
        self.assertEqual(minMoves(maze, 2, 2), -1)

    def test_coin_on_alex(self):
        maze = [[0, 0], [0, 2]]
        self.assertEqual(minMoves(maze, 1, 1), 2)

    def test_must_detour_for_coin(self):
        maze = [
            [0, 0, 0],
            [1, 1, 0],
            [2, 0, 0],
        ]
        # Collect coin at (2, 0) then reach Alex at (0, 2):
        # (0,0)->(0,1)->(0,2)->(1,2)->(2,2)->(2,1)->(2,0)->(2,1)->(2,2)->(1,2)->(0,2)
        # shortest: (0,0)->(0,1)->(0,2)->(1,2)->(2,2)->(2,1)->(2,0) then back to (0,2)
        # (0,0)-(0,1)-(0,2)-(1,2)-(2,2)-(2,1)-(2,0)-(2,1)-(2,2)-(1,2)-(0,2) = 10
        self.assertEqual(minMoves(maze, 0, 2), 10)

    def test_pass_through_alex_before_collecting(self):
        maze = [
            [0, 0, 0],
            [0, 1, 0],
            [2, 1, 0],
        ]
        # Alex at (0, 2). Coin at (2, 0). Must go to coin (possibly via Alex) then to Alex.
        # (0,0)->(1,0)->(2,0)->(1,0)->(0,0)->(0,1)->(0,2) = 6
        self.assertEqual(minMoves(maze, 0, 2), 6)

    def test_two_coins_not_on_shortest_path(self):
        maze = [
            [0, 0, 0, 2],
            [0, 1, 1, 1],
            [0, 0, 0, 2],
        ]
        # Coins at (0,3) and (2,3), Alex at (2, 2).
        # Start -> (0,3) = 3, (0,3) -> (2,3) = 8, (2,3) -> (2,2) = 1.
        self.assertEqual(minMoves(maze, 2, 2), 12)

    def test_single_open_cell(self):
        self.assertEqual(minMoves([[0]], 0, 0), 0)

    def test_single_coin_cell(self):
        self.assertEqual(minMoves([[2]], 0, 0), 0)

    def test_single_blocked_cell(self):
        self.assertEqual(minMoves([[1]], 0, 0), -1)

    def test_destination_out_of_bounds(self):
        maze = [[0, 0], [0, 0]]
        self.assertEqual(minMoves(maze, 5, 0), -1)
        self.assertEqual(minMoves(maze, 0, 5), -1)
        self.assertEqual(minMoves(maze, -1, 0), -1)

    def test_empty_maze(self):
        self.assertEqual(minMoves([], 0, 0), -1)
        self.assertEqual(minMoves([[]], 0, 0), -1)

    def test_only_horizontal_corridor(self):
        maze = [[0, 2, 0, 2, 0]]
        self.assertEqual(minMoves(maze, 0, 4), 4)

    def test_revisit_cell_with_new_coins(self):
        maze = [
            [0, 2],
            [2, 0],
        ]
        # Coins at (0,1) and (1,0), Alex at (1,1).
        # (0,0)->(0,1)->(0,0)->(1,0)->(1,1) = 4
        # (0,0)->(0,1)->(1,1) is only 2 but misses the coin at (1,0).
        self.assertEqual(minMoves(maze, 1, 1), 4)

    def test_coin_blocked_but_alex_reachable(self):
        maze = [
            [0, 0, 1],
            [0, 0, 1],
            [0, 1, 2],
        ]
        self.assertEqual(minMoves(maze, 1, 1), -1)

    def test_all_coins_along_path(self):
        maze = [
            [0, 2, 0],
            [1, 2, 0],
            [1, 0, 0],
        ]
        self.assertEqual(minMoves(maze, 2, 2), 4)

    def test_wide_open_with_far_coin(self):
        maze = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [2, 0, 0, 0],
        ]
        # Coin at (3,0), Alex at (0,3):
        # (0,0)->(1,0)->(2,0)->(3,0)->(2,0)->(1,0)->(0,0)->(0,1)->(0,2)->(0,3) = 9
        # or (0,0)->down to coin then across and up: (3,0)->(3,1)->(3,2)->(3,3)->(2,3)->(1,3)->(0,3)
        # from start to coin is 3, then to alex manhattan 6, total 9.
        self.assertEqual(minMoves(maze, 0, 3), 9)

    def test_start_is_a_coin(self):
        maze = [[2, 0, 2], [0, 0, 0]]
        self.assertEqual(minMoves(maze, 1, 2), 3)

    def test_three_coins_order_matters(self):
        maze = [
            [0, 2, 0, 2],
            [1, 1, 1, 0],
            [2, 0, 0, 0],
        ]
        self.assertEqual(minMoves(maze, 2, 3), 11)

    def test_every_cell_is_a_coin(self):
        maze = [[2, 2], [2, 2]]
        self.assertEqual(minMoves(maze, 1, 1), 4)
