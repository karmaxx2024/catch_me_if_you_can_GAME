import pygame
import random
import sys

# Инициализация Pygame
pygame.init()

# Размеры экрана
WIDTH, HEIGHT = 800, 600

# Подбираем количество столбцов и строк так, чтобы блоки 64x64 полностью влезали
CELL_SIZE = 64
COLS = WIDTH // CELL_SIZE  # 800//64 = 12 столбцов
ROWS = HEIGHT // CELL_SIZE  # 600//64 = 9 строк

# Корректируем размер окна под целое количество блоков
WIDTH = COLS * CELL_SIZE  # 12*64 = 768
HEIGHT = ROWS * CELL_SIZE  # 9*64 = 576

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Лабиринт с текстурой стен")

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WALL_COLOR = (100, 100, 100)  # Основной цвет стен
WALL_BORDER = (70, 70, 70)  # Цвет границы стен
GRID_COLOR = (200, 200, 200)  # Цвет сетки (если нужна)

# Создаем сетку лабиринта (1 - стена, 0 - проход)
maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]

# Направления для генерации (вверх, вправо, вниз, влево)
directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]


def generate_maze(start_row, start_col):
    stack = [(start_row, start_col)]
    maze[start_row][start_col] = 0  # Начальная точка

    while stack:
        current_row, current_col = stack[-1]
        neighbors = []

        # Проверяем соседей
        for dr, dc in directions:
            nr, nc = current_row + 2 * dr, current_col + 2 * dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] == 1:
                neighbors.append((dr, dc))

        if neighbors:
            # Выбираем случайного соседа
            dr, dc = random.choice(neighbors)
            wall_row, wall_col = current_row + dr, current_col + dc
            next_row, next_col = current_row + 2 * dr, current_col + 2 * dc

            # Убираем стену и перемещаемся
            maze[wall_row][wall_col] = 0
            maze[next_row][next_col] = 0
            stack.append((next_row, next_col))
        else:
            # Если нет соседей, возвращаемся
            stack.pop()


# Функция для отрисовки стены с текстурой (отдельный блок)
def draw_wall(surface, x, y, size):
    # Рисуем основу стены
    pygame.draw.rect(surface, WALL_COLOR, (x, y, size, size))
    # Рисуем границу (чтобы блок выглядел отдельно)
    pygame.draw.rect(surface, WALL_BORDER, (x, y, size, size), 2)
    # Добавляем "тень" для эффекта 3D
    pygame.draw.line(surface, (130, 130, 130), (x, y), (x + size, y), 1)
    pygame.draw.line(surface, (130, 130, 130), (x, y), (x, y + size), 1)


# Генерируем лабиринт
start_row, start_col = random.randint(0, ROWS // 2) * 2, random.randint(0, COLS // 2) * 2
generate_maze(start_row, start_col)

# Главный цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # Перегенерировать лабиринт по нажатию R
                maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]
                start_row, start_col = random.randint(0, ROWS // 2) * 2, random.randint(0, COLS // 2) * 2
                generate_maze(start_row, start_col)

    # Отрисовка
    screen.fill(WHITE)  # Белый фон для проходов

    # 1. Рисуем сетку (если нужна)
    for row in range(ROWS + 1):
        pygame.draw.line(screen, GRID_COLOR, (0, row * CELL_SIZE), (WIDTH, row * CELL_SIZE), 1)
    for col in range(COLS + 1):
        pygame.draw.line(screen, GRID_COLOR, (col * CELL_SIZE, 0), (col * CELL_SIZE, HEIGHT), 1)

    # 2. Рисуем стены с текстурой
    for row in range(ROWS):
        for col in range(COLS):
            if maze[row][col] == 1:
                draw_wall(screen, col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE)

    pygame.display.flip()

pygame.quit()
sys.exit()