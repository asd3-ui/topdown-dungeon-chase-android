import math
import pygame

class VirtualJoystick:
    def __init__(self, x, y, radius=60):
        self.base_x = x
        self.base_y = y
        self.radius = radius
        self.handle_x = x
        self.handle_y = y
        self.active = False
        self.touch_id = None

    def handle_event(self, event):
        if event.type == pygame.FINGERDOWN:
            sw, sh = pygame.display.get_surface().get_size()
            tx, ty = event.x * sw, event.y * sh
            if math.hypot(tx - self.base_x, ty - self.base_y) <= self.radius and not self.active:
                self.active = True
                self.touch_id = event.finger_id
                self.handle_x, self.handle_y = tx, ty
        elif event.type == pygame.FINGERMOTION and self.active:
            if event.finger_id == self.touch_id:
                sw, sh = pygame.display.get_surface().get_size()
                tx, ty = event.x * sw, event.y * sh
                angle = math.atan2(ty - self.base_y, tx - self.base_x)
                dist = min(math.hypot(tx - self.base_x, ty - self.base_y), self.radius)
                self.handle_x = self.base_x + math.cos(angle) * dist
                self.handle_y = self.base_y + math.sin(angle) * dist
        elif event.type == pygame.FINGERUP and self.active:
            if event.finger_id == self.touch_id:
                self.active = False
                self.touch_id = None
                self.handle_x = self.base_x
                self.handle_y = self.base_y

    def get_output(self):
        dx = (self.handle_x - self.base_x) / self.radius
        dy = (self.handle_y - self.base_y) / self.radius
        return dx, dy

    def draw(self, surface):
        pygame.draw.circle(surface, (80, 80, 80, 120), (self.base_x, self.base_y), self.radius, 3)
        pygame.draw.circle(surface, (180, 180, 180, 180), (int(self.handle_x), int(self.handle_y)), self.radius // 2)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.health = 100
        self.ammo = 30
        self.keys = 0
        self.score = 0

    def move(self, dx, dy, maze):
        # حركة محسنة مع تفادي التصادم بالجدران
        speed = 3.0
        # تحويل الاتجاهات بناءً على زاوية الرؤية للاعب
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        
        nx = self.x + (dx * cos_a - dy * sin_a) * 0.05
        ny = self.y + (dx * sin_a + dy * cos_a) * 0.05

        if maze[int(ny)][int(nx)] == 0 or maze[int(ny)][int(nx)] == 3:
            if maze[int(ny)][int(nx)] == 3:
                maze[int(ny)][int(nx)] = 0
                self.keys += 1
                self.score += 50
            self.x, self.y = nx, ny

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 50
        self.speed = 1.5

    def update(self, player_x, player_y, dt, maze):
        # مطاردة ذكية بسيطة للاعب
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0.3:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
