import pygame
from config import *
import random
from tile import Tile



class Human:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = "searching_partner"
        self.hunger = 0
        self.thirst = 0
        self.age = 0
        self.lifespan = random.uniform(HUMAN_LIFESPAN[0], HUMAN_LIFESPAN[1])
        self.resources = {'food': 5, 'water': 5, 'wood': 0, 'stone': 0}
        self.target = None

    def get_pos(self): return (self.x, self.y)

    def draw(self, surface):
        pos = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, COLORS['human'], pos, TILE_SIZE // 2)

    def update(self, world, humans):
        self.age += 1
        self.hunger += 0.4
        self.thirst += 0.6
        if self.is_dead():
            return
        self.consume_resources()
        self.run_ai(world, humans)
    
    def is_dead(self):
        return self.hunger >= 10 or self.thirst >= 10 or self.age >= self.lifespan

    def consume_resources(self):
        if self.hunger > 5 and self.resources['food'] > 0:
            self.resources['food'] -= 1; self.hunger -= 3
        if self.thirst > 6 and self.resources['water'] > 0:
            self.resources['water'] -= 1; self.thirst -= 4

    def run_ai(self, world, humans):
        if self.thirst > 5: self.target = self.find_nearest_resource(world, 'water')
        elif self.hunger > 5: self.target = self.find_nearest_resource(world, 'food')
        else:
            if sum([self.resources[i] for i in self.resources]) < HUMAN_INVENTORY_CAPACITY:
                    self.target = random.choice([self.find_nearest_resource(world, "wood"), self.find_nearest_resource(world, "stone"), self.find_nearest_human(humans)])
            else:
                self.target = self.find_nearest_human(humans)

        if self.target:
            target_pos = self.target.get_pos() if isinstance(self.target, Human) else (self.target.x, self.target.y)
            if get_distance(self.get_pos(), target_pos) == 0:
                if isinstance(self.target, Tile):
                    self.gather_resource(self.target)
                    self.target = None
            else:
                self.move_towards(target_pos)
    
    def gather_resource(self, tile):
        if tile and tile.resource_amount > 0:
            self.resources[tile.resource_type] += HUMAN_GATHER_SPEED
            tile.resource_amount -= HUMAN_GATHER_SPEED

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
        self.resources = {res: sum(h.resources.get(res, 0) for h in initial_members) for res in ['food', 'water', 'wood', 'stone']}
        self.inventory_capacity = self.population * 20
        self.state = "searching_resource"
        self.target = None
        self.reproduction_progress = 0

    def get_pos(self): return (self.x, self.y)
    
    def get_strength(self): return self.population + sum(self.resources.values())/10

    def draw(self, surface, font):
        pos = (self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(surface, COLORS['group'], pos, TILE_SIZE * 0.8)
        text = font.render(str(int(self.population)), True, (255,255,255))
        text_rect = text.get_rect(center=pos)
        surface.blit(text, text_rect)

    def update(self, world, groups):
        self.consume_and_reproduce()
        if self.population <= 0: return
        self.run_ai(world, groups)

    def consume_and_reproduce(self):
        food_needed = self.population * 0.1
        water_needed = self.population * 0.15

        if self.resources['food'] < food_needed or self.resources['water'] < water_needed:
            self.population -= 1
            return
        

        self.resources['food'] -= food_needed
        self.resources['water'] -= water_needed

        if self.resources['food'] > self.population and self.resources['water'] > self.population:
            self.population += 1
            self.inventory_capacity = self.population * 50

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
            if get_distance(self.get_pos(), target_pos) == 0:
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
        if self.resources['water'] < self.population * 2: return self.find_nearest_resource(world, 'water')
        if self.resources['food'] < self.population * 2: return self.find_nearest_resource(world, 'food')
        
        nearest_group = self.find_nearest_group(groups)
        if nearest_group and get_distance(self.get_pos(), nearest_group.get_pos()) < HUMAN_VISION_RADIUS * 2:
             return nearest_group

        if self.resources['wood'] < TRIBE_CREATION_RESOURCES['wood']: return self.find_nearest_resource(world, 'wood')
        if self.resources['stone'] < TRIBE_CREATION_RESOURCES['stone']: return self.find_nearest_resource(world, 'stone')
        
        return self.find_nearest_resource(world, random.choice(['wood', 'stone']))

    def gather_resource(self, tile):
        if sum(self.resources.values()) >= self.inventory_capacity: return
        
        amount = min(self.population * HUMAN_GATHER_SPEED, tile.resource_amount)
        self.resources[tile.resource_type] += amount
        tile.resource_amount -= amount

        self.state = "searching_resource"


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
               self.resources['wood'] >= TRIBE_CREATION_RESOURCES['wood'] and \
               self.resources['stone'] >= TRIBE_CREATION_RESOURCES['stone']
