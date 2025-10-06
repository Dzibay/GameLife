import pygame
import random
import math

# --- Константы и Настройки ---
# Экран
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GRID_WIDTH = 100
GRID_HEIGHT = 60
TILE_SIZE = 8
UI_PANEL_WIDTH = 280
GAME_WORLD_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH

# Цвета
COLORS = {
    'water': (50, 150, 255),
    'food': (50, 200, 50),
    'wood': (140, 90, 40),
    'stone': (130, 130, 130),
    'human': (255, 255, 0),
    'tribe': (200, 0, 200),
    'city': (220, 220, 220),
    'background': (10, 10, 10),
    'ui_background': (40, 40, 40),
    'text': (240, 240, 240),
    'war': (255, 0, 0),
    'peace': (0, 255, 0),
    'progress_bar_bg': (80, 80, 80),
    'progress_bar_fill': (100, 200, 255)
}
STATE_COLORS = [
    (0, 110, 230), (230, 110, 0), (0, 170, 0), (180, 0, 180),
    (230, 200, 0), (0, 180, 180)
]

# Параметры Симуляции
INITIAL_SPEED = 1
MAX_RESOURCE_PER_TILE = 1000
HUMAN_LIFESPAN = (60, 90) # в секундах
HUMAN_MAX_HUNGER = 100
HUMAN_MAX_THIRST = 100
HUMAN_INVENTORY_CAPACITY = 50
HUMAN_MERGE_RADIUS = 5
HUMAN_VISION_RADIUS = 10
TRIBE_CREATION_MEMBERS = 1
TRIBE_CREATION_RESOURCES = {'wood': 5, 'stone': 5}
TRIBE_MAX_POPULATION = 30
CITY_CREATION_RESOURCES = {'wood': 200, 'stone': 200}
CITY_MAX_POPULATION = 100
STATE_CREATION_RESOURCES = {'wood': 500, 'stone': 500}
STATE_EXPANSION_COST = {'wood': 100, 'stone': 100, 'food': 50}

# --- Вспомогательные функции ---
def get_distance(pos1, pos2):
    """Вычисляет расстояние между двумя точками."""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# --- Классы ---
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

class World:
    """Управляет всеми клетками (тайлами) мира."""
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.grid = [[Tile(x, y) for y in range(height)] for x in range(width)]

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]
        return None

    def get_neighbors(self, tile, radius=1):
        neighbors = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0: continue
                nx, ny = tile.x + dx, tile.y + dy
                neighbor_tile = self.get_tile(nx, ny)
                if neighbor_tile:
                    neighbors.append(neighbor_tile)
        return neighbors

    def draw(self, surface):
        for row in self.grid:
            for tile in row:
                tile.draw(surface)

