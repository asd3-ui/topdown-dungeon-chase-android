import random

def generate_level(level_num, width=24, height=24):
    # إنشاء متاهة مليئة بالجدران (1 = جدار، 0 = ممر، 2 = باب، 3 = مفتاح، 4 = مخرج)
    maze = [[1 for _ in range(width)] for _ in range(height)]
    
    # خوارزمية حفر المتاهة (DFS Backtracking مبسط)
    stack = [(1, 1)]
    maze[1][1] = 0
    
    while stack:
        cx, cy = stack[-1]
        neighbors = []
        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
            nx, ny = cx + dx, cy + dy
            if 0 < nx < width-1 and 0 < ny < height-1 and maze[ny][nx] == 1:
                neighbors.append((nx, ny, dx, dy))
                
        if neighbors:
            nx, ny, dx, dy = random.choice(neighbors)
            maze[cy + dy // 2][cx + dx // 2] = 0
            maze[ny][nx] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
            
    # إضافة بوابات ومفاتيح ومخرج حسب مستوى الصعوبة
    exit_x, exit_y = width - 2, height - 2
    maze[exit_y][exit_x] = 4 # مخرج للمستوى التالي
    
    # وضع مفتاح عشوائي
    placed_keys = 0
    while placed_keys < (level_num + 1):
        kx, ky = random.randint(1, width-2), random.randint(1, height-2)
        if maze[ky][kx] == 0:
            maze[ky][kx] = 3
            placed_keys += 1

    return maze, (1.5, 1.5), (float(exit_x + 0.5), float(exit_y + 0.5))
