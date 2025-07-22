import pygame
import os
import sys
import random
from collections import deque
from utils.sprites import init_sprites

# ========== КОНСТАНТЫ ==========
CELL_SIZE = 64
COLS, ROWS = 12, 9
WIDTH, HEIGHT = COLS * CELL_SIZE, ROWS * CELL_SIZE
FPS = 60

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FLOOR_COLOR = (230, 230, 250)
GRID_COLOR = (200, 200, 200)
TEXT_COLOR = (255, 255, 255)
INDICATOR_BG = (50, 50, 50)

# Состояния игры
STATE_PLAYING = 0
STATE_WIN = 1
STATE_LOSE = 2


# ========== КЛАСС ИГРОКА ==========
class Player:
    def __init__(self, x, y, sprites):
        self.grid_x = x
        self.grid_y = y
        self.x = x * CELL_SIZE
        self.y = y * CELL_SIZE
        self.sprites = sprites
        self.bananas = 5
        self.blocks = 3
        self.trapped_ghosts = 0
        self.direction = "right"

    def move(self, dx, dy, maze):
        new_x = self.grid_x + dx
        new_y = self.grid_y + dy

        if 0 <= new_x < COLS and 0 <= new_y < ROWS and maze[new_y][new_x] != 1:
            self.grid_x = new_x
            self.grid_y = new_y
            self.x = new_x * CELL_SIZE
            self.y = new_y * CELL_SIZE

            # Обновляем направление для анимации
            if dx > 0:
                self.direction = "right"
            elif dx < 0:
                self.direction = "left"
            elif dy > 0:
                self.direction = "down"
            elif dy < 0:
                self.direction = "up"

            return True
        return False

    def place_block(self, maze, blocks):
        if self.blocks > 0 and maze[self.grid_y][self.grid_x] != 1:
            blocks.append((self.grid_x, self.grid_y))
            self.blocks -= 1
            return True
        return False

    def throw_banana(self, bananas):
        if self.bananas > 0:
            bananas.append((self.grid_x, self.grid_y, self.direction))
            self.bananas -= 1
            return True
        return False

    def mine_block(self, maze, blocks):
        # Проверяем, есть ли рядом стена или блок
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            x, y = self.grid_x + dx, self.grid_y + dy
            if 0 <= x < COLS and 0 <= y < ROWS:
                if maze[y][x] == 1 or (x, y) in blocks:
                    if maze[y][x] == 1:
                        maze[y][x] = 0  # Удаляем стену
                    else:
                        blocks.remove((x, y))  # Удаляем блок
                    self.blocks += 1
                    return True
        return False

    def draw(self, screen):
        screen.blit(self.sprites["player"], (self.x + 5, self.y + 5))


# ========== КЛАСС ПРИВИДЕНИЯ ==========
class Ghost:
    def __init__(self, maze, sprites):
        self.sprites = sprites
        self.state = "chase"  # chase, trapped, scared
        self.trapped_time = 0
        self.scared_time = 0

        # Находим случайную позицию для привидения
        while True:
            x = random.randint(0, COLS - 1)
            y = random.randint(0, ROWS - 1)
            if maze[y][x] != 1 and (x > 2 or y > 2):  # Не слишком близко к игроку
                self.grid_x = x
                self.grid_y = y
                self.x = x * CELL_SIZE
                self.y = y * CELL_SIZE
                break

    def update(self, maze, player, bananas, blocks):
        if self.state == "trapped":
            self.trapped_time -= 1
            if self.trapped_time <= 0:
                self.state = "chase"
            return

        if self.state == "scared":
            self.scared_time -= 1
            if self.scared_time <= 0:
                self.state = "chase"

        # Проверяем, не попало ли в привидение бананом
        for banana in bananas[:]:
            bx, by, _ = banana
            if bx == self.grid_x and by == self.grid_y:
                bananas.remove(banana)
                if self.state == "chase":
                    self.state = "scared"
                    self.scared_time = FPS * 3  # 3 секунды

        # Движение привидения
        if random.random() < 0.1:  # 10% chance to change direction
            self.move_random(maze)

        # Проверка столкновения с игроком
        if self.grid_x == player.grid_x and self.grid_y == player.grid_y:
            if self.state == "scared":
                self.state = "trapped"
                self.trapped_time = FPS * 5  # 5 секунд
                player.trapped_ghosts += 1
            elif self.state == "chase":
                return True  # Игрок пойман

        return False

    def move_random(self, maze):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy

            if 0 <= new_x < COLS and 0 <= new_y < ROWS and maze[new_y][new_x] != 1:
                self.grid_x = new_x
                self.grid_y = new_y
                self.x = new_x * CELL_SIZE
                self.y = new_y * CELL_SIZE
                break

    def draw(self, screen):
        if self.state == "trapped":
            screen.blit(self.sprites["ghost_trapped"], (self.x + 5, self.y + 5))
        elif self.state == "scared":
            screen.blit(self.sprites["ghost_angry"], (self.x + 5, self.y + 5))
        else:
            screen.blit(self.sprites["ghost"], (self.x + 5, self.y + 5))


