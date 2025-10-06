import pygame
from config import *
import random


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
