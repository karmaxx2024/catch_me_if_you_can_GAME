import pygame
import os
import random


def load_sprite(name, size=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sprite_path = os.path.join(base_dir, '..', 'assets', 'sprites', f'{name}.png')

    try:
        sprite = pygame.image.load(sprite_path).convert_alpha()
        return pygame.transform.scale(sprite, size) if size else sprite
    except FileNotFoundError:
        print(f"Warning: Missing sprite {name}.png")
        temp_sprite = pygame.Surface(size if size else (32, 32), pygame.SRCALPHA)
        temp_sprite.fill((random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
        return temp_sprite


def init_sprites(cell_size):
    return {
        "player": load_sprite("character_sword_Attack_0.png", (cell_size - 10, cell_size - 10)),
        "ghost": load_sprite("sprite_walk0.png", (cell_size - 10, cell_size - 10)),
        "ghost_angry": load_sprite("sprite_2.png", (cell_size - 10, cell_size - 10)),
        "ghost_trapped": load_sprite("sprite_atack4.png", (cell_size - 10, cell_size - 10)),
        "banana": load_sprite("lemon.png", (cell_size // 2, cell_size // 2)),
        "block": load_sprite("wall_image.png", (cell_size, cell_size)),
        "wall": load_sprite("wall_image.png", (cell_size, cell_size))
    }