# ========== КЛАСС БАНАНА ==========
class Banana:
    @staticmethod
    def update_bananas(bananas, maze, blocks):
        new_bananas = []
        for x, y, direction in bananas:
            if direction == "right":
                dx, dy = 1, 0
            elif direction == "left":
                dx, dy = -1, 0
            elif direction == "up":
                dx, dy = 0, -1
            else:
                dx, dy = 0, 1  # down

            new_x, new_y = x + dx, y + dy

            if 0 <= new_x < COLS and 0 <= new_y < ROWS and maze[new_y][new_x] != 1 and (new_x, new_y) not in blocks:
                new_bananas.append((new_x, new_y, direction))

        return new_bananas

    @staticmethod
    def draw_bananas(screen, bananas, sprites):
        for x, y, _ in bananas:
            screen.blit(sprites["banana"], (x * CELL_SIZE + CELL_SIZE // 4, y * CELL_SIZE + CELL_SIZE // 4))


# ========== ФУНКЦИИ ГЕНЕРАЦИИ ==========
def generate_maze():
    maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]

    # Создаем проходы
    for y in range(1, ROWS - 1):
        for x in range(1, COLS - 1):
            if random.random() < 0.7:  # 70% chance to have a floor
                maze[y][x] = 0

    # Гарантируем, что у игрока есть место для старта
    for y in range(2):
        for x in range(2):
            maze[y][x] = 0

    # Гарантируем проходимость лабиринта
    for y in range(ROWS):
        for x in range(COLS):
            if maze[y][x] == 0:
                # Проверяем, не изолирована ли клетка
                neighbors = 0
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < COLS and 0 <= ny < ROWS and maze[ny][nx] == 0:
                        neighbors += 1
                if neighbors == 0:
                    # Делаем проход
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < COLS and 0 <= ny < ROWS:
                            maze[ny][nx] = 0

    return maze


# ========== ФУНКЦИИ ОТРИСОВКИ ==========
def draw_maze(screen, maze, sprites):
    for y in range(ROWS):
        for x in range(COLS):
            if maze[y][x] == 1:
                screen.blit(sprites["wall"], (x * CELL_SIZE, y * CELL_SIZE))
            else:
                pygame.draw.rect(screen, FLOOR_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Рисуем сетку
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))


def draw_blocks(screen, blocks, sprites):
    for x, y in blocks:
        screen.blit(sprites["block"], (x * CELL_SIZE, y * CELL_SIZE))


def draw_ui(screen, player, font, game_state):
    # Панель с информацией
    pygame.draw.rect(screen, INDICATOR_BG, (0, HEIGHT - 30, WIDTH, 30))

    # Отображаем количество бананов и блоков
    banana_text = font.render(f"Бананы: {player.bananas}", True, TEXT_COLOR)
    block_text = font.render(f"Блоки: {player.blocks}", True, TEXT_COLOR)
    ghosts_text = font.render(f"Поймано: {player.trapped_ghosts}/3", True, TEXT_COLOR)

    screen.blit(banana_text, (10, HEIGHT - 25))
    screen.blit(block_text, (150, HEIGHT - 25))
    screen.blit(ghosts_text, (290, HEIGHT - 25))

    # Сообщения о победе/поражении
    if game_state == STATE_WIN:
        win_text = font.render("ПОБЕДА! Нажмите R для рестарта", True, WHITE)
        text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        pygame.draw.rect(screen, BLACK, text_rect.inflate(20, 20))
        screen.blit(win_text, text_rect)
    elif game_state == STATE_LOSE:
        lose_text = font.render("ПОРАЖЕНИЕ! Нажмите R для рестарта", True, WHITE)
        text_rect = lose_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        pygame.draw.rect(screen, BLACK, text_rect.inflate(20, 20))
        screen.blit(lose_text, text_rect)


# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ghost Trapper")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    # Инициализация игры
    sprites = init_sprites(CELL_SIZE)
    maze = generate_maze()
    player = Player(1, 1, sprites)
    ghosts = [Ghost(maze, sprites) for _ in range(2)]
    blocks = []
    bananas = []
    game_state = STATE_PLAYING

    # Основной игровой цикл
    running = True
    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if game_state == STATE_PLAYING:
                    if event.key == pygame.K_w:
                        player.move(0, -1, maze)
                    elif event.key == pygame.K_s:
                        player.move(0, 1, maze)
                    elif event.key == pygame.K_a:
                        player.move(-1, 0, maze)
                    elif event.key == pygame.K_d:
                        player.move(1, 0, maze)
                    elif event.key == pygame.K_SPACE:
                        player.place_block(maze, blocks)
                    elif event.key == pygame.K_b:
                        player.throw_banana(bananas)
                    elif event.key == pygame.K_m:
                        player.mine_block(maze, blocks)
                elif event.key == pygame.K_r:  # Рестарт
                    maze = generate_maze()
                    player = Player(1, 1, sprites)
                    ghosts = [Ghost(maze, sprites) for _ in range(2)]
                    blocks = []
                    bananas = []
                    game_state = STATE_PLAYING

        # Обновление игрового состояния
        if game_state == STATE_PLAYING:
            # Обновляем бананы
            bananas = Banana.update_bananas(bananas, maze, blocks)

            # Обновляем привидения
            for ghost in ghosts:
                if ghost.update(maze, player, bananas, blocks):
                    game_state = STATE_LOSE

            # Проверка победы
            if player.trapped_ghosts >= 3:
                game_state = STATE_WIN

        # Отрисовка
        screen.fill(BLACK)
        draw_maze(screen, maze, sprites)
        draw_blocks(screen, blocks, sprites)
        Banana.draw_bananas(screen, bananas, sprites)

        for ghost in ghosts:
            ghost.draw(screen)

        player.draw(screen)
        draw_ui(screen, player, font, game_state)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()