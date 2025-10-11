import math

# --- Константы и Настройки ---
# Экран
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
UI_PANEL_WIDTH = 280
GAME_WORLD_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH

TILE_SIZE = 8
GRID_WIDTH = GAME_WORLD_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE



# Цвета
COLORS = {
    'water': (50, 150, 255),
    'food': (50, 200, 50),
    'wood': (140, 90, 40),
    'stone': (130, 130, 130),
    'human': (255, 255, 0),
    'group': (255, 165, 0),
    'tribe': (200, 0, 200),
    'city': (220, 220, 220),
    'background': (10, 10, 10),
    'ui_background': (40, 40, 40),
    'text': (240, 240, 240),
    'war': (255, 0, 0),
    'peace': (0, 255, 0),
    'destroyed': (0, 0, 0),
    'progress_bar_bg': (80, 80, 80),
    'progress_bar_fill': (100, 200, 255),
    'spawn_marker': (255, 255, 255, 150)
}

# Параметры Симуляции
INITIAL_SPEED = 1
TICK_STEP = 50
MAX_RESOURCE_PER_TILE = 100000

HUMAN_LIFESPAN = (60, 90) # в секундах
HUMAN_MAX_HUNGER = 10
HUMAN_MAX_THIRST = 10
HUMAN_INVENTORY_CAPACITY = 50
HUMAN_MERGE_RADIUS = 5
HUMAN_VISION_RADIUS = 10
HUMAN_GATHER_SPEED = 3

GROUP_CREATION_MEMBERS = 2
GROUP_JOIN_RADIUS = 4

TRIBE_CREATION_POPULATION = 10
TRIBE_CREATION_RESOURCES = {'wood': 50, 'stone': 50}
TRIBE_MAX_POPULATION = 30

CITY_CREATION_RESOURCES = {'wood': 500, 'stone': 500}
CITY_MAX_POPULATION = 1000

STATE_CREATION_RESOURCES = {'wood': 10000, 'stone': 10000}
STATE_EXPANSION_COST = {'wood': 2000, 'stone': 2000}
MAX_TECHNOLOGY_LVL = 100


# --- Вспомогательные функции ---
def get_distance(pos1, pos2):
    """Вычисляет расстояние между двумя точками."""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)