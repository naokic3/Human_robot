import random
from gridworld import GridWorld, Player
from drives import DriveCORE


def choose_action(world: GridWorld, player_idx: int, drives: DriveCORE) -> str:
    p = world.players[player_idx]
    best_score = float('-inf')
    best_dirs = []

    for direction, (dr, dc) in GridWorld.MOVE_DELTAS.items():
        new_r, new_c = p.row + dr, p.col + dc
        if not world.is_passable(new_r, new_c):
            new_r, new_c = p.row, p.col  # bumps into wall or obstacle, stays put

        energy_next = p.energy - GridWorld.ENERGY_DECAY
        if world.grid[new_r, new_c] == 1:
            energy_next += GridWorld.FOOD_RESTORE
        energy_next = max(0.0, min(1.0, energy_next))

        score = drives.score(p.energy, energy_next, new_r, new_c)
        if score > best_score:
            best_score = score
            best_dirs = [direction]
        elif score == best_score:
            best_dirs.append(direction)

    return random.choice(best_dirs)