class Human:
    """Автономный агент (человек)."""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = "searching_resource" # searching_resource, gathering, moving, merging
        self.hunger = 0
        self.thirst = 0
        self.age = 0
        self.lifespan = random.uniform(HUMAN_LIFESPAN[0], HUMAN_LIFESPAN[1])
        self.inventory = {'food': 5, 'water': 5, 'wood': 0, 'stone': 0}
        self.target = None
        self.path = []
        self.gathering_timer = 0

    def get_pos(self):
        return (self.x, self.y)

    def draw(self, surface):
        pos = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, COLORS['human'], pos, TILE_SIZE // 2)

    def update(self, world, humans, settlements, dt):
        self.age += dt
        self.hunger += 0.2 * dt
        self.thirst += 0.3 * dt

        if self.hunger >= HUMAN_MAX_HUNGER or self.thirst >= HUMAN_MAX_THIRST or self.age >= self.lifespan:
            self.die(humans)
            return

        self.consume_resources()
        self.run_ai(world, humans, settlements)

    def consume_resources(self):
        if self.hunger > 50 and self.inventory['food'] > 0:
            self.inventory['food'] -= 1
            self.hunger -= 30
        if self.thirst > 60 and self.inventory['water'] > 0:
            self.inventory['water'] -= 1
            self.thirst -= 40

    def find_best_target(self, world, humans):
        # Приоритеты: вода -> еда -> объединение -> ресурсы для племени
        if self.thirst > 70: return self.find_nearest_resource(world, 'water')
        if self.hunger > 60: return self.find_nearest_resource(world, 'food')

        # Поиск партнера для объединения
        if sum(self.inventory.values()) > 10:
            for other in humans:
                if other != self and get_distance(self.get_pos(), other.get_pos()) < HUMAN_MERGE_RADIUS:
                    self.state = "merging"
                    return other

        # Ресурсы для племени
        if self.inventory['wood'] < TRIBE_CREATION_RESOURCES['wood'] / TRIBE_CREATION_MEMBERS:
            return self.find_nearest_resource(world, 'wood')
        if self.inventory['stone'] < TRIBE_CREATION_RESOURCES['stone'] / TRIBE_CREATION_MEMBERS:
            return self.find_nearest_resource(world, 'stone')

        return self.find_nearest_resource(world, random.choice(['wood', 'stone']))

    def run_ai(self, world, humans, settlements):
        if self.state == "merging":
            if self.target and self.target in humans:
                if get_distance(self.get_pos(), self.target.get_pos()) > 1:
                    self.move_towards(self.target.get_pos())
                else:
                    self.state = "searching_resource"
                    self.target = None
            else:
                self.state = "searching_resource"
                self.target = None

        elif self.state in ["searching_resource", "moving"]:
            if self.target is None:
                self.target = self.find_best_target(world, humans)
                if self.target is None: return # Некуда идти
                self.path = []

            target_pos = self.target.get_pos() if isinstance(self.target, Human) else (self.target.x, self.target.y)

            if self.get_pos() == target_pos:
                if not isinstance(self.target, Human):
                    self.state = "gathering"
                    self.gathering_timer = 1 # 1 секунда на добычу
                else: # Дошли до цели (человека)
                    self.state = "searching_resource"
                    self.target = None
            else:
                self.state = "moving"
                self.move_towards(target_pos)

        elif self.state == "gathering":
            self.gathering_timer -= 1/60.0 # Используем 1/fps
            if self.gathering_timer <= 0:
                tile = world.get_tile(self.x, self.y)
                if tile and tile.resource_amount > 0:
                    resource = tile.resource_type
                    amount_gathered = min(5, tile.resource_amount)
                    
                    current_inv_total = sum(self.inventory.values())
                    if current_inv_total < HUMAN_INVENTORY_CAPACITY:
                        self.inventory[resource] += amount_gathered
                        tile.resource_amount -= amount_gathered
                
                self.state = "searching_resource"
                self.target = None

    def move_towards(self, target_pos):
        dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
        if abs(dx) > abs(dy):
            self.x += 1 if dx > 0 else -1
        elif dy != 0:
            self.y += 1 if dy > 0 else -1

    def find_nearest_resource(self, world, resource_type):
        best_tile = None
        min_dist = float('inf')
        for x in range(max(0, self.x - HUMAN_VISION_RADIUS), min(world.width, self.x + HUMAN_VISION_RADIUS)):
            for y in range(max(0, self.y - HUMAN_VISION_RADIUS), min(world.height, self.y + HUMAN_VISION_RADIUS)):
                tile = world.grid[x][y]
                if tile.resource_type == resource_type and tile.resource_amount > 0:
                    dist = get_distance((self.x, self.y), (x, y))
                    if dist < min_dist:
                        min_dist = dist
                        best_tile = tile
        return best_tile

    def die(self, humans):
        # Передача ресурсов ближайшему
        closest_human = None
        min_dist = 5 # Радиус передачи
        for human in humans:
            if human == self: continue
            dist = get_distance(self.get_pos(), human.get_pos())
            if dist < min_dist:
                min_dist = dist
                closest_human = human
        
        if closest_human:
            for res, amount in self.inventory.items():
                closest_human.inventory[res] += amount
        
        if self in humans:
            humans.remove(self)

