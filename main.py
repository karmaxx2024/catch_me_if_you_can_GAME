import pygame
import random
import sys
from collections import deque

# Инициализация Pygame
pygame.init()

# Размеры экрана
CELL_SIZE = 64
COLS, ROWS = 12, 9
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ghost Trapper - Охота за привидениями")

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WALL_COLOR = (100, 100, 100)
WALL_BORDER = (70, 70, 70)
FLOOR_COLOR = (230, 230, 250)
PLAYER_COLOR = (0, 255, 0)
GHOST_COLOR = (255, 0, 0)
BANANA_COLOR = (255, 255, 0)
BLOCK_COLOR = (0, 0, 255)
GRID_COLOR = (200, 200, 200)
TEXT_COLOR = (255, 255, 255)
INDICATOR_BG = (50, 50, 50)
TRAPPED_GHOST_COLOR = (150, 0, 0)
ANGRY_GHOST_COLOR = (255, 100, 100)

# Создание спрайтов
def create_sprite(color, size, border_radius=0):
    sprite = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(sprite, color, (2, 2, size - 4, size - 4), border_radius=border_radius)
    darker = tuple(max(c - 40, 0) for c in color)
    pygame.draw.rect(sprite, darker, (2, 2, size - 4, size - 4), 2, border_radius=border_radius)
    return sprite

player_img = create_sprite(PLAYER_COLOR, CELL_SIZE - 10, 10)
ghost_img = create_sprite(GHOST_COLOR, CELL_SIZE - 10, 20)
trapped_ghost_img = create_sprite(TRAPPED_GHOST_COLOR, CELL_SIZE - 10, 20)
angry_ghost_img = create_sprite(ANGRY_GHOST_COLOR, CELL_SIZE - 10, 20)
banana_img = create_sprite(BANANA_COLOR, CELL_SIZE // 2, 5)
block_img = create_sprite(BLOCK_COLOR, CELL_SIZE, 5)

# Генерация лабиринта
def generate_maze():
    maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]
    stack = [(1, 1)]
    maze[1][1] = 0
    while stack:
        x, y = stack[-1]
        neighbors = []
        for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
            nx, ny = x + dx, y + dy
            if 0 < nx < COLS - 1 and 0 < ny < ROWS - 1 and maze[ny][nx] == 1:
                neighbors.append((dx, dy))
        if neighbors:
            dx, dy = random.choice(neighbors)
            wall_x, wall_y = x + dx // 2, y + dy // 2
            maze[wall_y][wall_x] = 0
            maze[y + dy][x + dx] = 0
            stack.append((x + dx, y + dy))
        else:
            stack.pop()
    # Добавляем случайные проходы
    for _ in range(5):
        x, y = random.randint(1, COLS - 2), random.randint(1, ROWS - 2)
        maze[y][x] = 0
    return maze

