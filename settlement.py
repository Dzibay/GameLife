import pygame
from config import *
import random


tile_to_state = {}


class Settlement:
    """Базовый класс для Племени, Города и Государства."""
    def __init__(self, x, y, population, resources):
        self.type = ''
        self.x, self.y = x, y
        self.population = population
        self.resources = resources
        self.territory = []
        self.gather_radius = 0
        self.add_population_amount = 1
        self.update_territory(None)

    def get_pos(self): return (self.x, self.y)
    def update_territory(self, world): pass
    def get_max_population(self): return 0

    def get_tiles_in_radius(self, world, tile, radius):
        tiles = []
        center_x, center_y = tile.x, tile.y
        # Пробегаем квадрат вокруг точки
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x, y = center_x + dx, center_y + dy
                # Проверка выхода за границы мира
                if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                    tile = world.get_tile(x, y)
                    if tile:
                        # Проверяем, находится ли тайл в круге радиуса R
                        if (dx**2 + dy**2) <= radius**2:
                            tiles.append(tile)
        return tiles
    
    def gather_resources(self):
        for tile in self.territory:
            if tile.resource_amount > 0:
                amount = min(tile.resource_amount, HUMAN_GATHER_SPEED * self.population / len(self.territory))
                for resource in self.resources:
                    if resource == tile.resource_type:
                        self.resources[resource] += amount
                        tile.resource_amount -= amount
                    else:
                        self.resources[resource] += amount / 10
    

    def update_population(self):
        food_needed = self.population * 0.1
        water_needed = self.population * 0.05
        
        if self.resources['food'] < food_needed or self.resources['water'] < water_needed:
            self.population -= 1
        else:
            self.resources['food'] -= food_needed
            self.resources['water'] -= water_needed
            if self.population < self.get_max_population() and self.resources['food'] > self.population * 5 and self.resources['water'] > self.population * 5:
                self.population += self.add_population_amount
    
    def update(self, world):
        if not self.territory and world: self.update_territory(world)
        self.gather_resources()
        self.update_population()

class Tribe(Settlement):
    def __init__(self, group):
        super().__init__(group.x, group.y, group.population, group.resources)
        self.progress_to_city = 0
        self.type = 'Tribe'
        self.add_population_amount = 10

    def update_territory(self, world):
        if world:
            center_tile = world.get_tile(self.x, self.y)
            if center_tile: self.territory = [center_tile] + world.get_neighbors(center_tile)
    def draw(self, surface):
        pos = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, COLORS['tribe'], pos, TILE_SIZE)
    def get_max_population(self): return TRIBE_MAX_POPULATION
    def update(self, world):
        super().update(world)
        self.progress_to_city = sum(min(self.resources[res] / cost, 1) for res, cost in CITY_CREATION_RESOURCES.items()) / 2
    def can_evolve(self):
        return all(self.resources.get(res, 0) >= cost for res, cost in CITY_CREATION_RESOURCES.items())

class City(Tribe):
    def __init__(self, tribe):
        
        super().__init__(tribe)
        self.population = tribe.population
        self.resources = tribe.resources
        self.progress_to_state = 0
        self.type = 'City'
        self.add_population_amount = 50
        
    def update_territory(self, world):
        if world:
            center_tile = world.get_tile(self.x, self.y)
            if center_tile: self.territory = [center_tile] + world.get_neighbors(center_tile, radius=2)

    def draw(self, surface):
        rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE * 2)
        rect.center = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.rect(surface, COLORS['city'], rect)
    def get_max_population(self): return CITY_MAX_POPULATION
    def update(self, world):
        super().update(world)
        self.progress_to_state = self.progress_to_city = sum(min(self.resources[res] / cost, 1) for res, cost in STATE_CREATION_RESOURCES.items()) / 2

    def can_evolve(self):
        return all(self.resources.get(res, 0) >= cost for res, cost in STATE_CREATION_RESOURCES.items())

