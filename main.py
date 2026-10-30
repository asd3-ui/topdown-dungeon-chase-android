"""
main.py - Top-Down Dungeon Chase Game Engine
Optimized for mobile Android deployment via Buildozer and Pygame.
Features 20x20 top-down dungeon rendering, smooth follow camera, tactical overview mode,
30-frame cached A* chasing shadow beast, multi-touch virtual analog joystick,
Android Back Button (K_AC_BACK) intercepting, and local JSON high-score persistence.
STRICTLY ZERO FONT CALLS - No pygame.font.SysFont to prevent Android launch crash.
"""

import sys
import os
import math
import json
import time
from typing import List, Dict, Any, Tuple, Optional
import pygame

# Import local engine modules
from maze_generator import generate_dungeon, DungeonMaze, GRID_WIDTH, GRID_HEIGHT
from entities import (
    PlayerTopDown, EnemyTopDown, VirtualJoystick,
    draw_vector_string, draw_vector_bar, draw_vector_icon, draw_vector_char
)

# Configuration constants
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 480
TARGET_FPS: int = 60
TILE_SIZE: int = 56

# Color Palette (Top-Down Dungeon Theme)
BG_COLOR: Tuple[int, int, int] = (10, 12, 18)
FLOOR_COLOR: Tuple[int, int, int] = (22, 24, 34)
FLOOR_BORDER: Tuple[int, int, int] = (28, 32, 45)
WALL_TOP: Tuple[int, int, int] = (45, 53, 72)
WALL_FACE: Tuple[int, int, int] = (30, 36, 51)
WALL_BORDER: Tuple[int, int, int] = (64, 76, 102)
EXIT_COLOR: Tuple[int, int, int] = (16, 185, 129)
KEY_COLOR: Tuple[int, int, int] = (245, 158, 11)

# Game States
STATE_MENU: int = 0
STATE_PLAYING: int = 1
STATE_PAUSED: int = 2
STATE_GAMEOVER: int = 3
STATE_VICTORY: int = 4

# High scores file path
HIGHSCORE_FILE: str = "highscores.json"

# Android Back Key code fallback
K_AC_BACK = getattr(pygame, 'K_AC_BACK', 1073742094)


class HighScoreManager:
    """Manages local JSON-based persistent high scores."""

    def __init__(self, filepath: str = HIGHSCORE_FILE):
        self.filepath = filepath
        self.data: Dict[str, Any] = {"best_score": 0, "best_time": 0.0, "total_escapes": 0}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def save(self) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except Exception:
            pass

    def record_run(self, score: int, survive_time: float, escaped: bool) -> bool:
        is_new_best = False
        if score > self.data.get("best_score", 0):
            self.data["best_score"] = score
            is_new_best = True
        if survive_time > self.data.get("best_time", 0.0):
            self.data["best_time"] = round(survive_time, 1)
        if escaped:
            self.data["total_escapes"] = self.data.get("total_escapes", 0) + 1
        self.save()
        return is_new_best


class SoundSynthesizer:
    """
    Lightweight procedural audio effects using numpy/pygame mixer buffers.
    Safely degrades gracefully if audio hardware is unavailable on mobile.
    """

    def __init__(self):
        self.enabled = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.enabled = True
            self.heartbeat_sound = self._make_beep(70.0, 0.12, 0.4)
            self.key_sound = self._make_beep(880.0, 0.18, 0.3)
            self.alert_sound = self._make_beep(180.0, 0.35, 0.5)
        except Exception:
            self.enabled = False

    def _make_beep(self, freq: float, duration: float, volume: float) -> Optional[pygame.mixer.Sound]:
        if not self.enabled:
            return None
        try:
            import numpy as np
            sample_rate = 22050
            n_samples = int(sample_rate * duration)
            t = np.linspace(0, duration, n_samples, False)
            waveform = np.sin(2 * np.pi * freq * t) * (np.exp(-3.0 * t))
            waveform = (waveform * 32767 * volume).astype(np.int16)
            return pygame.sndarray.make_sound(waveform)
        except Exception:
            return None

    def play_heartbeat(self):
        if self.enabled and self.heartbeat_sound:
            self.heartbeat_sound.play()

    def play_key(self):
        if self.enabled and self.key_sound:
            self.key_sound.play()

    def play_alert(self):
        if self.enabled and self.alert_sound:
            self.alert_sound.play()


