"""
maze_generator.py - Procedural 20x20 Dungeon Maze Generator
Optimized for mobile memory footprint and deterministic corridors.
Solid stone walls = 1, Walkable passage corridors = 0.
"""

import random
from typing import List, Tuple, Optional

# Grid dimension strictly locked to 20x20 blocks
GRID_WIDTH: int = 20
GRID_HEIGHT: int = 20


class DungeonMaze:
    """
    Generates a 20x20 procedural dungeon maze using recursive backtracking
    with loop injections to prevent dead-end traps during enemy chases.
    """

    def __init__(self, width: int = GRID_WIDTH, height: int = GRID_HEIGHT, seed: Optional[int] = None):
        self.width = width
        self.height = height
        if seed is not None:
            random.seed(seed)
        self.grid: List[List[int]] = [[1 for _ in range(self.width)] for _ in range(self.height)]
        self.player_spawn: Tuple[float, float] = (1.5, 1.5)
        self.enemy_spawn: Tuple[float, float] = (18.5, 18.5)
        self.exit_pos: Tuple[float, float] = (18.5, 1.5)
        self.key_positions: List[Tuple[float, float]] = []
        self._carve_maze()

    def _carve_maze(self) -> None:
        """Carves corridors using randomized depth-first search with corridor loops."""
        # Start carving from (1, 1)
        start_x, start_y = 1, 1
        self.grid[start_y][start_x] = 0
        stack: List[Tuple[int, int]] = [(start_x, start_y)]

        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]

        while stack:
            cx, cy = stack[-1]
            unvisited_neighbors = []

            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 1 <= nx < self.width - 1 and 1 <= ny < self.height - 1:
                    if self.grid[ny][nx] == 1:
                        unvisited_neighbors.append((nx, ny, dx, dy))

            if unvisited_neighbors:
                nx, ny, dx, dy = random.choice(unvisited_neighbors)
                # Carve through wall
                self.grid[cy + dy // 2][cx + dx // 2] = 0
                self.grid[ny][nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

        # Add loops and wider corridors (10-15% chance to break extra walls)
        # to ensure dynamic escape routes from the A* chasing enemy
        for y in range(2, self.height - 2):
            for x in range(2, self.width - 2):
                if self.grid[y][x] == 1:
                    # Check horizontal connectivity
                    if self.grid[y][x - 1] == 0 and self.grid[y][x + 1] == 0:
                        if random.random() < 0.15:
                            self.grid[y][x] = 0
                    # Check vertical connectivity
                    elif self.grid[y - 1][x] == 0 and self.grid[y + 1][x] == 0:
                        if random.random() < 0.15:
                            self.grid[y][x] = 0

        # Carve central chamber for intense chase encounters
        for cy in range(8, 12):
            for cx in range(8, 12):
                self.grid[cy][cx] = 0

        # Enforce solid outer boundary walls
        for x in range(self.width):
            self.grid[0][x] = 1
            self.grid[self.height - 1][x] = 1
        for y in range(self.height):
            self.grid[y][0] = 1
            self.grid[y][self.width - 1] = 1

        self._assign_entities()

    def _assign_entities(self) -> None:
        """Finds open corridor tiles for player, enemy, exit, and relic keys."""
        open_tiles = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == 0:
                    open_tiles.append((x + 0.5, y + 0.5))

        if not open_tiles:
            # Fallback if map generation was blocked
            self.grid[1][1] = 0
            self.grid[1][2] = 0
            open_tiles = [(1.5, 1.5), (2.5, 1.5)]

        # Player spawn: top-left quadrant open tile
        top_left_tiles = [t for t in open_tiles if t[0] < 7 and t[1] < 7]
        self.player_spawn = top_left_tiles[0] if top_left_tiles else open_tiles[0]

        # Enemy spawn: far corner (bottom-right quadrant open tile)
        bottom_right_tiles = [t for t in open_tiles if t[0] > 12 and t[1] > 12]
        self.enemy_spawn = bottom_right_tiles[-1] if bottom_right_tiles else open_tiles[-1]

        # Exit spawn: far corner (top-right or bottom-left)
        top_right_tiles = [t for t in open_tiles if t[0] > 13 and t[1] < 7]
        self.exit_pos = top_right_tiles[0] if top_right_tiles else open_tiles[len(open_tiles) // 2]

        # Place 3 dungeon keys across different quadrants
        candidates = [t for t in open_tiles if t not in (self.player_spawn, self.enemy_spawn, self.exit_pos)]
        random.shuffle(candidates)
        self.key_positions = candidates[:3]

    def is_wall(self, x: float, y: float) -> bool:
        """Check if floating point position collides with a solid grid wall."""
        gx = int(x)
        gy = int(y)
        if gx < 0 or gx >= self.width or gy < 0 or gy >= self.height:
            return True
        return self.grid[gy][gx] == 1

    def to_list(self) -> List[List[int]]:
        """Returns the 20x20 2D integer matrix."""
        return self.grid


def generate_dungeon(seed: Optional[int] = None) -> DungeonMaze:
    """Factory function to build and return a ready-to-render DungeonMaze."""
    return DungeonMaze(GRID_WIDTH, GRID_HEIGHT, seed=seed)