class Settlement:
    """Базовый класс для Племени, Города и Государства."""
    def __init__(self, x, y, members):
        self.x, self.y = x, y
        self.population = len(members)
        self.resources = {res: sum(h.inventory[res] for h in members) for res in ['food', 'water', 'wood', 'stone']}
        self.territory = []
        self.update_territory(None) # world будет передан позже

    def get_pos(self):
        return (self.x, self.y)

    def update_territory(self, world):
        pass # Переопределяется в дочерних классах
    
    def gather_resources(self, world):
        for tile in self.territory:
            main_res = tile.resource_type
            # Добыча основного ресурса
            amount = min(tile.resource_amount, 5) # Племя добывает по 5 за тик
            self.resources[main_res] = self.resources.get(main_res, 0) + amount
            tile.resource_amount -= amount
            # Добыча неосновных ресурсов
            for res_type in ['food', 'water', 'wood', 'stone']:
                if res_type != main_res:
                    amount = min(tile.resource_amount, 1) # 10% от 10, т.е. 1
                    self.resources[res_type] = self.resources.get(res_type, 0) + amount * 0.1 # Медленная добыча

    def update_population(self, dt):
        # Потребление
        food_needed = self.population * 0.1 * dt
        water_needed = self.population * 0.15 * dt
        
        if self.resources['food'] < food_needed or self.resources['water'] < water_needed:
            self.population -= 1 * dt # Население убывает
        else:
            self.resources['food'] -= food_needed
            self.resources['water'] -= water_needed

        # Рост
        if self.resources['food'] > self.population * 2 and self.resources['water'] > self.population * 2:
             if self.population < self.get_max_population():
                self.population += 0.5 * dt

    def get_max_population(self):
        return 0 # Переопределяется

    def update(self, world, dt):
        self.gather_resources(world)
        self.update_population(dt)


class Tribe(Settlement):
    def __init__(self, x, y, members):
        super().__init__(x, y, members)
        self.progress_to_city = 0

    def update_territory(self, world):
        if world:
            center_tile = world.get_tile(self.x, self.y)
            if center_tile:
                self.territory = [center_tile] + world.get_neighbors(center_tile)

    def draw(self, surface):
        pos = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, COLORS['tribe'], pos, TILE_SIZE)

    def get_max_population(self):
        return TRIBE_MAX_POPULATION
    
    def update(self, world, dt):
        super().update(world, dt)
        if not self.territory: self.update_territory(world)
        
        # Прогресс до города
        progress_gain = (self.population / TRIBE_MAX_POPULATION) + \
                        (self.resources['wood'] / CITY_CREATION_RESOURCES['wood']) + \
                        (self.resources['stone'] / CITY_CREATION_RESOURCES['stone'])
        self.progress_to_city += progress_gain * dt * 0.1

    def can_evolve(self):
        return self.population >= TRIBE_MAX_POPULATION and \
               self.resources['wood'] >= CITY_CREATION_RESOURCES['wood'] and \
               self.resources['stone'] >= CITY_CREATION_RESOURCES['stone']

class City(Tribe):
    def __init__(self, tribe):
        # Наследуем параметры от племени
        super().__init__(tribe.x, tribe.y, [])
        self.population = tribe.population
        self.resources = tribe.resources
        self.progress_to_state = 0
    
    def update_territory(self, world):
        if world:
            center_tile = world.get_tile(self.x, self.y)
            if center_tile:
                self.territory = [center_tile] + world.get_neighbors(center_tile, radius=2)

    def draw(self, surface):
        rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE * 2)
        rect.center = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.rect(surface, COLORS['city'], rect)

    def get_max_population(self):
        return CITY_MAX_POPULATION

    def update(self, world, dt):
        super().update(world, dt)
        # Прогресс до государства
        progress_gain = (self.population / CITY_MAX_POPULATION) + \
                        (self.resources['wood'] / STATE_CREATION_RESOURCES['wood']) + \
                        (self.resources['stone'] / STATE_CREATION_RESOURCES['stone'])
        self.progress_to_state += progress_gain * dt * 0.05
    
    def can_evolve(self):
        return self.population >= CITY_MAX_POPULATION and \
               self.resources['wood'] >= STATE_CREATION_RESOURCES['wood'] and \
               self.resources['stone'] >= STATE_CREATION_RESOURCES['stone']

