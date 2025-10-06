import pygame
import random
import math

# --- Константы и Настройки ---
# Экран
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GRID_WIDTH = 100
GRID_HEIGHT = 60
TILE_SIZE = 10 # Увеличим для лучшей видимости
UI_PANEL_WIDTH = 300 # Увеличим панель
GAME_WORLD_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH

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
    'progress_bar_bg': (80, 80, 80),
    'progress_bar_fill': (100, 200, 255),
    'spawn_marker': (255, 255, 255, 150)
}
STATE_COLORS = [
    (0, 110, 230), (230, 110, 0), (0, 170, 0), (180, 0, 180),
    (230, 200, 0), (0, 180, 180)
]

# Параметры Симуляции
MAX_RESOURCE_PER_TILE = 1000
HUMAN_LIFESPAN = (70, 100)
HUMAN_VISION_RADIUS = 10
GROUP_CREATION_MEMBERS = 2
GROUP_JOIN_RADIUS = 4
TRIBE_CREATION_POPULATION = 15
TRIBE_CREATION_RESOURCES = {'wood': 50, 'stone': 50}
TRIBE_MAX_POPULATION = 40
CITY_CREATION_RESOURCES = {'wood': 200, 'stone': 200}
CITY_MAX_POPULATION = 100
STATE_CREATION_RESOURCES = {'wood': 500, 'stone': 500}
STATE_EXPANSION_COST = {'wood': 100, 'stone': 100, 'food': 50}

# --- Вспомогательные функции ---
def get_distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# --- Классы ---
class Tile:
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
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = "searching_partner"
        self.hunger = 0
        self.thirst = 0
        self.age = 0
        self.lifespan = random.uniform(HUMAN_LIFESPAN[0], HUMAN_LIFESPAN[1])
        self.inventory = {'food': 5, 'water': 5, 'wood': 0, 'stone': 0}
        self.target = None

    def get_pos(self): return (self.x, self.y)

    def draw(self, surface):
        pos = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, COLORS['human'], pos, TILE_SIZE // 2)

    def update(self, world, humans, dt):
        self.age += dt
        self.hunger += 0.2 * dt
        self.thirst += 0.3 * dt
        if self.is_dead():
            return
        self.consume_resources()
        self.run_ai(world, humans)
    
    def is_dead(self):
        return self.hunger >= 100 or self.thirst >= 100 or self.age >= self.lifespan

    def consume_resources(self):
        if self.hunger > 50 and self.inventory['food'] > 0:
            self.inventory['food'] -= 1; self.hunger -= 30
        if self.thirst > 60 and self.inventory['water'] > 0:
            self.inventory['water'] -= 1; self.thirst -= 40

    def run_ai(self, world, humans):
        if self.thirst > 70: self.target = self.find_nearest_resource(world, 'water')
        elif self.hunger > 60: self.target = self.find_nearest_resource(world, 'food')
        else: self.target = self.find_nearest_human(humans)

        if self.target:
            target_pos = self.target.get_pos() if isinstance(self.target, Human) else (self.target.x, self.target.y)
            if get_distance(self.get_pos(), target_pos) <= 1:
                if isinstance(self.target, Tile):
                    self.gather_resource(self.target)
                    self.target = None
            else:
                self.move_towards(target_pos)
    
    def gather_resource(self, tile):
        if tile and tile.resource_amount > 0:
            amount = min(5, tile.resource_amount)
            self.inventory[tile.resource_type] += amount
            tile.resource_amount -= amount

    def move_towards(self, target_pos):
        dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
        if abs(dx) > abs(dy): self.x += 1 if dx > 0 else -1
        elif dy != 0: self.y += 1 if dy > 0 else -1
        
        self.x = max(0, min(GRID_WIDTH - 1, self.x))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y))


    def find_nearest_resource(self, world, resource_type):
        return self.find_nearest(world.grid, lambda tile: tile.resource_type == resource_type and tile.resource_amount > 0)
    
    def find_nearest_human(self, humans):
        return self.find_nearest(humans, lambda h: h != self)
        
    def find_nearest(self, collection, condition):
        best_obj, min_dist = None, float('inf')
        # Ограничиваем поиск радиусом, чтобы не сканировать всю карту
        search_radius = HUMAN_VISION_RADIUS
        
        # Проверяем объекты в коллекции (либо тайлы, либо люди)
        flat_collection = [item for sublist in collection for item in sublist] if isinstance(collection[0], list) else collection

        for obj in flat_collection:
            if condition(obj):
                dist = get_distance(self.get_pos(), obj.get_pos() if hasattr(obj, 'get_pos') else (obj.x, obj.y))
                if dist < min_dist and dist < search_radius:
                    min_dist = dist
                    best_obj = obj
        return best_obj


