"""
entities.py - Top-Down Game Entities and Vector UI Rendering
Contains PlayerTopDown, EnemyTopDown with optimized 30-frame A* pathfinding,
VirtualJoystick with visual circular border and centered touch-sensitive knob,
and pure pygame.draw vector UI renderers.
STRICTLY ZERO FONT CALLS - No pygame.font.SysFont to ensure crash-proof Android deployment.
"""

import math
import heapq
from typing import List, Tuple, Optional, Dict
import pygame

# Segment mapping for pure vector digit drawing (7-segment display logic)
DIGIT_SEGMENTS = {
    '0': (1, 1, 1, 1, 1, 1, 0),
    '1': (0, 1, 1, 0, 0, 0, 0),
    '2': (1, 1, 0, 1, 1, 0, 1),
    '3': (1, 1, 1, 1, 0, 0, 1),
    '4': (0, 1, 1, 0, 0, 1, 1),
    '5': (1, 0, 1, 1, 0, 1, 1),
    '6': (1, 0, 1, 1, 1, 1, 1),
    '7': (1, 1, 1, 0, 0, 0, 0),
    '8': (1, 1, 1, 1, 1, 1, 1),
    '9': (1, 1, 1, 1, 0, 1, 1),
    '-': (0, 0, 0, 0, 0, 0, 1),
    ':': (),
}

# Vector strokes for uppercase letters (normalized coordinates 0.0 to 1.0)
VECTOR_FONT_STROKES: Dict[str, List[List[Tuple[float, float]]]] = {
    'A': [[(0.0, 1.0), (0.5, 0.0), (1.0, 1.0)], [(0.2, 0.6), (0.8, 0.6)]],
    'B': [[(0.0, 1.0), (0.0, 0.0), (0.7, 0.0), (0.9, 0.25), (0.7, 0.5), (0.0, 0.5)],
          [(0.7, 0.5), (0.9, 0.75), (0.7, 1.0), (0.0, 1.0)]],
    'C': [[(1.0, 0.1), (0.3, 0.0), (0.0, 0.3), (0.0, 0.7), (0.3, 1.0), (1.0, 0.9)]],
    'D': [[(0.0, 1.0), (0.0, 0.0), (0.6, 0.0), (1.0, 0.4), (1.0, 0.6), (0.6, 1.0), (0.0, 1.0)]],
    'E': [[(1.0, 0.0), (0.0, 0.0), (0.0, 1.0), (1.0, 1.0)], [(0.0, 0.5), (0.7, 0.5)]],
    'F': [[(0.0, 1.0), (0.0, 0.0), (1.0, 0.0)], [(0.0, 0.5), (0.7, 0.5)]],
    'G': [[(1.0, 0.1), (0.2, 0.0), (0.0, 0.3), (0.0, 0.7), (0.2, 1.0), (0.9, 1.0), (0.9, 0.5), (0.5, 0.5)]],
    'H': [[(0.0, 0.0), (0.0, 1.0)], [(1.0, 0.0), (1.0, 1.0)], [(0.0, 0.5), (1.0, 0.5)]],
    'I': [[(0.2, 0.0), (0.8, 0.0)], [(0.5, 0.0), (0.5, 1.0)], [(0.2, 1.0), (0.8, 1.0)]],
    'J': [[(0.8, 0.0), (0.8, 0.8), (0.5, 1.0), (0.1, 0.8), (0.1, 0.6)]],
    'K': [[(0.0, 0.0), (0.0, 1.0)], [(1.0, 0.0), (0.0, 0.5), (1.0, 1.0)]],
    'L': [[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0)]],
    'M': [[(0.0, 1.0), (0.0, 0.0), (0.5, 0.6), (1.0, 0.0), (1.0, 1.0)]],
    'N': [[(0.0, 1.0), (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)]],
    'O': [[(0.2, 0.0), (0.8, 0.0), (1.0, 0.3), (1.0, 0.7), (0.8, 1.0), (0.2, 1.0), (0.0, 0.7), (0.0, 0.3), (0.2, 0.0)]],
    'P': [[(0.0, 1.0), (0.0, 0.0), (0.8, 0.0), (1.0, 0.25), (0.8, 0.5), (0.0, 0.5)]],
    'Q': [[(0.2, 0.0), (0.8, 0.0), (1.0, 0.3), (1.0, 0.7), (0.8, 1.0), (0.2, 1.0), (0.0, 0.7), (0.0, 0.3), (0.2, 0.0)],
          [(0.6, 0.6), (1.0, 1.0)]],
    'R': [[(0.0, 1.0), (0.0, 0.0), (0.8, 0.0), (1.0, 0.25), (0.8, 0.5), (0.0, 0.5)], [(0.5, 0.5), (1.0, 1.0)]],
    'S': [[(1.0, 0.1), (0.3, 0.0), (0.0, 0.3), (1.0, 0.7), (0.7, 1.0), (0.0, 0.9)]],
    'T': [[(0.0, 0.0), (1.0, 0.0)], [(0.5, 0.0), (0.5, 1.0)]],
    'U': [[(0.0, 0.0), (0.0, 0.8), (0.3, 1.0), (0.7, 1.0), (1.0, 0.8), (1.0, 0.0)]],
    'V': [[(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)]],
    'W': [[(0.0, 0.0), (0.2, 1.0), (0.5, 0.4), (0.8, 1.0), (1.0, 0.0)]],
    'X': [[(0.0, 0.0), (1.0, 1.0)], [(1.0, 0.0), (0.0, 1.0)]],
    'Y': [[(0.0, 0.0), (0.5, 0.5), (1.0, 0.0)], [(0.5, 0.5), (0.5, 1.0)]],
    'Z': [[(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)]],
    '/': [[(0.0, 1.0), (1.0, 0.0)]],
    '>': [[(0.1, 0.1), (0.9, 0.5), (0.1, 0.9)]],
    '<': [[(0.9, 0.1), (0.1, 0.5), (0.9, 0.9)]],
}


