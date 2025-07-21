# utils/sprites.py
import pygame
import os
import random

def load_sprite(name, size=None):
    # Получаем абсолютный путь к папке со спрайтами
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sprite_path = os.path.join(base_dir, "assets", "sprites", f"{name}.png")

    try:
        sprite = pygame.image.load(sprite_path).convert_alpha()
        if size:
            sprite = pygame.transform.scale(sprite, size)
        return sprite
    except FileNotFoundError:
        print(f"Error: Could not load sprite {name}.png from {sprite_path}")
        # Создаем временный спрайт, если файл не найден
        temp_sprite = pygame.Surface(size if size else (32, 32), pygame.SRCALPHA)
        temp_sprite.fill((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        return temp_sprite


def init_sprites(cell_size):
    sprites = {
        "player": load_sprite("player", (cell_size - 10, cell_size - 10)),
        "ghost": load_sprite("ghost", (cell_size - 10, cell_size - 10)),
        "ghost_angry": load_sprite("ghost_angry", (cell_size - 10, cell_size - 10)),
        "ghost_trapped": load_sprite("ghost_trapped", (cell_size - 10, cell_size - 10)),
        "banana": load_sprite("banana", (cell_size // 2, cell_size // 2)),
        "block": load_sprite("block", (cell_size, cell_size)),
        "wall": load_sprite("wall", (cell_size, cell_size))
    }
    return sprites