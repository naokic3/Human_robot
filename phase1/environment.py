import numpy as np
from dataclasses import dataclass


@dataclass
class Player:
    row: int
    col: int
    energy: float = 1.0


class GridWorld:
    ENERGY_DECAY = 0.05
    FOOD_RESTORE = 0.4

    MOVE_DELTAS = {
        (-1, 0):    (-1,  0),
        (1, 0):  ( 1,  0),
        (0, -1):  ( 0, -1),
        (0, 1): ( 0,  1),
    }

    OBSTACLE = 2

    def __init__(self, width=10, height=10, num_food=3, num_obstacles=0, num_players=1, seed=None):
        self.width = width
        self.height = height
        self._rng = np.random.default_rng(seed)
        self._num_food = num_food

        self.grid = np.zeros((height, width), dtype=int)

        all_indices = self._rng.permutation(height * width)
        take = lambda n, offset=0: all_indices[offset:offset + n].tolist()

        obstacle_indices = take(num_obstacles)
        food_indices = take(num_food, offset=num_obstacles)
        player_indices = take(num_players, offset=num_obstacles + num_food)

        self.grid[np.unravel_index(obstacle_indices, (height, width))] = self.OBSTACLE
        self.grid[np.unravel_index(food_indices, (height, width))] = 1

        rows, cols = np.unravel_index(player_indices, (height, width))
        self.players = [Player(row=int(r), col=int(c)) for r, c in zip(rows, cols)]

    def in_bounds(self, row, col):
        return 0 <= row < self.height and 0 <= col < self.width

    def is_passable(self, row, col):
        return self.in_bounds(row, col) and self.grid[row, col] != self.OBSTACLE

    def _respawn_food(self):
        occupied = {(p.row, p.col) for p in self.players}
        empty = [(r, c) for r in range(self.height) for c in range(self.width)
                 if self.grid[r, c] == 0 and (r, c) not in occupied]
        if empty:
            idx = self._rng.integers(len(empty))
            r, c = empty[idx]
            self.grid[r, c] = 1

    def step(self, player_idx, direction: tuple):
        if direction not in self.MOVE_DELTAS:
            raise ValueError(f"Invalid direction: {direction}")
        p = self.players[player_idx]
        dr, dc = self.MOVE_DELTAS[direction]
        new_r, new_c = p.row + dr, p.col + dc
        if self.is_passable(new_r, new_c):
            p.row, p.col = new_r, new_c
        p.energy = max(0.0, p.energy - self.ENERGY_DECAY)
        if self.grid[p.row, p.col] == 1:
            p.energy = min(1.0, p.energy + self.FOOD_RESTORE)
            self.grid[p.row, p.col] = 0
            self._respawn_food()



    def render(self):
        player_positions = {(p.row, p.col) for p in self.players}
        for r in range(self.height):
            for c in range(self.width):
                if (r, c) in player_positions:
                    print("P", end=" ")
                elif self.grid[r, c] == self.OBSTACLE:
                    print("X", end=" ")
                elif self.grid[r, c] == 1:
                    print("F", end=" ")
                else:
                    print(".", end=" ")
            print()
