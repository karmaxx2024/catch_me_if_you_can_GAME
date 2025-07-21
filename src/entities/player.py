import pygame
import random

class Player:
    def __init__(self, x, y, sprites):
        self.grid_x = x
        self.grid_y = y
        self.x = x * CELL_SIZE
        self.y = y * CELL_SIZE
        self.sprites = sprites
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

    def place_block(self, maze):
        if self.block_cooldown > 0:
            return False

        if self.blocks > 0 and len(self.placed_blocks) < self.max_blocks:
            if maze[self.grid_y][self.grid_x] == 0 and (self.grid_x, self.grid_y) not in self.placed_blocks:
                self.placed_blocks.append((self.grid_x, self.grid_y))
                self.blocks -= 1
                self.block_cooldown = 30
                return True
        return False

    def throw_banana(self, bananas):
        if self.banana_cooldown > 0:
            return False

        if self.bananas > 0:
            bananas.append((self.grid_x, self.grid_y))
            self.bananas -= 1
            self.banana_cooldown = 30
            return True
        return False

    def start_mining(self, maze, blocks):
        directions = [(0, 1), (1, 0), (-1, 0)]  # Низ, право, лево

        for dx, dy in directions:
            target_x, target_y = self.grid_x + dx, self.grid_y + dy
            if 0 <= target_x < COLS and 0 <= target_y < ROWS:
                if (target_x, target_y) in blocks or maze[target_y][target_x] == 1:
                    self.mining_target = (target_x, target_y)
                    self.mining_time = 60
                    return True
        return False

    def update_mining(self, maze, blocks):
        if self.mining_time > 0:
            self.mining_time -= 1
            if self.mining_time <= 0 and self.mining_target:
                target_x, target_y = self.mining_target
                if (target_x, target_y) in blocks:
                    blocks.remove((target_x, target_y))
                    self.blocks += 1
                    if self.blocks > self.max_blocks:
                        self.blocks = self.max_blocks
                elif maze[target_y][target_x] == 1:
                    maze[target_y][target_x] = 0
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
            temp_img = self.sprites["player"].copy()
            temp_img.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(temp_img, (self.x + 5, self.y + 5))
        else:
            surface.blit(self.sprites["player"], (self.x + 5, self.y + 5))