class State(City):
    def __init__(self, city, color):
        super().__init__(city)
        self.population = city.population
        self.resources = city.resources
        self.color = color
        self.diplomacy = {} # {other_state: 'war'/'peace'}
        self.capacity = 150 # Базовая вместимость

    def update_territory(self, world):
        if world:
            if not self.territory: # Первоначальное создание
                center_tile = world.get_tile(self.x, self.y)
                if center_tile:
                    self.territory = [center_tile] + world.get_neighbors(center_tile, radius=3)
            for tile in self.territory:
                tile.owner_state = self
            self.capacity = 150 + len(self.territory) * 5

    def draw(self, surface): # Государство не рисует себя, оно окрашивает тайлы
        pass

    def get_max_population(self):
        return self.capacity

    def expand(self, world):
        if all(self.resources[res] >= cost for res, cost in STATE_EXPANSION_COST.items()):
            expandable_tiles = set()
            for tile in self.territory:
                for neighbor in world.get_neighbors(tile):
                    if neighbor not in self.territory and neighbor.owner_state is None:
                        expandable_tiles.add(neighbor)
            
            if expandable_tiles:
                new_tile = random.choice(list(expandable_tiles))
                self.territory.append(new_tile)
                new_tile.owner_state = self
                for res, cost in STATE_EXPANSION_COST.items():
                    self.resources[res] -= cost
                return True
        return False
    
    def update(self, world, dt, states):
        # Не вызываем super().update(), т.к. логика отличается
        if not self.territory: self.update_territory(world)
        self.gather_resources(world)
        self.update_population(dt)

        if self.population < 0:
            # Распад государства
            for tile in self.territory:
                tile.owner_state = None
            if self in states:
                states.remove(self)
            return

        # Попытка расширения раз в секунду
        if int(pygame.time.get_ticks() / 1000) % 2 == 0:
            self.expand(world)
        
        self.update_diplomacy(world, states)

    def get_strength(self):
        return self.population + sum(self.resources.values()) / 10

    def update_diplomacy(self, world, states):
        my_border_tiles = {t for t in self.territory if any(n not in self.territory for n in world.get_neighbors(t))}

        for other_state in states:
            if other_state == self: continue

            other_border_tiles = {t for t in other_state.territory if any(n not in other_state.territory for n in world.get_neighbors(t))}
            
            # Проверка соприкосновения
            is_neighbor = False
            for tile1 in my_border_tiles:
                for tile2 in other_border_tiles:
                    if get_distance((tile1.x, tile1.y), (tile2.x, tile2.y)) < 2:
                        is_neighbor = True
                        break
                if is_neighbor: break
            
            if is_neighbor:
                if other_state not in self.diplomacy:
                    # Новое знакомство - решение: война или мир
                    if self.get_strength() > other_state.get_strength() * 1.5:
                        self.diplomacy[other_state] = 'war'
                        other_state.diplomacy[self] = 'war'
                    else:
                        self.diplomacy[other_state] = 'peace'
                        other_state.diplomacy[self] = 'peace'
            else:
                if other_state in self.diplomacy:
                    del self.diplomacy[other_state] # Больше не соседи


