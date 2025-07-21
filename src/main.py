import pygame
import os
print("Current working directory:", os.getcwd())
print("Files in directory:", os.listdir('.'))
from config import CELL_SIZE, COLS, ROWS
import sys
import random
from collections import deque
from utils.sprites import init_sprites
from entities.player import Player
from entities.ghost import Ghost

# Инициализация Pygame
pygame.init()

# Константы игры
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


# Инициализация игры
def init_game(sprites):
    maze = generate_maze()
    player = Player(1, 1, sprites)
    ghosts = [Ghost(maze, sprites) for _ in range(2)]
    bananas = []
    blocks = []
    return maze, player, ghosts, bananas, blocks


# Главная функция игры
def main():
    # Настройка экрана
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ghost Trapper - Охота за привидениями")
    clock = pygame.time.Clock()

    # Загрузка ресурсов
    sprites = init_sprites(CELL_SIZE)
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)

    # Инициализация игры
    maze, player, ghosts, bananas, blocks = init_game(sprites)
    game_over = False
    win = False
    score = 0

    running = True
    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (game_over or win):
                    maze, player, ghosts, bananas, blocks = init_game(sprites)
                    game_over = False
                    win = False
                    score = 0
                elif event.key == pygame.K_SPACE and not game_over and not win:
                    if player.place_block(maze):
                        blocks.append((player.grid_x, player.grid_y))
                elif event.key == pygame.K_b and not game_over and not win:
                    if player.throw_banana(bananas):
                        pass
                elif event.key == pygame.K_m and not game_over and not win:
                    player.start_mining(maze, blocks)

        # Обновление игры
        if not game_over and not win:
            # Управление игроком
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]: player.move(0, -1, maze)
            if keys[pygame.K_s]: player.move(0, 1, maze)
            if keys[pygame.K_a]: player.move(-1, 0, maze)
            if keys[pygame.K_d]: player.move(1, 0, maze)

            player.update(maze, blocks)

            # Обновление привидений
            for ghost in ghosts:
                if ghost.state != "trapped":
                    ghost.update(maze, player, bananas, blocks)
                    if player.rect.colliderect(ghost.rect) and ghost.state != "eat":
                        if player.take_damage():
                            if player.health <= 0:
                                game_over = True

            # Проверка победы
            trapped_ghosts = sum(1 for ghost in ghosts if ghost.state == "trapped")
            if trapped_ghosts >= len(ghosts):
                win = True
                score += 100 * len(ghosts)

            # Спавн бананов
            if random.random() < 0.005 and len(bananas) < 5:
                while True:
                    x = random.randint(1, COLS - 2)
                    y = random.randint(1, ROWS - 2)
                    if maze[y][x] == 0 and (x, y) != (player.grid_x, player.grid_y) and (x, y) not in blocks:
                        bananas.append((x, y))
                        break

        # Отрисовка
        screen.fill(BLACK)

        # Отрисовка пола и сетки
        for y in range(ROWS):
            for x in range(COLS):
                if maze[y][x] == 0:
                    pygame.draw.rect(screen, FLOOR_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        for x in range(0, WIDTH, CELL_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, CELL_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)

        # Отрисовка стен
        for y in range(ROWS):
            for x in range(COLS):
                if maze[y][x] == 1:
                    screen.blit(sprites["wall"], (x * CELL_SIZE, y * CELL_SIZE))

        # Отрисовка блоков
        for block in blocks:
            screen.blit(sprites["block"], (block[0] * CELL_SIZE, block[1] * CELL_SIZE))

        # Отрисовка бананов
        for banana in bananas:
            screen.blit(sprites["banana"],
                        (banana[0] * CELL_SIZE + CELL_SIZE // 4,
                         banana[1] * CELL_SIZE + CELL_SIZE // 4))

        # Отрисовка игрока и привидений
        player.draw(screen)
        for ghost in ghosts:
            ghost.draw(screen)

        # Панель информации
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

        # Сообщения о конце игры
        if game_over:
            over_text = font.render("ИГРА ОКОНЧЕНА! Нажмите R для рестарта", True, (255, 0, 0))
            screen.blit(over_text, (WIDTH // 2 - 200, HEIGHT // 2))

        if win:
            win_text = font.render(f"ПОБЕДА! Очки: {score}", True, (0, 255, 0))
            screen.blit(win_text, (WIDTH // 2 - 150, HEIGHT // 2))
            restart_text = font.render("Нажмите R для рестарта", True, (0, 255, 0))
            screen.blit(restart_text, (WIDTH // 2 - 150, HEIGHT // 2 + 40))

        # Индикатор добычи
        if player.mining_time > 0:
            progress = 60 - player.mining_time
            pygame.draw.rect(screen, (100, 100, 100), (player.x, player.y - 20, CELL_SIZE, 10))
            pygame.draw.rect(screen, (0, 255, 0), (player.x, player.y - 20, CELL_SIZE * progress / 60, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()