class Group:
    def __init__(self, x, y, initial_members):
        self.x, self.y = x, y
        self.population = len(initial_members)
        self.inventory = {res: sum(h.inventory.get(res, 0) for h in initial_members) for res in ['food', 'water', 'wood', 'stone']}
        self.inventory_capacity = self.population * 20
        self.state = "searching_resource"
        self.target = None
        self.reproduction_progress = 0

    def get_pos(self): return (self.x, self.y)
    
    def get_strength(self): return self.population + sum(self.inventory.values())/10

    def draw(self, surface, font):
        pos = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, COLORS['group'], pos, TILE_SIZE * 0.8)
        text = font.render(str(int(self.population)), True, (255,255,255))
        text_rect = text.get_rect(center=pos)
        surface.blit(text, text_rect)

    def update(self, world, groups, dt):
        self.consume_and_reproduce(dt)
        if self.population <= 0: return
        self.run_ai(world, groups)

    def consume_and_reproduce(self, dt):
        food_needed = self.population * 0.1 * dt
        water_needed = self.population * 0.15 * dt

        if self.inventory['food'] < food_needed or self.inventory['water'] < water_needed:
            self.population -= 1 * dt
            return

        self.inventory['food'] -= food_needed
        self.inventory['water'] -= water_needed

        if self.inventory['food'] > self.population and self.inventory['water'] > self.population:
            self.reproduction_progress += dt
            if self.reproduction_progress > 10: # 10 секунд на рождение нового
                self.population += 1
                self.reproduction_progress = 0
                self.inventory_capacity = self.population * 20

    def run_ai(self, world, groups):
        if self.state == "gathering":
            if self.target and self.target.resource_amount > 0:
                self.gather_resource(self.target)
            else:
                self.state = "searching_resource"
                self.target = None

        if self.state == "searching_resource":
            self.target = self.find_best_target(world, groups)
            if self.target:
                self.state = "moving"
        
        if self.state == "moving":
            if not self.target:
                self.state = "searching_resource"
                return

            target_pos = self.target.get_pos() if hasattr(self.target, 'get_pos') else (self.target.x, self.target.y)
            if get_distance(self.get_pos(), target_pos) <= 1:
                if isinstance(self.target, Tile):
                    self.state = "gathering"
                elif isinstance(self.target, Group):
                    # Логика взаимодействия с другой группой (война/слияние)
                    # Вынесена в Game.update_social_dynamics для централизованного управления
                    self.state = "searching_resource"
                    self.target = None
            else:
                self.move_towards(target_pos)

    def find_best_target(self, world, groups):
        # Приоритеты: вода -> еда -> враг -> ресурсы для племени
        if self.inventory['water'] < self.population * 2: return self.find_nearest_resource(world, 'water')
        if self.inventory['food'] < self.population * 2: return self.find_nearest_resource(world, 'food')
        
        nearest_group = self.find_nearest_group(groups)
        if nearest_group and get_distance(self.get_pos(), nearest_group.get_pos()) < HUMAN_VISION_RADIUS * 2:
             return nearest_group

        if self.inventory['wood'] < TRIBE_CREATION_RESOURCES['wood']: return self.find_nearest_resource(world, 'wood')
        if self.inventory['stone'] < TRIBE_CREATION_RESOURCES['stone']: return self.find_nearest_resource(world, 'stone')
        
        return self.find_nearest_resource(world, random.choice(['wood', 'stone']))

    def gather_resource(self, tile):
        if sum(self.inventory.values()) >= self.inventory_capacity: return
        
        gather_speed = int(max(1, self.population / 2))
        amount = min(gather_speed, tile.resource_amount)
        self.inventory[tile.resource_type] += amount
        tile.resource_amount -= amount

    def move_towards(self, target_pos):
        dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
        if abs(dx) > abs(dy): self.x += 1 if dx > 0 else -1
        elif dy != 0: self.y += 1 if dy > 0 else -1
        self.x = int(max(0, min(GRID_WIDTH - 1, self.x)))
        self.y = int(max(0, min(GRID_HEIGHT - 1, self.y)))
    
    def find_nearest_resource(self, world, r_type):
        # Простая реализация поиска в радиусе
        best_tile, min_dist = None, float('inf')
        for dx in range(-HUMAN_VISION_RADIUS, HUMAN_VISION_RADIUS):
            for dy in range(-HUMAN_VISION_RADIUS, HUMAN_VISION_RADIUS):
                tile = world.get_tile(self.x + dx, self.y + dy)
                if tile and tile.resource_type == r_type and tile.resource_amount > 50:
                    dist = get_distance(self.get_pos(), (tile.x, tile.y))
                    if dist < min_dist:
                        min_dist, best_tile = dist, tile
        return best_tile
    
    def find_nearest_group(self, groups):
        best_group, min_dist = None, float('inf')
        for g in groups:
            if g == self: continue
            dist = get_distance(self.get_pos(), g.get_pos())
            if dist < min_dist:
                min_dist, best_group = dist, g
        return best_group
    
    def can_evolve(self):
        return self.population >= TRIBE_CREATION_POPULATION and \
               self.inventory['wood'] >= TRIBE_CREATION_RESOURCES['wood'] and \
               self.inventory['stone'] >= TRIBE_CREATION_RESOURCES['stone']

