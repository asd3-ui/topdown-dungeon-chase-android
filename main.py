import sys
import math
import pygame
from maze_generator import generate_level
from entities import VirtualJoystick, Player, Enemy

def main():
    pygame.init()
    pygame.mixer.init()

    info = pygame.display.Info()
    sw = info.current_w if info.current_w > 0 else 960
    sh = info.current_h if info.current_h > 0 else 540
    screen = pygame.display.set_mode((sw, sh), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("Dungeon Raycast 3D Advanced")
    clock = pygame.time.Clock()

    current_level = 1
    maze, start_pos, exit_pos = generate_level(current_level)
    player = Player(start_pos[0], start_pos[1])
    enemies = [Enemy(10.5, 10.5), Enemy(15.5, 5.5)]

    joystick = VirtualJoystick(120, sh - 120, 55)
    turn_joystick = VirtualJoystick(sw - 120, sh - 120, 55)

    FOV = math.pi / 3
    HALF_FOV = FOV / 2
    NUM_RAYS = 120
    DELTA_ANGLE = FOV / NUM_RAYS
    MAX_DEPTH = 16

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            joystick.handle_event(event)
            turn_joystick.handle_event(event)

        # تحديث الحركة
        dx, dy = joystick.get_output()
        player.move(dx, dy, maze)

        tdx, _ = turn_joystick.get_output()
        player.angle += tdx * 0.05

        # التحقق من الوصول للمخرج للانتقال للمستوى التالي
        if math.hypot(player.x - exit_pos[0], player.y - exit_pos[1]) < 0.6:
            current_level += 1
            maze, start_pos, exit_pos = generate_level(current_level)
            player.x, player.y = start_pos
            enemies.append(Enemy(float(exit_pos[0]-2), float(exit_pos[1]-2)))

        # تحديث الأعداء
        for enemy in enemies:
            enemy.update(player.x, player.y, dt, maze)
            if math.hypot(player.x - enemy.x, player.y - enemy.y) < 0.5:
                player.health -= 10 * dt

        if player.health <= 0:
            # إعادة تشغيل سريعة عند الموت
            player.health = 100
            current_level = 1
            maze, start_pos, exit_pos = generate_level(current_level)
            player.x, player.y = start_pos

        # --- الرسم والتصيير (Raycasting Rendering) ---
        screen.fill((20, 20, 30)) # لون سماء افتراضي
        pygame.draw.rect(screen, (40, 40, 50), (0, sh // 2, sw, sh // 2)) # الأرضية

        # رسم الأشعة (Raycasting Walls)
        ray_angle = player.angle - HALF_FOV
        scale = sw / NUM_RAYS

        for ray in range(NUM_RAYS):
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            # خوارزمية تتبع الأشعة (DDA)
            depth = 0
            hit_wall = False
            while not hit_wall and depth < MAX_DEPTH:
                depth += 0.05
                test_x = int(player.x + depth * cos_a)
                test_y = int(player.y + depth * sin_a)

                if test_x < 0 or test_x >= len(maze[0]) or test_y < 0 or test_y >= len(maze):
                    hit_wall = True
                    depth = MAX_DEPTH
                elif maze[test_y][test_x] > 0:
                    hit_wall = True

            # تصحيح تأثير عين السمكة (Fish-eye correction)
            depth *= math.cos(player.angle - ray_angle)
            wall_height = min(int(sh / (depth + 0.0001)), sh * 2)

            # تظليل الجدران حسب المسافة لزيادة الواقعية
            color_factor = max(40, 255 - int(depth * 15))
            wall_color = (color_factor // 2, color_factor, color_factor // 3) if maze[test_y][test_x] == 4 else (color_factor, color_factor, color_factor)

            pygame.draw.rect(screen, wall_color, (ray * scale, (sh - wall_height) // 2, scale + 1, wall_height))
            ray_angle += DELTA_ANGLE

        # رسم الخريطة المصغرة (Minimap)
        map_scale = 6
        for my, row in enumerate(maze):
            for mx, tile in enumerate(row):
                if tile > 0:
                    color = (200, 50, 50) if tile == 4 else (100, 100, 100)
                    pygame.draw.rect(screen, color, (mx * map_scale + 20, my * map_scale + 20, map_scale, map_scale))
        pygame.draw.circle(screen, (0, 255, 0), (int(player.x * map_scale + 20), int(player.y * map_scale + 20)), 3)

        # واجهة المستخدم (UI HUD)
        font = pygame.font.SysFont(None, 28)
        health_txt = font.render(f"Health: {int(player.health)}", True, (255, 50, 50))
        level_txt = font.render(f"Level: {current_level}", True, (255, 255, 255))
        keys_txt = font.render(f"Keys: {player.keys}", True, (255, 215, 0))
        
        screen.blit(health_txt, (sw - 150, 20))
        screen.blit(level_txt, (sw - 150, 50))
        screen.blit(keys_txt, (sw - 150, 80))

        # رسم أدوات التحكم باللمس
        joystick.draw(screen)
        turn_joystick.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