# --- Основной класс игры ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Эволюция Цивилизации")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 14)
        self.big_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.world = World(GRID_WIDTH, GRID_HEIGHT)
        self.humans = []
        self.settlements = []
        self.states = []
        self.running = True
        self.paused = False
        self.game_speed = INITIAL_SPEED
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.selected_object = None

    def run(self):
        while self.running:
            self.handle_events()
            if not self.paused:
                for _ in range(self.game_speed):
                    self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                if event.key == pygame.K_RIGHT:
                    self.game_speed = min(self.game_speed * 2, 128)
                if event.key == pygame.K_LEFT:
                    self.game_speed = max(self.game_speed // 2, 1)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] > GAME_WORLD_WIDTH: # Клик по UI
                    # Проверка кнопок
                    if self.add_human_button_rect.collidepoint(mouse_pos):
                        self.add_human()
                else: # Клик по миру
                    grid_x = mouse_pos[0] // TILE_SIZE
                    grid_y = mouse_pos[1] // TILE_SIZE
                    self.selected_object = self.get_object_at(grid_x, grid_y)


    def get_object_at(self, x, y):
        # Проверяем поселения
        for s in self.settlements + self.states:
            if isinstance(s, State):
                tile = self.world.get_tile(x, y)
                if tile and tile.owner_state == s:
                    return s
            else: # Племя или город
                 if get_distance((x,y), s.get_pos()) <= 2:
                    return s
        # Проверяем людей
        for h in self.humans:
            if h.x == x and h.y == y:
                return h
        # Если ничего не нашли, возвращаем тайл
        return self.world.get_tile(x,y)

    def add_human(self):
        x, y = 10, 10
        # x = random.randint(0, GRID_WIDTH - 1)
        # y = random.randint(0, GRID_HEIGHT - 1)
        self.humans.append(Human(x, y))

    def update(self):
        dt = self.clock.get_time() / 1000.0 # Время в секундах

        # Обновление людей
        for human in list(self.humans):
            human.update(self.world, self.humans, self.settlements, dt)

        # Формирование племен
        self.check_for_tribe_formation()

        # Обновление поселений и государств
        new_settlements = []
        for settlement in list(self.settlements):
            if isinstance(settlement, State):
                 settlement.update(self.world, dt, self.states)
            else:
                 settlement.update(self.world, dt)
            
            # Эволюция
            if hasattr(settlement, 'can_evolve') and settlement.can_evolve():
                if isinstance(settlement, Tribe):
                    new_city = City(settlement)
                    new_settlements.append(new_city)
                elif isinstance(settlement, City):
                    available_colors = [c for c in STATE_COLORS if c not in [s.color for s in self.states]]
                    if available_colors:
                       new_state = State(settlement, random.choice(available_colors))
                       self.settlements.append(new_state) # Добавляем в основной список для рендеринга и т.д.
                       self.states.append(new_state)
            else:
                new_settlements.append(settlement)
        self.settlements = new_settlements

        # Убираем мертвых
        self.humans = [h for h in self.humans if h.hunger < HUMAN_MAX_HUNGER and h.thirst < HUMAN_MAX_THIRST and h.age < h.lifespan]
        self.settlements = [s for s in self.settlements if s.population > 0]
        self.states = [s for s in self.states if s.population > 0]


    def check_for_tribe_formation(self):
        to_remove = []
        checked_humans = set()
        for human in self.humans:
            if human in checked_humans: continue

            potential_group = [human]
            for other in self.humans:
                if other != human and get_distance(human.get_pos(), other.get_pos()) < HUMAN_MERGE_RADIUS:
                    potential_group.append(other)
            
            if len(potential_group) >= TRIBE_CREATION_MEMBERS:
                total_res = {res: sum(h.inventory[res] for h in potential_group) for res in ['wood', 'stone']}
                if total_res['wood'] >= TRIBE_CREATION_RESOURCES['wood'] and total_res['stone'] >= TRIBE_CREATION_RESOURCES['stone']:
                    
                    avg_x = int(sum(h.x for h in potential_group) / len(potential_group))
                    avg_y = int(sum(h.y for h in potential_group) / len(potential_group))
                    
                    new_tribe = Tribe(avg_x, avg_y, potential_group)
                    self.settlements.append(new_tribe)
                    
                    for member in potential_group:
                        to_remove.append(member)
                    
                    # Чтобы избежать двойного использования людей
                    for member in potential_group:
                        checked_humans.add(member)

        self.humans = [h for h in self.humans if h not in to_remove]


    def draw(self):
        self.screen.fill(COLORS['background'])
        
        # Игровой мир
        game_surface = self.screen.subsurface(pygame.Rect(0, 0, GAME_WORLD_WIDTH, SCREEN_HEIGHT))
        self.world.draw(game_surface)
        
        for settlement in self.settlements:
            settlement.draw(game_surface)
        
        for human in self.humans:
            human.draw(game_surface)
        
        self.draw_diplomacy(game_surface)
        
        # UI
        self.draw_ui()

        pygame.display.flip()
    
    def draw_diplomacy(self, surface):
        for state in self.states:
            for other, status in state.diplomacy.items():
                if status == 'war':
                    color = COLORS['war']
                elif status == 'peace':
                    color = COLORS['peace']
                else:
                    continue

                pygame.draw.line(surface, color, 
                                 (state.x * TILE_SIZE, state.y * TILE_SIZE),
                                 (other.x * TILE_SIZE, other.y * TILE_SIZE), 2)


    def draw_ui(self):
        ui_rect = pygame.Rect(GAME_WORLD_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLORS['ui_background'], ui_rect)
        
        y_pos = 20
        
        # Общая информация
        self.draw_text(f"Симуляция: {'Пауза' if self.paused else 'Идет'}", 20, y_pos)
        y_pos += 30
        self.draw_text(f"Скорость: x{self.game_speed}", 20, y_pos)
        y_pos += 30
        self.draw_text(f"Люди: {len(self.humans)}", 20, y_pos)
        y_pos += 25
        self.draw_text(f"Поселения: {len(self.settlements)}", 20, y_pos)
        y_pos += 25
        self.draw_text(f"Государства: {len(self.states)}", 20, y_pos)
        y_pos += 40

        # Кнопка добавления человека
        self.add_human_button_rect = pygame.Rect(GAME_WORLD_WIDTH + 20, y_pos, UI_PANEL_WIDTH - 40, 40)
        pygame.draw.rect(self.screen, (80, 80, 150), self.add_human_button_rect, border_radius=5)
        self.draw_text("Добавить человека", 30, y_pos + 10, center_on_button=self.add_human_button_rect)
        y_pos += 60

        # Информация о выбранном объекте
        if self.selected_object:
            pygame.draw.line(self.screen, COLORS['text'], (GAME_WORLD_WIDTH + 10, y_pos), (SCREEN_WIDTH - 10, y_pos))
            y_pos += 20
            
            obj = self.selected_object
            if isinstance(obj, Human):
                self.draw_text("Человек", 20, y_pos, font=self.big_font)
                y_pos += 25
                self.draw_text(f"Состояние: {obj.state}", 20, y_pos)
                y_pos += 20
                self.draw_text(f"Возраст: {int(obj.age)} / {int(obj.lifespan)}", 20, y_pos)
                y_pos += 20
                self.draw_text(f"Голод: {int(obj.hunger)}/{HUMAN_MAX_HUNGER}", 20, y_pos)
                y_pos += 20
                self.draw_text(f"Жажда: {int(obj.thirst)}/{HUMAN_MAX_THIRST}", 20, y_pos)
                y_pos += 25
                self.draw_text("Инвентарь:", 20, y_pos)
                y_pos += 20
                for res, amount in obj.inventory.items():
                    self.draw_text(f"  {res.capitalize()}: {amount}", 20, y_pos)
                    y_pos += 20
            
            elif isinstance(obj, State):
                self.draw_text("Государство", 20, y_pos, font=self.big_font)
                y_pos += 25
                self.draw_text(f"Население: {int(obj.population)} / {obj.capacity}", 20, y_pos)
                y_pos += 20
                self.draw_text(f"Территория: {len(obj.territory)} клеток", 20, y_pos)
                y_pos += 25
                self.draw_text("Ресурсы:", 20, y_pos)
                y_pos += 20
                for res, amount in obj.resources.items():
                    self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y_pos)
                    y_pos += 20
                y_pos += 10
                self.draw_text("Дипломатия:", 20, y_pos)
                y_pos += 20
                if not obj.diplomacy: self.draw_text("  Нет контактов", 20, y_pos)
                for other, status in obj.diplomacy.items():
                    self.draw_text(f"  Статус: {status.capitalize()}", 20, y_pos, color=COLORS[status])
                    y_pos += 20

            elif isinstance(obj, City):
                self.draw_text("Город", 20, y_pos, font=self.big_font)
                y_pos += 25
                self.draw_text(f"Население: {int(obj.population)}/{CITY_MAX_POPULATION}", 20, y_pos)
                y_pos += 20
                self.draw_progress_bar("Прогресс до Государства:", obj.progress_to_state / 10, y_pos) # Делим для наглядности
                y_pos += 35
                self.draw_text("Ресурсы:", 20, y_pos)
                y_pos += 20
                for res, amount in obj.resources.items():
                    self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y_pos)
                    y_pos += 20

            elif isinstance(obj, Tribe):
                self.draw_text("Племя", 20, y_pos, font=self.big_font)
                y_pos += 25
                self.draw_text(f"Население: {int(obj.population)}/{TRIBE_MAX_POPULATION}", 20, y_pos)
                y_pos += 20
                self.draw_progress_bar("Прогресс до Города:", obj.progress_to_city, y_pos)
                y_pos += 35
                self.draw_text("Ресурсы:", 20, y_pos)
                y_pos += 20
                for res, amount in obj.resources.items():
                    self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y_pos)
                    y_pos += 20
            
            elif isinstance(obj, Tile):
                self.draw_text("Клетка Мира", 20, y_pos, font=self.big_font)
                y_pos += 25
                self.draw_text(f"Координаты: ({obj.x}, {obj.y})", 20, y_pos)
                y_pos += 20
                self.draw_text(f"Ресурс: {obj.resource_type.capitalize()}", 20, y_pos)
                y_pos += 20
                self.draw_text(f"Количество: {int(obj.resource_amount)}", 20, y_pos)
                y_pos += 20
                if obj.owner_state:
                     self.draw_text("Владелец: Государство", 20, y_pos)
                else:
                     self.draw_text("Владелец: Нет", 20, y_pos)

    def draw_text(self, text, x_offset, y_pos, font=None, color=None, center_on_button=None):
        if font is None: font = self.font
        if color is None: color = COLORS['text']
        
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        
        if center_on_button:
            text_rect.center = center_on_button.center
        else:
            text_rect.topleft = (GAME_WORLD_WIDTH + x_offset, y_pos)
        
        self.screen.blit(text_surface, text_rect)
        
    def draw_progress_bar(self, label, progress, y_pos):
        self.draw_text(label, 20, y_pos)
        y_pos += 20
        progress = max(0, min(1, progress)) # Ограничение от 0 до 1
        
        bg_rect = pygame.Rect(GAME_WORLD_WIDTH + 20, y_pos, UI_PANEL_WIDTH - 40, 15)
        fill_rect = pygame.Rect(GAME_WORLD_WIDTH + 20, y_pos, (UI_PANEL_WIDTH - 40) * progress, 15)
        
        pygame.draw.rect(self.screen, COLORS['progress_bar_bg'], bg_rect, border_radius=3)
        pygame.draw.rect(self.screen, COLORS['progress_bar_fill'], fill_rect, border_radius=3)


game = Game()
game.run()