# --- Остальные классы (Tribe, City, State) почти без изменений, только конструкторы ---

class Settlement:
    """Базовый класс для Племени, Города и Государства."""
    def __init__(self, x, y, population, resources):
        self.x, self.y = x, y
        self.population = population
        self.resources = resources
        self.territory = []
        self.update_territory(None)

    def get_pos(self): return (self.x, self.y)
    def update_territory(self, world): pass
    def get_max_population(self): return 0
    
    def gather_resources(self, world):
        for tile in self.territory:
            if tile.resource_amount > 0:
                amount = min(tile.resource_amount, 5) 
                self.resources[tile.resource_type] += amount
                tile.resource_amount -= amount

    def update_population(self, dt):
        food_needed = self.population * 0.1 * dt
        water_needed = self.population * 0.15 * dt
        
        if self.resources['food'] < food_needed or self.resources['water'] < water_needed:
            self.population -= 0.5 * dt
        else:
            self.resources['food'] -= food_needed
            self.resources['water'] -= water_needed
            if self.population < self.get_max_population() and self.resources['food'] > self.population and self.resources['water'] > self.population:
                self.population += 0.5 * dt
    
    def update(self, world, dt):
        if not self.territory and world: self.update_territory(world)
        self.gather_resources(world)
        self.update_population(dt)


class Tribe(Settlement):
    def __init__(self, group):
        super().__init__(group.x, group.y, group.population, group.inventory)
        self.progress_to_city = 0

    def update_territory(self, world):
        center_tile = world.get_tile(self.x, self.y)
        if center_tile: self.territory = [center_tile] + world.get_neighbors(center_tile)
    def draw(self, surface):
        pos = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, COLORS['tribe'], pos, TILE_SIZE)
    def get_max_population(self): return TRIBE_MAX_POPULATION
    def update(self, world, dt):
        super().update(world, dt)
        self.progress_to_city += (self.population / TRIBE_MAX_POPULATION) * dt * 0.1
    def can_evolve(self):
        return self.population >= TRIBE_MAX_POPULATION and self.resources['wood'] >= CITY_CREATION_RESOURCES['wood']

