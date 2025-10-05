# -*- coding: utf-8 -*-

# Настройки экрана
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 30
TITLE = "Civilization Evolution"

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_GREEN = (144, 238, 144)
GRAY = (128, 128, 128)
BROWN = (165, 42, 42)
CYAN = (0, 255, 255)
SILVER = (192, 192, 192)


# Настройки мира
TILE_SIZE = 16
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE
RESOURCE_SPAWN_CHANCE = 0.5
RESOURCE_SPAWN_RATE = 1

# Типы ресурсов и их цвета
RESOURCES = {
    "food": ((180, 220, 180), 5),
    "water": ((150, 200, 255), 5),
    "wood": ((200, 180, 150), 10),
    "stone": ((190, 190, 190), 10)
}

# Настройки человека
PERSON_RADIUS = 4
PERSON_COLOR = YELLOW
PERSON_SPEED = 1
PERSON_LIFESPAN = 2000  # в тиках
PERSON_HUNGER_RATE = 0.05
PERSON_REPRODUCE_THRESHOLD = 50
PERSON_REPRODUCE_COOLDOWN = 200
PERSON_FOUND_SETTLEMENT_RADIUS = 100

# Настройки эволюции
TRIBE_FORMATION_POPULATION = 2
TRIBE_FORMATION_RESOURCES = {"wood": 200, "stone": 10}
TRIBE_SIZE = TILE_SIZE
TRIBE_COLOR = (255, 165, 0) # Orange

CITY_EVOLUTION_POPULATION = 100
CITY_EVOLUTION_RESOURCES = {"wood": 2000, "stone": 100}
CITY_SIZE = TILE_SIZE * 2
CITY_COLOR = (128, 0, 128) # Purple

STATE_EVOLUTION_POPULATION = 500
STATE_EVOLUTION_RESOURCES = {"wood": 10000, "stone": 5000}
STATE_BASE_SIZE = TILE_SIZE * 3
STATE_RESOURCES_NEEDED_TO_EXPAND = {"wood": 10, "stone": 10}
STATE_COLORS = [
    (220, 20, 60),    # ярко-красный
    (65, 105, 225),   # ярко-синий
    (255, 140, 0),    # оранжевый
    (128, 0, 128),    # фиолетовый
    (0, 128, 0),      # зелёный
    (255, 215, 0),    # золотой
    (255, 20, 147),   # ярко-розовый
    (0, 206, 209),    # бирюзовый
    (139, 69, 19),    # коричневый
    (0, 0, 139)       # тёмно-синий
]

# Настройки взаимодействия государств
WAR_CHANCE = 0.5