# Класс игрока
class Player:
    def __init__(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.x = x * CELL_SIZE
        self.y = y * CELL_SIZE
        self.bananas = 5
        self.blocks = 3
        self.max_blocks = 10
        self.placed_blocks = []
        self.rect = pygame.Rect(self.x + 5, self.y + 5, CELL_SIZE - 10, CELL_SIZE - 10)
        self.mining_time = 0
        self.mining_target = None
        self.move_cooldown = 0
        self.banana_cooldown = 0
        self.block_cooldown = 0
        self.health = 3
        self.invincible = 0

    def move(self, dx, dy, maze):
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return False
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy
        if 0 <= new_x < COLS and 0 <= new_y < ROWS and maze[new_y][new_x] == 0:
            self.grid_x, self.grid_y = new_x, new_y
            self.x, self.y = new_x * CELL_SIZE, new_y * CELL_SIZE
            self.rect.x, self.rect.y = self.x + 5, self.y + 5
            self.move_cooldown = 10
            return True
        return False

    def place_block(self, maze, blocks):
        if self.block_cooldown > 0 or self.blocks <= 0:
            return False
        target_pos = (self.grid_x, self.grid_y)
        if maze[self.grid_y][self.grid_x] == 0 and target_pos not in blocks:
            blocks.append(target_pos)
            self.blocks -= 1
            self.block_cooldown = 30
            return True
        return False

    def throw_banana(self, bananas):
        if self.banana_cooldown > 0 or self.bananas <= 0:
            return False
        if any(pos == (self.grid_x, self.grid_y) for pos in bananas):
            return False
        bananas.append((self.grid_x, self.grid_y))
        self.bananas -= 1
        self.banana_cooldown = 30
        return True

    def start_mining(self, maze, blocks):
        directions = [(0, 1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            tx, ty = self.grid_x + dx, self.grid_y + dy
            if 0 <= tx < COLS and 0 <= ty < ROWS:
                if (tx, ty) in blocks or maze[ty][tx] == 1:
                    self.mining_target = (tx, ty)
                    self.mining_time = 60
                    return True
        return False

    def update_mining(self, maze, blocks):
        if self.mining_time > 0:
            self.mining_time -= 1
            if self.mining_time <= 0 and self.mining_target:
                tx, ty = self.mining_target
                if (tx, ty) in blocks:
                    blocks.remove((tx, ty))
                    self.blocks += 1
                    if self.blocks > self.max_blocks:
                        self.blocks = self.max_blocks
                elif maze[ty][tx] == 1:
                    maze[ty][tx] = 0
                self.mining_target = None
                return True
        return False

    def take_damage(self):
        if self.invincible <= 0:
            self.health -= 1
            self.invincible = 60
            return True
        return False

    def update(self, maze, blocks):
        if self.banana_cooldown > 0:
            self.banana_cooldown -= 1
        if self.block_cooldown > 0:
            self.block_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        self.update_mining(maze, blocks)

    def draw(self, surface):
        if self.invincible > 0 and self.invincible % 10 < 5:
            temp_img = player_img.copy()
            temp_img.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(temp_img, (self.x + 5, self.y + 5))
        else:
            surface.blit(player_img, (self.x + 5, self.y + 5))

# Класс привидения
class Ghost:
    def __init__(self, maze):
        while True:
            x = random.randint(1, COLS - 2)
            y = random.randint(1, ROWS - 2)
            if maze[y][x] == 0:
                self.grid_x = x
                self.grid_y = y
                self.x = x * CELL_SIZE
                self.y = y * CELL_SIZE
                break
        self.state = "chase"
        self.target_banana = None
        self.eat_time = 0
        self.break_time = 0
        self.rect = pygame.Rect(self.x + 5, self.y + 5, CELL_SIZE - 10, CELL_SIZE - 10)
        self.speed = 1
        self.move_timer = 0
        self.path = []
        self.last_player_pos = (0, 0)
        self.patrol_points = []
        self.current_patrol_index = 0
        self.anger = 0
        self.break_power = 1
        self.assigned_banana = None

    def find_path(self, maze, target_x, target_y, blocks):
        open_set = []
        closed_set = set()
        came_from = {}
        start = (self.grid_x, self.grid_y)
        open_set.append(start)
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, (target_x, target_y))}
        while open_set:
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            if current == (target_x, target_y):
                path = []
                while current in came_from:
                    prev = came_from[current]
                    path.append((current[0] - prev[0], current[1] - prev[1]))
                    current = prev
                path.reverse()
                return path
            open_set.remove(current)
            closed_set.add(current)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if not (0 <= neighbor[0] < COLS and 0 <= neighbor[1] < ROWS):
                    continue
                if maze[neighbor[1]][neighbor[0]] == 1:
                    continue
                if neighbor in blocks and neighbor not in self.path:
                    continue
                if neighbor in closed_set:
                    continue
                tentative_g_score = g_score[current] + 1
                if neighbor not in open_set:
                    open_set.append(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + self.heuristic(neighbor, (target_x, target_y))
        return []

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def check_bananas(self, bananas, all_ghosts):
        if self.assigned_banana in bananas:
            return
        for banana in bananas:
            if banana not in [g.assigned_banana for g in all_ghosts]:
                self.assigned_banana = banana
                self.state = "eat"
                self.eat_time = 60 // (self.anger + 1)
                break

    def panic_break_blocks(self, blocks):
        directions = [(0, 1), (1, 0), (-1, 0), (0, -1)]
        for dx, dy in directions:
            nearby = (self.grid_x + dx, self.grid_y + dy)
            if nearby in blocks:
                blocks.remove(nearby)
                self.break_power += 0.5
                break

    def update(self, maze, player, bananas, blocks, all_ghosts):
        if self.state == "trapped":
            return
        self.move_timer += 1
        if self.move_timer < 30 // max(1, self.speed + self.anger * 0.5):
            return
        self.move_timer = 0

        if self.state == "chase":
            if (player.grid_x, player.grid_y) != self.last_player_pos:
                self.last_player_pos = (player.grid_x, player.grid_y)
                self.path = self.find_path(maze, player.grid_x, player.grid_y, blocks)
            if not self.path:
                self.path = self.find_path(maze, player.grid_x, player.grid_y, blocks)
                if not self.path:
                    self.state = "patrol"
                    self.generate_patrol_points(maze)
        elif self.state == "patrol":
            self.patrol(maze, blocks)
        elif self.state == "eat":
            self.eat_time -= 1
            if self.eat_time <= 0:
                if self.assigned_banana in bananas:
                    bananas.remove(self.assigned_banana)
                self.assigned_banana = None
                self.state = "chase"
                self.anger += 1
                self.speed = 2 + self.anger
                self.panic_break_blocks(blocks)
        else:
            possible_moves = self.get_possible_moves(maze, blocks)
            if possible_moves:
                dx, dy = random.choice(possible_moves)
                self.move_ghost(dx, dy, maze, blocks)

        if self.state != "eat":
            self.check_bananas(bananas, all_ghosts)

        if self.check_trapped(blocks):
            return

    def get_possible_moves(self, maze, blocks):
        possible_moves = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if 0 <= new_x < COLS and 0 <= new_y < ROWS and maze[new_y][new_x] == 0:
                if (new_x, new_y) not in blocks or (new_x, new_y) in self.path:
                    possible_moves.append((dx, dy))
        return possible_moves

    def move_ghost(self, dx, dy, maze, blocks):
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy
        if 0 <= new_x < COLS and 0 <= new_y < ROWS and maze[new_y][new_x] == 0:
            if (new_x, new_y) not in blocks or (new_x, new_y) in self.path:
                self.grid_x = new_x
                self.grid_y = new_y
                self.x = new_x * CELL_SIZE
                self.y = new_y * CELL_SIZE
                self.rect.topleft = (self.x + 5, self.y + 5)

    def generate_patrol_points(self, maze):
        self.patrol_points = []
        for _ in range(3):
            while True:
                x = random.randint(1, COLS - 2)
                y = random.randint(1, ROWS - 2)
                if maze[y][x] == 0 and (x, y) != (self.grid_x, self.grid_y):
                    self.patrol_points.append((x, y))
                    break
        self.current_patrol_index = 0

    def patrol(self, maze, blocks):
        if not self.patrol_points:
            self.generate_patrol_points(maze)
            return
        target = self.patrol_points[self.current_patrol_index]
        if (self.grid_x, self.grid_y) == target:
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
            target = self.patrol_points[self.current_patrol_index]
        path = self.find_path(maze, *target, blocks)
        if path:
            dx, dy = path[0]
            self.move_ghost(dx, dy, maze, blocks)
        else:
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

    def check_trapped(self, blocks):
        if (self.grid_x, self.grid_y) in blocks:
            self.state = "trapped"
            return True
        return False

    def draw(self, surface):
        if self.state == "trapped":
            surface.blit(trapped_ghost_img, (self.x + 5, self.y + 5))
        elif self.state == "break" or self.anger > 0:
            surface.blit(angry_ghost_img, (self.x + 5, self.y + 5))
        else:
            surface.blit(ghost_img, (self.x + 5, self.y + 5))

# Функция для отрисовки стены
def draw_wall(surface, x, y):
    pygame.draw.rect(surface, WALL_COLOR, (x, y, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(surface, WALL_BORDER, (x, y, CELL_SIZE, CELL_SIZE), 2)
    pygame.draw.line(surface, (130, 130, 130), (x, y), (x + CELL_SIZE, y), 1)
    pygame.draw.line(surface, (130, 130, 130), (x, y), (x, y + CELL_SIZE), 1)

# Инициализация игры
def init_game():
    maze = generate_maze()
    player = Player(1, 1)
    ghosts = [Ghost(maze) for _ in range(2)]
    bananas = []
    blocks = []
    return maze, player, ghosts, bananas, blocks

# Главная функция игры
def main():
    maze, player, ghosts, bananas, blocks = init_game()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    game_over = False
    win = False
    score = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (game_over or win):
                    maze, player, ghosts, bananas, blocks = init_game()
                    game_over = False
                    win = False
                    score = 0
                elif event.key == pygame.K_SPACE and not game_over and not win:
                    if player.place_block(maze, blocks):
                        pass
                elif event.key == pygame.K_b and not game_over and not win:
                    if player.throw_banana(bananas):
                        pass
                elif event.key == pygame.K_m and not game_over and not win:
                    player.start_mining(maze, blocks)

        if not game_over and not win:
            keys = pygame.key.get_pressed()
            moved = False
            if keys[pygame.K_w]: moved = player.move(0, -1, maze)
            if keys[pygame.K_s]: moved = player.move(0, 1, maze)
            if keys[pygame.K_a]: moved = player.move(-1, 0, maze)
            if keys[pygame.K_d]: moved = player.move(1, 0, maze)
            if moved:
                for ghost in ghosts:
                    ghost.last_player_pos = (player.grid_x, player.grid_y)
                    ghost.path = ghost.find_path(maze, player.grid_x, player.grid_y, blocks)

            player.update(maze, blocks)

            for ghost in ghosts:
                if ghost.state != "trapped":
                    ghost.update(maze, player, bananas, blocks, ghosts)
                    if player.rect.colliderect(ghost.rect) and ghost.state != "eat":
                        if player.take_damage():
                            if player.health <= 0:
                                game_over = True

            trapped_ghosts = sum(1 for ghost in ghosts if ghost.check_trapped(blocks))
            if trapped_ghosts >= len(ghosts):
                win = True
                score += 100 * len(ghosts)

            if random.random() < 0.005 and len(bananas) < 5:
                while True:
                    x = random.randint(1, COLS - 2)
                    y = random.randint(1, ROWS - 2)
                    if maze[y][x] == 0 and (x, y) != (player.grid_x, player.grid_y) and (x, y) not in blocks:
                        bananas.append((x, y))
                        break

        screen.fill(BLACK)
        for y in range(ROWS):
            for x in range(COLS):
                if maze[y][x] == 0:
                    pygame.draw.rect(screen, FLOOR_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        for x in range(0, WIDTH, CELL_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, CELL_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)
        for y in range(ROWS):
            for x in range(COLS):
                if maze[y][x] == 1:
                    draw_wall(screen, x * CELL_SIZE, y * CELL_SIZE)
        for block in blocks:
            screen.blit(block_img, (block[0] * CELL_SIZE, block[1] * CELL_SIZE))
        for banana in bananas:
            screen.blit(banana_img, (banana[0] * CELL_SIZE + CELL_SIZE // 4, banana[1] * CELL_SIZE + CELL_SIZE // 4))
        player.draw(screen)
        for ghost in ghosts:
            ghost.draw(screen)

        pygame.draw.rect(screen, INDICATOR_BG, (10, 10, 200, 100), border_radius=5)
        bananas_text = font.render(f"Бананы: {player.bananas}", True, TEXT_COLOR)
        screen.blit(bananas_text, (20, 20))
        blocks_text = font.render(f"Блоки: {player.blocks}/{player.max_blocks}", True, TEXT_COLOR)
        screen.blit(blocks_text, (20, 50))
        health_text = font.render(f"Жизни: {player.health}", True, TEXT_COLOR)
        screen.blit(health_text, (20, 80))
        score_text = font.render(f"Очки: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (WIDTH - 150, 20))
        controls_text = small_font.render("Пробел: блок | B: банан | M: добыча", True, TEXT_COLOR)
        screen.blit(controls_text, (WIDTH - 250, HEIGHT - 30))

        if game_over:
            over_text = font.render("ИГРА ОКОНЧЕНА! Нажмите R для рестарта", True, (255, 0, 0))
            screen.blit(over_text, (WIDTH // 2 - 200, HEIGHT // 2))
        if win:
            win_text = font.render(f"ПОБЕДА! Очки: {score}", True, (0, 255, 0))
            screen.blit(win_text, (WIDTH // 2 - 150, HEIGHT // 2))
            restart_text = font.render("Нажмите R для рестарта", True, (0, 255, 0))
            screen.blit(restart_text, (WIDTH // 2 - 150, HEIGHT // 2 + 40))

        if player.mining_time > 0:
            progress = 60 - player.mining_time
            pygame.draw.rect(screen, (100, 100, 100), (player.x, player.y - 20, CELL_SIZE, 10))
            pygame.draw.rect(screen, (0, 255, 0), (player.x, player.y - 20, CELL_SIZE * progress / 60, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()