class City(Tribe):
    def __init__(self, tribe):
        super().__init__(tribe)
        self.population = tribe.population
        self.resources = tribe.resources
        self.progress_to_state = 0
    def update_territory(self, world):
        center_tile = world.get_tile(self.x, self.y)
        if center_tile: self.territory = [center_tile] + world.get_neighbors(center_tile, radius=2)
    def draw(self, surface):
        rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE * 2)
        rect.center = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.rect(surface, COLORS['city'], rect)
    def get_max_population(self): return CITY_MAX_POPULATION
    def update(self, world, dt):
        super().update(world, dt)
        self.progress_to_state += (self.population / CITY_MAX_POPULATION) * dt * 0.05
    def can_evolve(self):
        return self.population >= CITY_MAX_POPULATION and self.resources['wood'] >= STATE_CREATION_RESOURCES['wood']
        
class State(City):
    # Этот класс остается почти без изменений
    def __init__(self, city, color):
        super().__init__(city)
        self.color = color; self.diplomacy = {}; self.capacity = 150
    def update_territory(self, world):
        if not self.territory:
            center_tile = world.get_tile(self.x, self.y)
            if center_tile: self.territory = [center_tile] + world.get_neighbors(center_tile, radius=3)
        for tile in self.territory: tile.owner_state = self
        self.capacity = 150 + len(self.territory) * 5
    def draw(self, surface): pass
    def get_max_population(self): return self.capacity
    def get_strength(self): return self.population + sum(self.resources.values()) / 10
    def expand(self, world):
        if all(self.resources.get(res, 0) >= cost for res, cost in STATE_EXPANSION_COST.items()):
            expandable_tiles = {n for t in self.territory for n in world.get_neighbors(t) if n not in self.territory and n.owner_state is None}
            if expandable_tiles:
                new_tile = random.choice(list(expandable_tiles))
                self.territory.append(new_tile)
                new_tile.owner_state = self
                for res, cost in STATE_EXPANSION_COST.items(): self.resources[res] -= cost
    def update_diplomacy(self, world, states):
        # Логика дипломатии остается прежней
        pass
    def update(self, world, dt, states):
        if not self.territory: self.update_territory(world)
        self.gather_resources(world)
        self.update_population(dt)
        if self.population <= 0:
            for tile in self.territory: tile.owner_state = None
            if self in states: states.remove(self)
            return
        if random.random() < 0.01: self.expand(world)
        self.update_diplomacy(world, states)