def draw_vector_char(surface: pygame.Surface, char: str, x: int, y: int, w: int, h: int,
                     color: Tuple[int, int, int], thickness: int = 2) -> None:
    char = char.upper()
    if char == ' ':
        return
    if char in DIGIT_SEGMENTS and DIGIT_SEGMENTS[char]:
        segs = DIGIT_SEGMENTS[char]
        coords = [
            ((x, y), (x + w, y)),
            ((x + w, y), (x + w, y + h // 2)),
            ((x + w, y + h // 2), (x + w, y + h)),
            ((x, y + h), (x + w, y + h)),
            ((x, y + h // 2), (x, y + h)),
            ((x, y), (x, y + h // 2)),
            ((x, y + h // 2), (x + w, y + h // 2)),
        ]
        for idx, active in enumerate(segs):
            if active:
                pygame.draw.line(surface, color, coords[idx][0], coords[idx][1], thickness)
        return

    if char == ':':
        r = max(2, thickness)
        pygame.draw.circle(surface, color, (x + w // 2, y + h // 3), r)
        pygame.draw.circle(surface, color, (x + w // 2, y + 2 * h // 3), r)
        return

    if char in VECTOR_FONT_STROKES:
        strokes = VECTOR_FONT_STROKES[char]
        for stroke in strokes:
            pts = [(int(x + px * w), int(y + py * h)) for px, py in stroke]
            if len(pts) > 1:
                pygame.draw.lines(surface, color, False, pts, thickness)


def draw_vector_string(surface: pygame.Surface, text: str, x: int, y: int,
                       char_w: int = 14, char_h: int = 22, spacing: int = 5,
                       color: Tuple[int, int, int] = (255, 255, 255), thickness: int = 2) -> int:
    cur_x = x
    for char in text:
        draw_vector_char(surface, char, cur_x, y, char_w, char_h, color, thickness)
        cur_x += char_w + spacing
    return cur_x


def draw_vector_bar(surface: pygame.Surface, x: int, y: int, w: int, h: int,
                    current: float, max_val: float,
                    fg_color: Tuple[int, int, int], bg_color: Tuple[int, int, int] = (30, 30, 40),
                    border_color: Tuple[int, int, int] = (180, 180, 200)) -> None:
    ratio = max(0.0, min(1.0, current / max(1.0, max_val)))
    fill_w = int(w * ratio)

    pygame.draw.rect(surface, bg_color, (x, y, w, h))
    if fill_w > 0:
        pygame.draw.rect(surface, fg_color, (x, y, fill_w, h))

    pygame.draw.rect(surface, border_color, (x, y, w, h), 2)
    for i in range(1, 4):
        tx = x + (w * i) // 4
        pygame.draw.line(surface, border_color, (tx, y), (tx, y + h - 1), 1)


def draw_vector_icon(surface: pygame.Surface, icon_type: str, x: int, y: int,
                     size: int, color: Tuple[int, int, int]) -> None:
    cx, cy = x + size // 2, y + size // 2
    r = size // 2

    if icon_type == "heart":
        pts = [
            (cx, cy + r),
            (cx - r, cy),
            (cx - r // 2, cy - r),
            (cx, cy - r // 3),
            (cx + r // 2, cy - r),
            (cx + r, cy),
        ]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.polygon(surface, (255, 200, 200), pts, 1)

    elif icon_type == "stamina":
        pts = [
            (cx + r // 3, cy - r),
            (cx - r // 3, cy - r // 6),
            (cx, cy - r // 6),
            (cx - r // 2, cy + r),
            (cx + r // 4, cy + r // 8),
            (cx - r // 8, cy + r // 8),
        ]
        pygame.draw.polygon(surface, color, pts)

    elif icon_type == "key":
        pygame.draw.circle(surface, color, (cx - r // 3, cy), r // 2, 2)
        pygame.draw.line(surface, color, (cx, cy), (cx + r, cy), 3)
        pygame.draw.line(surface, color, (cx + r // 2, cy), (cx + r // 2, cy + r // 2), 2)
        pygame.draw.line(surface, color, (cx + 4 * r // 5, cy), (cx + 4 * r // 5, cy + r // 2), 2)

    elif icon_type == "skull":
        pygame.draw.circle(surface, color, (cx, cy - r // 4), 2 * r // 3)
        pygame.draw.rect(surface, color, (cx - r // 3, cy, 2 * r // 3, r // 2))
        pygame.draw.circle(surface, (10, 10, 15), (cx - r // 4, cy - r // 4), r // 6)
        pygame.draw.circle(surface, (10, 10, 15), (cx + r // 4, cy - r // 4), r // 6)


class PlayerTopDown:
    """
    Top-Down Player entity with 2D coordinate velocity, orientation angle,
    wall sliding collision, stamina sprint, and health.
    """

    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y
        self.angle: float = 0.0
        self.radius: float = 0.32
        self.max_health: float = 100.0
        self.health: float = 100.0
        self.max_stamina: float = 100.0
        self.stamina: float = 100.0
        self.is_sprinting: bool = False
        self.keys_collected: int = 0
        self.total_keys: int = 3
        self.score: int = 0
        self.time_alive: float = 0.0

    def update_motion(self, vx: float, vy: float, dt: float, maze_grid: List[List[int]]) -> None:
        """Updates 2D motion with wall sliding collision and stamina sprint."""
        self.time_alive += dt

        mag = math.hypot(vx, vy)
        if mag > 1.0:
            vx /= mag
            vy /= mag

        if mag > 0.08:
            self.angle = math.atan2(vy, vx)

        base_speed = 3.4
        if self.is_sprinting and self.stamina > 5.0 and mag > 0.08:
            speed = base_speed * 1.65
            self.stamina = max(0.0, self.stamina - 35.0 * dt)
        else:
            speed = base_speed
            self.is_sprinting = False
            self.stamina = min(self.max_stamina, self.stamina + 22.0 * dt)

        dx = vx * speed * dt
        dy = vy * speed * dt

        # Collision sliding on X
        new_x = self.x + dx
        if not self._check_collision(new_x, self.y, maze_grid):
            self.x = new_x

        # Collision sliding on Y
        new_y = self.y + dy
        if not self._check_collision(self.x, new_y, maze_grid):
            self.y = new_y

    def _check_collision(self, px: float, py: float, grid: List[List[int]]) -> bool:
        r = self.radius
        check_points = [
            (px - r, py - r), (px + r, py - r),
            (px - r, py + r), (px + r, py + r),
            (px, py - r), (px, py + r),
            (px - r, py), (px + r, py),
        ]
        h = len(grid)
        w = len(grid[0])
        for cx, cy in check_points:
            gx, gy = int(cx), int(cy)
            if gx < 0 or gx >= w or gy < 0 or gy >= h or grid[gy][gx] == 1:
                return True
        return False


DIFFICULTY_PRESETS = {
    "EASY": {"speed": 1.65, "recalc_interval": 48},
    "NORMAL": {"speed": 2.2, "recalc_interval": 30},
    "HARD": {"speed": 2.75, "recalc_interval": 16},
}


class EnemyTopDown:
    """
    Top-Down Chasing Beast with difficulty-configured speed and A* recalculation interval.
    """

    def __init__(self, x: float, y: float, difficulty: str = "NORMAL"):
        self.x: float = x
        self.y: float = y
        self.angle: float = 0.0
        self.difficulty = difficulty.upper()
        preset = DIFFICULTY_PRESETS.get(self.difficulty, DIFFICULTY_PRESETS["NORMAL"])
        self.speed: float = preset["speed"]
        self.recalc_interval: int = preset["recalc_interval"]
        self.radius: float = 0.36
        self.path: List[Tuple[int, int]] = []
        self.recalc_timer: int = 0
        self.distance_to_player: float = 999.0
        self.pulse_phase: float = 0.0

    def update(self, player_x: float, player_y: float, maze_grid: List[List[int]], dt: float) -> bool:
        self.pulse_phase = (self.pulse_phase + dt * 4.5) % (2.0 * math.pi)
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        self.distance_to_player = dist

        if dist < 0.65:
            return True

        self.recalc_timer += 1
        if self.recalc_timer >= self.recalc_interval or not self.path:
            self.recalc_timer = 0
            start_node = (int(self.x), int(self.y))
            goal_node = (int(player_x), int(player_y))
            self.path = self._astar_search(start_node, goal_node, maze_grid)

        target_x, target_y = player_x, player_y
        if len(self.path) > 1:
            next_node = self.path[1]
            target_x = next_node[0] + 0.5
            target_y = next_node[1] + 0.5
            if math.hypot(target_x - self.x, target_y - self.y) < 0.25:
                self.path.pop(0)

        tdx = target_x - self.x
        tdy = target_y - self.y
        tdist = math.hypot(tdx, tdy)

        if tdist > 0.001:
            self.angle = math.atan2(tdy, tdx)
            move_step = min(self.speed * dt, tdist)
            nx = self.x + (tdx / tdist) * move_step
            ny = self.y + (tdy / tdist) * move_step
            gx, gy = int(nx), int(ny)
            if 0 <= gx < 20 and 0 <= gy < 20 and maze_grid[gy][gx] == 0:
                self.x = nx
                self.y = ny

        return False

    def _astar_search(self, start: Tuple[int, int], goal: Tuple[int, int],
                      grid: List[List[int]]) -> List[Tuple[int, int]]:
        if start == goal:
            return [start]

        h, w = len(grid), len(grid[0])
        open_set: List[Tuple[float, int, int]] = []
        heapq.heappush(open_set, (0.0, start[0], start[1]))

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0.0}

        def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        while open_set:
            _, cx, cy = heapq.heappop(open_set)
            current = (cx, cy)

            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == 0:
                    neighbor = (nx, ny)
                    tentative_g = g_score[current] + 1.0
                    if tentative_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f_score, nx, ny))

        return [start]


class VirtualJoystick:
    """
    Analog Multi-Touch Virtual Joystick for Mobile Screens.
    Rendered with a high-tech glowing circular border and centered touch-sensitive knob.
    """

    def __init__(self, screen_w: int, screen_h: int):
        self.resize(screen_w, screen_h)
        self.touch_id: Optional[int] = None
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.sprint_pressed: bool = False

    def resize(self, w: int, h: int) -> None:
        self.w = w
        self.h = h
        # Compact mobile sizing to prevent overlap and fit phone UI perfectly
        self.base_radius = int(min(w, h) * 0.105)
        self.knob_radius = int(self.base_radius * 0.44)

        # Left joystick anchor (compact margins)
        self.cx = int(self.base_radius * 1.35) + 12
        self.cy = h - int(self.base_radius * 1.35) - 12
        self.knob_x = float(self.cx)
        self.knob_y = float(self.cy)

        # Compact sprint button on right
        btn_s = int(self.base_radius * 1.05)
        self.sprint_rect = pygame.Rect(w - btn_s - 16, h - btn_s - 16, btn_s, btn_s)

    def handle_touch_down(self, touch_id: int, screen_x: float, screen_y: float) -> None:
        px = screen_x * self.w
        py = screen_y * self.h

        if self.sprint_rect.collidepoint(px, py):
            self.sprint_pressed = True
            return

        if px < self.w * 0.5:
            self.touch_id = touch_id
            self._update_knob(px, py)

    def handle_touch_move(self, touch_id: int, screen_x: float, screen_y: float) -> None:
        if touch_id == self.touch_id:
            px = screen_x * self.w
            py = screen_y * self.h
            self._update_knob(px, py)

    def handle_touch_up(self, touch_id: int) -> None:
        if touch_id == self.touch_id:
            self.touch_id = None
            self.knob_x = float(self.cx)
            self.knob_y = float(self.cy)
            self.vx = 0.0
            self.vy = 0.0
        self.sprint_pressed = False

    def _update_knob(self, px: float, py: float) -> None:
        dx = px - self.cx
        dy = py - self.cy
        dist = math.hypot(dx, dy)
        max_dist = float(self.base_radius)

        if dist > max_dist and dist > 0.0:
            dx = (dx / dist) * max_dist
            dy = (dy / dist) * max_dist

        self.knob_x = self.cx + dx
        self.knob_y = self.cy + dy

        self.vx = dx / max_dist
        self.vy = dy / max_dist

    def render(self, surface: pygame.Surface) -> None:
        # Visual circular border
        active = self.touch_id is not None
        border_col = (0, 220, 240) if active else (40, 100, 140)
        pygame.draw.circle(surface, (12, 16, 24), (self.cx, self.cy), self.base_radius)
        pygame.draw.circle(surface, border_col, (self.cx, self.cy), self.base_radius, 2)
        pygame.draw.circle(surface, (25, 45, 65), (self.cx, self.cy), int(self.base_radius * 0.6), 1)

        # Crosshair lines
        pygame.draw.line(surface, (30, 60, 80), (self.cx - self.base_radius + 4, self.cy), (self.cx + self.base_radius - 4, self.cy), 1)
        pygame.draw.line(surface, (30, 60, 80), (self.cx, self.cy - self.base_radius + 4), (self.cx, self.cy + self.base_radius - 4), 1)

        # Cardinal tick triangles (▲, ▼, ◄, ►)
        tick_col = (0, 240, 255) if active else (70, 130, 160)
        pygame.draw.polygon(surface, tick_col, [(self.cx, self.cy - self.base_radius + 3), (self.cx - 5, self.cy - self.base_radius + 11), (self.cx + 5, self.cy - self.base_radius + 11)])
        pygame.draw.polygon(surface, tick_col, [(self.cx, self.cy + self.base_radius - 3), (self.cx - 5, self.cy + self.base_radius - 11), (self.cx + 5, self.cy + self.base_radius - 11)])
        pygame.draw.polygon(surface, tick_col, [(self.cx - self.base_radius + 3, self.cy), (self.cx - self.base_radius + 11, self.cy - 5), (self.cx - self.base_radius + 11, self.cy + 5)])
        pygame.draw.polygon(surface, tick_col, [(self.cx + self.base_radius - 3, self.cy), (self.cx + self.base_radius - 11, self.cy - 5), (self.cx + self.base_radius - 11, self.cy + 5)])

        # Centered touch-sensitive knob
        kx, ky = int(self.knob_x), int(self.knob_y)
        knob_core = (0, 240, 200) if active else (70, 85, 110)
        knob_rim = (255, 255, 255) if active else (140, 170, 200)
        pygame.draw.circle(surface, (20, 25, 38), (kx, ky), self.knob_radius)
        pygame.draw.circle(surface, knob_core, (kx, ky), int(self.knob_radius * 0.55))
        pygame.draw.circle(surface, knob_rim, (kx, ky), self.knob_radius, 2)
        pygame.draw.circle(surface, (255, 255, 255), (kx, ky), max(2, self.knob_radius // 4))

        # Sprint Action Button
        sprint_col = (255, 140, 0) if self.sprint_pressed else (35, 42, 60)
        pygame.draw.rect(surface, sprint_col, self.sprint_rect, border_radius=12)
        sprint_rim = (255, 220, 120) if self.sprint_pressed else (120, 135, 160)
        pygame.draw.rect(surface, sprint_rim, self.sprint_rect, width=2, border_radius=12)
        draw_vector_icon(surface, "stamina", self.sprint_rect.x + (self.sprint_rect.w - 28) // 2, self.sprint_rect.y + (self.sprint_rect.h - 28) // 2, 28, (255, 255, 255))