class DungeonGame:
    """
    Main Game Controller & Top-Down Renderer.
    Features follow camera, 360-degree analog touch joystick, vector HUD, and persistence.
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Top-Down Dungeon Chase")
        self.clock = pygame.time.Clock()

        self.state: int = STATE_MENU
        self.highscores = HighScoreManager()
        self.audio = SoundSynthesizer()
        self.joystick = VirtualJoystick(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.difficulty: str = "NORMAL"
        self.camera_x: float = 0.0
        self.camera_y: float = 0.0
        self.full_map_mode: bool = False
        self.heartbeat_timer = 0.0
        self.init_game_session()

    def init_game_session(self) -> None:
        """Starts a fresh dungeon run with procedural maze and entities."""
        self.dungeon = generate_dungeon()
        px, py = self.dungeon.player_spawn
        ex, ey = self.dungeon.enemy_spawn

        self.player = PlayerTopDown(px, py)
        self.enemy = EnemyTopDown(ex, ey, difficulty=self.difficulty)
        self.camera_x = px * TILE_SIZE
        self.camera_y = py * TILE_SIZE
        self.game_time: float = 0.0
        self.is_new_best: bool = False

    def handle_events(self) -> bool:
        """Polls pygame events and handles Android Back Button."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.VIDEORESIZE:
                w, h = event.w, event.h
                self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                self.joystick.resize(w, h)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == K_AC_BACK:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                    elif self.state in (STATE_PAUSED, STATE_GAMEOVER, STATE_VICTORY):
                        self.state = STATE_MENU
                    elif self.state == STATE_MENU:
                        return False

                elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if self.state in (STATE_MENU, STATE_GAMEOVER, STATE_VICTORY):
                        self.init_game_session()
                        self.state = STATE_PLAYING
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING

                elif event.key == pygame.K_d and self.state in (STATE_MENU, STATE_PAUSED):
                    diffs = ["EASY", "NORMAL", "HARD"]
                    idx = (diffs.index(self.difficulty) + 1) % len(diffs)
                    self.difficulty = diffs[idx]

                elif event.key == pygame.K_m and self.state == STATE_PLAYING:
                    self.full_map_mode = not self.full_map_mode

                elif event.key == pygame.K_p and self.state == STATE_PLAYING:
                    self.state = STATE_PAUSED

            elif event.type == pygame.FINGERDOWN:
                if self.state == STATE_PLAYING:
                    self.joystick.handle_touch_down(event.finger_id, event.x, event.y)
                elif self.state in (STATE_MENU, STATE_GAMEOVER, STATE_VICTORY):
                    self.init_game_session()
                    self.state = STATE_PLAYING
                elif self.state == STATE_PAUSED:
                    self.state = STATE_PLAYING

            elif event.type == pygame.FINGERMOTION:
                if self.state == STATE_PLAYING:
                    self.joystick.handle_touch_move(event.finger_id, event.x, event.y)

            elif event.type == pygame.FINGERUP:
                if self.state == STATE_PLAYING:
                    self.joystick.handle_touch_up(event.finger_id)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state in (STATE_MENU, STATE_GAMEOVER, STATE_VICTORY):
                    self.init_game_session()
                    self.state = STATE_PLAYING
                elif self.state == STATE_PAUSED:
                    self.state = STATE_PLAYING

        return True

    def update(self, dt: float) -> None:
        """Updates physics, camera follow, keys, and A* enemy chase."""
        if self.state != STATE_PLAYING:
            return

        self.game_time += dt

        # Gather movement vector
        keys = pygame.key.get_pressed()
        vx = 0.0
        vy = 0.0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            vy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            vy += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vx += 1.0

        vx += self.joystick.vx
        vy += self.joystick.vy

        self.player.is_sprinting = keys[pygame.K_LSHIFT] or self.joystick.sprint_pressed
        self.player.update_motion(vx, vy, dt, self.dungeon.grid)

        # Smooth camera lerp
        target_cam_x = self.player.x * TILE_SIZE
        target_cam_y = self.player.y * TILE_SIZE
        self.camera_x += (target_cam_x - self.camera_x) * 0.12
        self.camera_y += (target_cam_y - self.camera_y) * 0.12

        # Key pickups
        for kpos in list(self.dungeon.key_positions):
            if math.hypot(self.player.x - kpos[0], self.player.y - kpos[1]) < 0.7:
                self.dungeon.key_positions.remove(kpos)
                self.player.keys_collected += 1
                self.player.score += 500
                self.audio.play_key()

        # Exit escape
        if self.player.keys_collected >= self.player.total_keys:
            ex, ey = self.dungeon.exit_pos
            if math.hypot(self.player.x - ex, self.player.y - ey) < 0.85:
                self.player.score += 2000 + int(max(0.0, 300.0 - self.game_time) * 10)
                self.is_new_best = self.highscores.record_run(self.player.score, self.game_time, True)
                self.state = STATE_VICTORY
                return

        # Enemy AI Update (30-frame throttled A*)
        caught = self.enemy.update(self.player.x, self.player.y, self.dungeon.grid, dt)
        if caught:
            self.player.health -= 60.0 * dt
            if self.player.health <= 0.0:
                self.is_new_best = self.highscores.record_run(self.player.score, self.game_time, False)
                self.audio.play_alert()
                self.state = STATE_GAMEOVER
                return

        # Proximity Heartbeat Audio
        dist = self.enemy.distance_to_player
        heartbeat_interval = max(0.22, min(1.4, dist * 0.11))
        self.heartbeat_timer += dt
        if self.heartbeat_timer >= heartbeat_interval:
            self.heartbeat_timer = 0.0
            if dist < 8.5:
                self.audio.play_heartbeat()

    def render(self) -> None:
        """Renders top-down viewport, dungeon tiles, entities, vector HUD, and overlays."""
        surface = self.screen
        sw, sh = surface.get_size()
        surface.fill(BG_COLOR)

        if self.state in (STATE_PLAYING, STATE_PAUSED):
            self._render_top_down_world(surface, sw, sh)
            self._render_hud(surface, sw, sh)
            if not self.full_map_mode:
                self._render_minimap(surface, sw, sh)
            self.joystick.render(surface)

            if self.state == STATE_PAUSED:
                overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                surface.blit(overlay, (0, 0))
                draw_vector_string(surface, "PAUSED", sw // 2 - 60, sh // 2 - 30, 20, 32, 6, (255, 200, 0), 3)
                draw_vector_string(surface, "TAP OR PRESS SPACE TO RESUME", sw // 2 - 190, sh // 2 + 30, 10, 16, 4, (200, 200, 200), 2)

        elif self.state == STATE_MENU:
            self._render_menu(surface, sw, sh)

        elif self.state == STATE_GAMEOVER:
            self._render_gameover(surface, sw, sh)

        elif self.state == STATE_VICTORY:
            self._render_victory(surface, sw, sh)

        pygame.display.flip()

    def _render_minimap(self, surface: pygame.Surface, sw: int, sh: int) -> None:
        """Renders small static 20x20 mini-map overlay in the corner during Follow View."""
        map_size = 96
        cell_size = map_size / GRID_WIDTH
        mx = sw - map_size - 16
        my = 16

        # Outer radar frame with drop shadow
        pygame.draw.rect(surface, (8, 11, 18), (mx - 4, my - 4, map_size + 8, map_size + 8), border_radius=6)
        pygame.draw.rect(surface, (6, 182, 212), (mx - 4, my - 4, map_size + 8, map_size + 8), 1, border_radius=6)

        # 20x20 Dungeon grid cells
        for gy in range(GRID_HEIGHT):
            for gx in range(GRID_WIDTH):
                cx = mx + gx * cell_size
                cy = my + gy * cell_size
                if self.dungeon.grid[gy][gx] == 1:
                    pygame.draw.rect(surface, (40, 50, 70), (cx, cy, cell_size + 0.5, cell_size + 0.5))
                else:
                    pygame.draw.rect(surface, (14, 18, 26), (cx, cy, cell_size + 0.5, cell_size + 0.5))

        # Exit portal dot
        ex, ey = self.dungeon.exit_pos
        pygame.draw.circle(surface, (16, 185, 129), (int(mx + ex * cell_size), int(my + ey * cell_size)), 2)

        # Keys dots
        for kx, ky in self.dungeon.key_positions:
            pygame.draw.circle(surface, (245, 158, 11), (int(mx + kx * cell_size), int(my + ky * cell_size)), 2)

        # Chasing beast enemy pulsing dot
        enx, eny = self.enemy.x, self.enemy.y
        pygame.draw.circle(surface, (239, 68, 68), (int(mx + enx * cell_size), int(my + eny * cell_size)), 3)

        # Player dot with direction pointer
        px, py = self.player.x, self.player.y
        center_px = int(mx + px * cell_size)
        center_py = int(my + py * cell_size)
        pygame.draw.circle(surface, (6, 182, 212), (center_px, center_py), 3)
        pygame.draw.circle(surface, (255, 255, 255), (center_px, center_py), 1)
        dir_x = int(center_px + math.cos(self.player.angle) * 6)
        dir_y = int(center_py + math.sin(self.player.angle) * 6)
        pygame.draw.line(surface, (255, 255, 255), (center_px, center_py), (dir_x, dir_y), 1)

    def _render_top_down_world(self, surface: pygame.Surface, sw: int, sh: int) -> None:
        """Renders the 20x20 dungeon from a realistic 3D top-down perspective."""
        if not self.full_map_mode:
            tile_s = TILE_SIZE
            ox = sw // 2 - int(self.camera_x)
            oy = sh // 2 - int(self.camera_y)
        else:
            tile_s = int(min(sw, sh) / (GRID_WIDTH + 1))
            ox = (sw - GRID_WIDTH * tile_s) // 2
            oy = (sh - GRID_HEIGHT * tile_s) // 2

        # 1. Render Tiles (Floors & Realistic 3D Walls)
        for gy in range(GRID_HEIGHT):
            for gx in range(GRID_WIDTH):
                rx = ox + gx * tile_s
                ry = oy + gy * tile_s

                # Frustum culling
                if rx + tile_s < 0 or rx > sw or ry + tile_s < 0 or ry > sh:
                    continue

                if self.dungeon.grid[gy][gx] == 0:
                    # Floor corridor with flagstone pavers
                    pygame.draw.rect(surface, FLOOR_COLOR, (rx, ry, tile_s, tile_s))
                    pygame.draw.rect(surface, FLOOR_BORDER, (rx, ry, tile_s, tile_s), 1)
                else:
                    # Realistic 3D Wall: Drop shadow on adjacent floors
                    if gy + 1 < GRID_HEIGHT and self.dungeon.grid[gy + 1][gx] == 0:
                        pygame.draw.rect(surface, (12, 14, 20), (rx, ry + tile_s, tile_s, max(2, tile_s // 8)))
                    if gx + 1 < GRID_WIDTH and self.dungeon.grid[gy][gx + 1] == 0:
                        pygame.draw.rect(surface, (12, 14, 20), (rx + tile_s, ry, max(2, tile_s // 8), tile_s))

                    # Solid 3D Beveled Stone Wall Top
                    pygame.draw.rect(surface, WALL_TOP, (rx, ry, tile_s, tile_s))
                    # Top-left specular highlight
                    pygame.draw.line(surface, (85, 100, 130), (rx, ry), (rx + tile_s - 1, ry), 1)
                    pygame.draw.line(surface, (85, 100, 130), (rx, ry), (rx, ry + tile_s - 1), 1)

                    # 3D Wall Front Edge Extrusion
                    face_h = int(tile_s * 0.28)
                    pygame.draw.rect(surface, WALL_FACE, (rx, ry + tile_s - face_h, tile_s, face_h))
                    pygame.draw.line(surface, (100, 120, 155), (rx, ry + tile_s - face_h), (rx + tile_s - 1, ry + tile_s - face_h), 1)
                    pygame.draw.rect(surface, WALL_BORDER, (rx, ry, tile_s, tile_s), 1)

        # 2. Render Exit Portal
        ex = ox + int(self.dungeon.exit_pos[0] * tile_s)
        ey = oy + int(self.dungeon.exit_pos[1] * tile_s)
        portal_ready = self.player.keys_collected >= self.player.total_keys
        portal_col = EXIT_COLOR if portal_ready else (70, 85, 105)
        pygame.draw.circle(surface, portal_col, (ex, ey), int(tile_s * 0.42), 3)
        pygame.draw.circle(surface, portal_col, (ex, ey), int(tile_s * 0.25))

        # 3. Render Relic Keys
        for kpos in self.dungeon.key_positions:
            kx = ox + int(kpos[0] * tile_s)
            ky = oy + int(kpos[1] * tile_s)
            pygame.draw.circle(surface, (255, 180, 0), (kx, ky), int(tile_s * 0.3), 1)
            pygame.draw.circle(surface, KEY_COLOR, (kx, ky), int(tile_s * 0.18))

        # 4. Render Chasing Enemy (Shadow Beast)
        enx = ox + int(self.enemy.x * tile_s)
        eny = oy + int(self.enemy.y * tile_s)
        beast_r = int(tile_s * 0.36)

        # Crimson terror aura
        pygame.draw.circle(surface, (120, 20, 20), (enx, eny), int(beast_r * 1.5), 1)

        # Beast diamond body oriented towards travel direction
        cos_e = math.cos(self.enemy.angle)
        sin_e = math.sin(self.enemy.angle)
        pts_e = [
            (enx + int(beast_r * 1.2 * cos_e), eny + int(beast_r * 1.2 * sin_e)),
            (enx - int(beast_r * 0.8 * cos_e - beast_r * sin_e), eny - int(beast_r * 0.8 * sin_e + beast_r * cos_e)),
            (enx - int(beast_r * 0.4 * cos_e), eny - int(beast_r * 0.4 * sin_e)),
            (enx - int(beast_r * 0.8 * cos_e + beast_r * sin_e), eny - int(beast_r * 0.8 * sin_e - beast_r * cos_e)),
        ]
        pygame.draw.polygon(surface, (220, 38, 38), pts_e)
        pygame.draw.polygon(surface, (255, 150, 150), pts_e, 2)

        # 5. Render Player Character
        plx = ox + int(self.player.x * tile_s)
        ply = oy + int(self.player.y * tile_s)
        player_r = int(tile_s * 0.34)

        # Player torchlight halo
        pygame.draw.circle(surface, (20, 60, 80), (plx, ply), int(player_r * 1.6), 1)

        # Player avatar circle
        pygame.draw.circle(surface, (6, 182, 212), (plx, ply), player_r)
        pygame.draw.circle(surface, (255, 255, 255), (plx, ply), player_r, 2)

        # Directional facing pointer
        p_dx = math.cos(self.player.angle) * (player_r + 5)
        p_dy = math.sin(self.player.angle) * (player_r + 5)
        pygame.draw.line(surface, (255, 255, 255), (plx, ply), (int(plx + p_dx), int(ply + p_dy)), 3)

    def _render_hud(self, surface: pygame.Surface, sw: int, sh: int) -> None:
        """Renders vector HP, Stamina, Keys, and Threat Proximity."""
        # Health Bar
        draw_vector_icon(surface, "heart", 20, 20, 24, (255, 60, 60))
        draw_vector_bar(surface, 52, 22, 140, 18, self.player.health, self.player.max_health, (220, 40, 40))

        # Stamina Bar
        draw_vector_icon(surface, "stamina", 20, 48, 24, (255, 180, 0))
        draw_vector_bar(surface, 52, 50, 140, 14, self.player.stamina, self.player.max_stamina, (255, 160, 20))

        # Keys
        draw_vector_icon(surface, "key", 20, 72, 22, (255, 215, 0))
        key_str = f"{self.player.keys_collected}/{self.player.total_keys}"
        draw_vector_string(surface, key_str, 52, 74, 10, 16, 4, (255, 215, 0), 2)

        # Enemy Threat Indicator
        threat_dist = self.enemy.distance_to_player
        threat_color = (255, 40, 40) if threat_dist < 4.0 else ((255, 140, 0) if threat_dist < 8.0 else (80, 80, 100))
        draw_vector_icon(surface, "skull", sw // 2 - 12, 18, 24, threat_color)

    def _render_menu(self, surface: pygame.Surface, sw: int, sh: int) -> None:
        surface.fill((10, 12, 18))
        pygame.draw.rect(surface, (40, 50, 70), (16, 16, sw - 32, sh - 32), 2)
        pygame.draw.rect(surface, (25, 30, 45), (22, 22, sw - 44, sh - 44), 1)

        title_y = sh // 4 - 30
        draw_vector_string(surface, "TOP DOWN DUNGEON CHASE", sw // 2 - 250, title_y, 16, 28, 5, (6, 182, 212), 3)
        draw_vector_string(surface, "ESCAPE THE LABYRINTH", sw // 2 - 140, title_y + 45, 10, 16, 4, (200, 200, 220), 2)

        btn_w, btn_h = 240, 46
        btn_x = sw // 2 - btn_w // 2
        btn_y = sh // 2
        pygame.draw.rect(surface, (20, 60, 80), (btn_x, btn_y, btn_w, btn_h), border_radius=8)
        pygame.draw.rect(surface, (6, 182, 212), (btn_x, btn_y, btn_w, btn_h), 2, border_radius=8)
        draw_vector_string(surface, "TAP TO START", btn_x + 36, btn_y + 12, 12, 20, 4, (255, 255, 255), 2)

        best_sc = self.highscores.data.get("best_score", 0)
        draw_vector_string(surface, f"HIGH SCORE: {best_sc}", sw // 2 - 90, btn_y + 65, 10, 16, 4, (255, 215, 0), 2)

        # Difficulty indicator badge
        diff_col = (50, 220, 120) if self.difficulty == "EASY" else ((255, 180, 0) if self.difficulty == "NORMAL" else (255, 60, 60))
        draw_vector_string(surface, f"DIFFICULTY: {self.difficulty} (PRESS D)", sw // 2 - 160, btn_y + 95, 8, 14, 3, diff_col, 2)

        hint_y = sh - 45
        draw_vector_string(surface, "WASD MOVE  SHIFT SPRINT  M MAP VIEW", sw // 2 - 190, hint_y, 8, 14, 3, (130, 140, 160), 1)

    def _render_gameover(self, surface: pygame.Surface, sw: int, sh: int) -> None:
        surface.fill((20, 8, 8))
        pygame.draw.rect(surface, (120, 20, 20), (20, 20, sw - 40, sh - 40), 2)

        draw_vector_icon(surface, "skull", sw // 2 - 24, sh // 3 - 50, 48, (255, 40, 40))
        draw_vector_string(surface, "YOU WERE CAUGHT", sw // 2 - 150, sh // 3 + 20, 16, 26, 5, (255, 50, 50), 3)

        draw_vector_string(surface, f"SCORE: {self.player.score}", sw // 2 - 70, sh // 2 + 10, 12, 20, 4, (255, 255, 255), 2)
        surv_str = f"SURVIVED: {int(self.game_time)}S"
        draw_vector_string(surface, surv_str, sw // 2 - 75, sh // 2 + 40, 10, 16, 4, (200, 200, 200), 2)

        draw_vector_string(surface, "TAP OR PRESS SPACE TO RETRY", sw // 2 - 165, sh - 70, 10, 16, 3, (255, 200, 0), 2)

    def _render_victory(self, surface: pygame.Surface, sw: int, sh: int) -> None:
        surface.fill((8, 24, 16))
        pygame.draw.rect(surface, (40, 180, 100), (20, 20, sw - 40, sh - 40), 2)

        draw_vector_string(surface, "DUNGEON ESCAPED", sw // 2 - 160, sh // 3 - 20, 16, 28, 5, (50, 255, 140), 3)
        draw_vector_string(surface, f"FINAL SCORE: {self.player.score}", sw // 2 - 110, sh // 2, 12, 20, 4, (255, 255, 255), 2)
        time_str = f"ESCAPE TIME: {int(self.game_time)}S"
        draw_vector_string(surface, time_str, sw // 2 - 95, sh // 2 + 35, 10, 16, 4, (220, 240, 220), 2)

        draw_vector_string(surface, "TAP OR PRESS SPACE FOR NEXT RUN", sw // 2 - 180, sh - 70, 10, 16, 3, (255, 215, 0), 2)

    def run(self) -> None:
        """Main game loop ticking at capped 60 FPS."""
        running = True
        while running:
            dt = min(self.clock.tick(TARGET_FPS) / 1000.0, 0.05)
            running = self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    game = DungeonGame()
    game.run()