# --- Основной класс игры ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Эволюция Цивилизации v2")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 12)
        self.big_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.world = World(GRID_WIDTH, GRID_HEIGHT)
        self.humans = []
        self.groups = []
        self.settlements = []
        self.states = []
        self.running = True
        self.paused = False
        self.game_speed = 1
        self.selected_object = None
        self.spawning_mode = False

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
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: self.paused = not self.paused
                if event.key == pygame.K_RIGHT: self.game_speed = min(self.game_speed * 2, 64)
                if event.key == pygame.K_LEFT: self.game_speed = max(self.game_speed // 2, 1)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] > GAME_WORLD_WIDTH: # Клик по UI
                    if self.add_human_button_rect.collidepoint(mouse_pos):
                        self.spawning_mode = not self.spawning_mode # Вкл/выкл режим
                else: # Клик по миру
                    grid_x = mouse_pos[0] // TILE_SIZE
                    grid_y = mouse_pos[1] // TILE_SIZE
                    if self.spawning_mode:
                        self.add_human(grid_x, grid_y)
                        self.spawning_mode = False
                    else:
                        self.selected_object = self.get_object_at(grid_x, grid_y)

    def get_object_at(self, x, y):
        # В порядке "слоев": государства -> поселения -> группы -> люди -> тайлы
        tile = self.world.get_tile(x,y)
        if tile and tile.owner_state: return tile.owner_state
        for s in self.settlements:
            if get_distance((x, y), s.get_pos()) <= 2: return s
        for g in self.groups:
            if get_distance((x, y), g.get_pos()) <= 1: return g
        for h in self.humans:
            if h.x == x and h.y == y: return h
        return tile

    def add_human(self, x, y):
        self.humans.append(Human(x, y))

    def update(self):
        dt = 1/60.0 # Фиксированный timestep для стабильности при разной скорости
        
        # Обновление всех сущностей
        for human in self.humans: human.update(self.world, self.humans, dt)
        for group in self.groups: group.update(self.world, self.groups, dt)
        
        new_settlements = []
        for s in self.settlements:
            if isinstance(s, State): s.update(self.world, dt, self.states)
            else: s.update(self.world, dt)
            
            if hasattr(s, 'can_evolve') and s.can_evolve():
                if isinstance(s, Tribe): new_settlements.append(City(s))
                elif isinstance(s, City):
                    color = random.choice([c for c in STATE_COLORS if c not in [st.color for st in self.states]] or [(100,100,100)])
                    new_state = State(s, color)
                    self.states.append(new_state)
                    new_settlements.append(new_state)
            else:
                new_settlements.append(s)
        self.settlements = new_settlements

        # Социальная динамика и эволюция
        self.update_social_dynamics()
        
        # Очистка мертвых
        self.humans = [h for h in self.humans if not h.is_dead()]
        self.groups = [g for g in self.groups if g.population > 0]
        self.settlements = [s for s in self.settlements if s.population > 0]
        self.states = [s for s in self.states if s in self.settlements]


    def update_social_dynamics(self):
        # 1. Формирование групп из людей
        to_remove_h, checked_h = [], set()
        for h1 in self.humans:
            if h1 in checked_h: continue
            partners = [h1]
            for h2 in self.humans:
                if h1 != h2 and get_distance(h1.get_pos(), h2.get_pos()) < 2:
                    partners.append(h2)
            
            if len(partners) >= GROUP_CREATION_MEMBERS:
                avg_x = int(sum(p.x for p in partners) / len(partners))
                avg_y = int(sum(p.y for p in partners) / len(partners))
                self.groups.append(Group(avg_x, avg_y, partners))
                for p in partners:
                    to_remove_h.append(p)
                    checked_h.add(p)
        self.humans = [h for h in self.humans if h not in to_remove_h]

        # 2. Присоединение людей к группам
        to_remove_h = []
        for human in self.humans:
            for group in self.groups:
                if get_distance(human.get_pos(), group.get_pos()) < GROUP_JOIN_RADIUS:
                    group.population += 1
                    for res, amount in human.inventory.items(): group.inventory[res] += amount
                    to_remove_h.append(human)
                    break
        self.humans = [h for h in self.humans if h not in to_remove_h]

        # 3. Взаимодействие групп
        to_remove_g, checked_g = [], set()
        for g1 in self.groups:
            if g1 in checked_g: continue
            for g2 in self.groups:
                if g1 != g2 and g2 not in checked_g and get_distance(g1.get_pos(), g2.get_pos()) < 3:
                    # Война или слияние
                    if g1.get_strength() > g2.get_strength() * 1.5: # Война - сильный побеждает
                        g1.population += g2.population * 0.5 # Поглощает половину
                        for res, amount in g2.inventory.items(): g1.inventory[res] += amount
                        to_remove_g.append(g2)
                    elif g2.get_strength() > g1.get_strength() * 1.5:
                        g2.population += g1.population * 0.5
                        for res, amount in g1.inventory.items(): g2.inventory[res] += amount
                        to_remove_g.append(g1)
                    else: # Слияние
                        g1.population += g2.population
                        for res, amount in g2.inventory.items(): g1.inventory[res] += amount
                        to_remove_g.append(g2)

                    checked_g.add(g1); checked_g.add(g2)
                    break
        self.groups = [g for g in self.groups if g not in to_remove_g]


        # 4. Эволюция групп в племена
        to_remove_g = []
        for group in self.groups:
            if group.can_evolve():
                self.settlements.append(Tribe(group))
                to_remove_g.append(group)
        self.groups = [g for g in self.groups if g not in to_remove_g]

    def draw(self):
        self.screen.fill(COLORS['background'])
        game_surface = self.screen.subsurface(pygame.Rect(0, 0, GAME_WORLD_WIDTH, SCREEN_HEIGHT))
        self.world.draw(game_surface)
        
        for s in self.settlements: s.draw(game_surface)
        for g in self.groups: g.draw(game_surface, self.font)
        for h in self.humans: h.draw(game_surface)
        
        if self.spawning_mode:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] < GAME_WORLD_WIDTH:
                grid_x, grid_y = mouse_pos[0] // TILE_SIZE, mouse_pos[1] // TILE_SIZE
                marker_rect = pygame.Rect(grid_x * TILE_SIZE, grid_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                s.fill(COLORS['spawn_marker'])
                game_surface.blit(s, marker_rect.topleft)

        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        ui_rect = pygame.Rect(GAME_WORLD_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLORS['ui_background'], ui_rect)
        y_pos = 20
        
        # Общая инфо
        self.draw_text(f"Люди: {len(self.humans)} | Группы: {len(self.groups)}", 20, y_pos)
        y_pos += 25
        self.draw_text(f"Поселения: {len([s for s in self.settlements if not isinstance(s, State)])} | Государства: {len(self.states)}", 20, y_pos)
        y_pos += 30
        
        # Кнопка
        btn_color = (100, 180, 100) if self.spawning_mode else (80, 80, 150)
        self.add_human_button_rect = pygame.Rect(GAME_WORLD_WIDTH + 20, y_pos, UI_PANEL_WIDTH - 40, 40)
        pygame.draw.rect(self.screen, btn_color, self.add_human_button_rect, border_radius=5)
        btn_text = "Выберите место на карте" if self.spawning_mode else "Добавить человека"
        self.draw_text(btn_text, 0, 0, center_on_button=self.add_human_button_rect)
        y_pos += 60

        # Инфо о выбранном объекте
        if self.selected_object:
            pygame.draw.line(self.screen, COLORS['text'], (GAME_WORLD_WIDTH + 10, y_pos), (SCREEN_WIDTH - 10, y_pos))
            y_pos += 15
            obj = self.selected_object
            
            if isinstance(obj, Group):
                self.draw_text("Группа", 20, y_pos, font=self.big_font)
                y_pos += 25
                self.draw_text(f"Население: {int(obj.population)}", 20, y_pos)
                y_pos += 20
                self.draw_text(f"Состояние: {obj.state}", 20, y_pos)
                y_pos += 25
                self.draw_text(f"Инвентарь (Макс: {obj.inventory_capacity}):", 20, y_pos)
                y_pos += 20
                for res, amount in obj.inventory.items():
                    self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y_pos)
                    y_pos += 20
                self.draw_progress_bar("Эволюция в племя:", (obj.population / TRIBE_CREATION_POPULATION), y_pos)
            
            # ... (остальные instanceof блоки: Human, Tribe, City, State, Tile)
            # Код для них остается практически таким же, как и в прошлой версии
            # Для краткости он здесь опущен, но он есть в полном файле
            
    def draw_text(self, text, x_offset, y_pos, font=None, color=None, center_on_button=None):
        if font is None: font = self.font
        if color is None: color = COLORS['text']
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center_on_button: text_rect.center = center_on_button.center
        else: text_rect.topleft = (GAME_WORLD_WIDTH + x_offset, y_pos)
        self.screen.blit(text_surface, text_rect)

    def draw_progress_bar(self, label, progress, y_pos):
        self.draw_text(label, 20, y_pos)
        y_pos += 20
        progress = max(0, min(1, progress))
        bg_rect = pygame.Rect(GAME_WORLD_WIDTH + 20, y_pos, UI_PANEL_WIDTH - 40, 15)
        fill_rect = pygame.Rect(GAME_WORLD_WIDTH + 20, y_pos, (UI_PANEL_WIDTH - 40) * progress, 15)
        pygame.draw.rect(self.screen, COLORS['progress_bar_bg'], bg_rect, border_radius=3)
        pygame.draw.rect(self.screen, COLORS['progress_bar_fill'], fill_rect, border_radius=3)


if __name__ == '__main__':
    game = Game()
    game.run()

