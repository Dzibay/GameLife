import random
import pygame
from config import *

class Tile:
    """Представляет клетку мира."""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.resource_type = random.choice(['food', 'water', 'wood', 'stone'])
        self.resource_amount = random.randint(MAX_RESOURCE_PER_TILE // 2, MAX_RESOURCE_PER_TILE)
        self.color = COLORS[self.resource_type]
        self.rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.owner_state = None

    def draw(self, surface):
        if self.owner_state:
            color = self.owner_state.color
            pygame.draw.rect(surface, (int(color[0]*0.7), int(color[1]*0.7), int(color[2]*0.7)), self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)