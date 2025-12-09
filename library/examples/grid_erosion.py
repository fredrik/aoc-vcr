"""Example: Grid erosion visualization.

Simulates erosion where cells with fewer than 2 neighbors are removed each step.
"""

import random
import time

from aoc_vcr import Recorder


def create_grid(width: int, height: int, density: float = 0.4) -> dict[tuple[int, int], str]:
    """Create a random grid with given density of filled cells."""
    grid = {}
    for row in range(height):
        for col in range(width):
            if random.random() < density:
                grid[(row, col)] = "#"
    return grid


def count_neighbors(grid: dict[tuple[int, int], str], row: int, col: int) -> int:
    """Count filled neighbors (8-directional)."""
    count = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            if (row + dr, col + dc) in grid:
                count += 1
    return count


def erode_one(grid: dict[tuple[int, int], str], min_neighbors: int = 2) -> tuple[dict, tuple[int, int] | None]:
    """Remove one cell with fewer than min_neighbors. Returns new grid and removed cell."""
    for (row, col), val in grid.items():
        if count_neighbors(grid, row, col) < min_neighbors:
            new_grid = {k: v for k, v in grid.items() if k != (row, col)}
            return new_grid, (row, col)
    return grid, None


def solve(width: int = 80, height: int = 50, seed: int | None = None):
    """Run erosion simulation with visualization."""
    if seed is not None:
        random.seed(seed)

    rec = Recorder(day=99, part=1)

    grid = create_grid(width, height)
    initial_count = len(grid)
    rec.snapshot(grid=grid, label="initial", cells=len(grid))

    frame = 0
    total_removed = 0
    removed_cell = True
    while removed_cell is not None and grid:
        grid, removed_cell = erode_one(grid)
        if removed_cell:
            frame += 1
            total_removed += 1
            rec.snapshot(grid=grid, frame=frame, cells=len(grid), removed=removed_cell)

    rec.finish()

    print(f"Erosion complete: {initial_count} → {len(grid)} cells in {frame} frames")
    return len(grid)


if __name__ == "__main__":
    solve(seed=42)