class State(City):
    def __init__(self, city, color):
        super().__init__(city)
        self.color = color; self.diplomacy = {}
        self.type = 'State'
        self.border_tiles = set()
        self.add_population_amount = 300
        self.technology_lvl = 0
        self.nuclear_bomb = 0
        self.nuclear_progress = 0
        self.starting_nuclear_war = 0
        self.neighbors_cache = {}

    def update_territory(self, world):
        if world: 
            if not self.territory: 
                center_tile = world.get_tile(self.x, self.y) 
                if center_tile: 
                    self.territory = [center_tile] + world.get_neighbors(center_tile, radius=3) 
                    for tile in self.territory: 
                        tile.owner_state = self

        # if not self.territory:
        #     c = world.get_tile(self.x, self.y)
        #     if c: self.territory = [c] + world.get_neighbors(c, radius=3)
        # for t in self.territory:
        #     t.owner_state = self
        # self.capacity = len(self.territory) * 20

    def draw(self, surface): pass
    def get_max_population(self): return len(self.territory) * 20
    def get_power(self): return (self.population + sum(self.resources.values()) / 10) * self.technology_lvl
    def get_summary_power(self):
        return sum([state.get_power() for state, diplomacy in self.diplomacy.items() if diplomacy == 'peace']) + self.get_power()

    def update_border_tiles(self, world):
        self.border_tiles = {t for t in self.territory
                            if any(n.owner_state != self for n in world.get_neighbors(t))}
    

    # def expand(self, world):
    #     # Проверяем ресурсы
    #     if not all(self.resources.get(res, 0) >= cost for res, cost in STATE_EXPANSION_COST.items()):
    #         return
        
    #     # Собираем все соседние тайлы текущей территории
    #     expandable_tiles = set()
    #     for tile in self.border_tiles:
    #         for neighbor in world.get_neighbors(tile):
    #             if neighbor.owner_state is None:
    #                 expandable_tiles.add(neighbor)
        
    #     if not expandable_tiles:
    #         return  # нет куда расширяться

    #     # Выбираем случайный тайл из множества
    #     new_tile = random.choice(list(expandable_tiles))

    #     # Расширяем территорию
    #     self.territory.append(new_tile)
    #     new_tile.owner_state = self

    #     tile_to_state[(new_tile.x, new_tile.y)] = self
    #     self.border_tiles.add(new_tile)
    #     # проверяем соседей нового тайла
    #     for neighbor in world.get_neighbors(new_tile):
    #         if neighbor.owner_state == self:
    #             # сосед уже наш, он может перестать быть пограничным
    #             if all(n.owner_state == self for n in world.get_neighbors(neighbor)):
    #                 self.border_tiles.discard(neighbor)

    #     # Снимаем ресурсы
    #     for res, cost in STATE_EXPANSION_COST.items():
    #         self.resources[res] -= cost
    def expand(self, world):
        if not all(self.resources.get(res, 0) >= cost for res, cost in STATE_EXPANSION_COST.items()):
            return
        expandable = set()
        for t in self.border_tiles:
            key = (t.x, t.y, 1)
            if key not in self.neighbors_cache:
                self.neighbors_cache[key] = world.get_neighbors(t)
            for n in self.neighbors_cache[key]:
                if n.owner_state is None:
                    expandable.add(n)
        if not expandable:
            return
        new_tile = random.choice(tuple(expandable))
        self.territory.append(new_tile)
        new_tile.owner_state = self
        tile_to_state[(new_tile.x, new_tile.y)] = self
        self.border_tiles.add(new_tile)
        for n in world.get_neighbors(new_tile):
            if n.owner_state == self and all(nb.owner_state == self for nb in world.get_neighbors(n)):
                self.border_tiles.discard(n)
        for res, cost in STATE_EXPANSION_COST.items():
            self.resources[res] -= cost
        self._power_dirty = True


    # def update_diplomacy(self, world):
    #     # Сохраняем всех соседних государств
    #     neighboring_states = set()
        
    #     for tile in self.border_tiles:
    #         for neighbor in world.get_neighbors(tile):
    #             if neighbor.owner_state and neighbor.owner_state != self:
    #                 neighboring_states.add(neighbor.owner_state)
        
    #     # Обновляем дипломатию
    #     for other_state in neighboring_states:
    #         if other_state not in self.diplomacy:
    #             # Решаем: война или мир
    #             if other_state.nuclear_bomb and self.nuclear_bomb:
    #                 self.diplomacy[other_state] = 'war'
    #                 other_state.diplomacy[self] = 'war'
    #             else:
    #                 try:
    #                     power_differense = self.get_summary_power() / other_state.get_summary_power()
    #                     if power_differense > 1.2 or power_differense < 0.8:
    #                         self.diplomacy[other_state] = 'war'
    #                         other_state.diplomacy[self] = 'war'
    #                     else:
    #                         self.diplomacy[other_state] = 'peace'
    #                         other_state.diplomacy[self] = 'peace'
    #                 except:
    #                     pass
        
    #     # Убираем из дипломатов тех, кто больше не сосед
    #     for other_state in list(self.diplomacy.keys()):
    #         if other_state not in neighboring_states:
    #             del self.diplomacy[other_state]
    def update_diplomacy(self, world):
        neighboring = set()
        for t in self.border_tiles:
            key = (t.x, t.y, 1)
            if key not in self.neighbors_cache:
                self.neighbors_cache[key] = world.get_neighbors(t)
            for n in self.neighbors_cache[key]:
                if n.owner_state and n.owner_state != self:
                    neighboring.add(n.owner_state)
        for other in neighboring:
            if other not in self.diplomacy:
                try:
                    ratio = self.get_summary_power() / other.get_summary_power()
                    status = 'war' if ratio > 1.2 or ratio < 0.8 else 'peace'
                    self.diplomacy[other] = status
                    other.diplomacy[self] = status
                except ZeroDivisionError:
                    pass
        for s in list(self.diplomacy.keys()):
            if s not in neighboring:
                del self.diplomacy[s]
    
    def handle_wars(self, world, states):
        for enemy, status in self.diplomacy.items():
            if status != 'war': 
                continue

            # Найти граничащие тайлы между state и enemy
            border_pairs = []
            for tile in self.border_tiles:
                for neighbor in world.get_neighbors(tile):
                    if neighbor.owner_state == enemy:
                        border_pairs.append((tile, neighbor))
            
            if not border_pairs:
                continue  # нет прямого контакта на границе
            
            # Выбираем случайную пару
            attacker_tile, defender_tile = random.choice(border_pairs)
            
            # Определяем победителя с учётом силы
            attacker_power = self.get_summary_power()
            defender_power = enemy.get_summary_power()
            total = attacker_power + defender_power
            win_chance = attacker_power / total
            
            if random.random() < win_chance:
                winner, loser = self, enemy
                winner_tile, loser_tile = attacker_tile, defender_tile
            else:
                winner, loser = enemy, self
                winner_tile, loser_tile = defender_tile, attacker_tile
            
            # Прогресс ядерной войны
            if loser.nuclear_bomb >= 1:
                loser.starting_nuclear_war = min(loser.starting_nuclear_war + 0.01, 1)

            # Победитель захватывает клетку
            winner.territory.append(loser_tile)
            loser.territory.remove(loser_tile)
            loser_tile.owner_state = winner

            # Потери населения и ресурсов (пример)
            loss_ratio = 0.01  # 1% потерь
            winner.population = max(1, int(winner.population * (1 - loss_ratio)))
            loser.population = max(1, int(loser.population * (1 - loss_ratio)))
            for res in winner.resources:
                winner.resources[res] = max(0, int(winner.resources[res] * (1 - loss_ratio)))
            for res in loser.resources:
                loser.resources[res] = max(0, int(loser.resources[res] * (1 - loss_ratio)))

            # После войны нужно обновить border_tiles
            self.update_border_tiles(world)

            try:
                enemy.update_border_tiles(world)
                if not loser.territory:
                    states.remove(loser)
                    break
            except:
                pass

    def update_technology_lvl(self):
        if self.technology_lvl < MAX_TECHNOLOGY_LVL:
            self.technology_lvl += self.population / 300 / 100
            for state, diplomacy in self.diplomacy.items():
                if diplomacy == 'peace':
                    self.technology_lvl += state.technology_lvl / MAX_TECHNOLOGY_LVL / 100
                else:
                    self.technology_lvl -= state.technology_lvl / MAX_TECHNOLOGY_LVL / 100
        if self.technology_lvl >= MAX_TECHNOLOGY_LVL:
            self.create_nuclear_bomb()

    def create_nuclear_bomb(self):
        self.nuclear_bomb += 0.005
        self.nuclear_progress = self.nuclear_bomb % 1 / 1
    
    def check_nuclear_progress(self, world):
        if self.starting_nuclear_war == 1:
            if self.nuclear_bomb >= 1:
                for state in [state for state, diplomacy in self.diplomacy.items() if diplomacy == 'war']:
                    target_tile = random.choice(state.territory)
                    self.nuclear_bomb -= 1
                    world.nuclear_explosion(target_tile)

    def update(self, world, states):
        if self.population > 0 and self.territory:
            self.gather_resources()
            if len(self.territory) < 1000:
                self.update_population()

                if self.population <= 0:
                    for tile in self.territory: tile.owner_state = None

                self.expand(world)
                self.update_diplomacy(world)
                self.update_technology_lvl()
                self.handle_wars(world, states)
                self.check_nuclear_progress(world)
