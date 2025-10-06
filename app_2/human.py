import pygame
from config import *
import random



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
        self.hunger += 2 * dt
        self.thirst += 3 * dt

        if self.hunger >= HUMAN_MAX_HUNGER or self.thirst >= HUMAN_MAX_THIRST or self.age >= self.lifespan:
            self.die(humans)
            return

        self.consume_resources()
        self.run_ai(world, humans, settlements)

    def consume_resources(self):
        if self.hunger > (HUMAN_MAX_HUNGER // 2) and self.inventory['food'] > 0:
            self.inventory['food'] -= 1
            self.hunger -= 3
        if self.thirst > (HUMAN_MAX_THIRST // 2) and self.inventory['water'] > 0:
            self.inventory['water'] -= 1
            self.thirst -= 4

    def find_best_target(self, world, humans):
        # Приоритеты: вода -> еда -> объединение -> ресурсы для племени
        if self.inventory['food'] <= 2: return self.find_nearest_resource(world, 'food')
        if self.inventory['water'] <= 2: return self.find_nearest_resource(world, 'water')

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
                print("Собрал")
                self.target = None

    def move_towards(self, target_pos):
        dx, dy = target_pos[0] - self.x, target_pos[1] - self.y
        if abs(dx) > abs(dy):
            self.x += 1 if dx > 0 else -1
        elif dy != 0:
            self.y += 1 if dy > 0 else -1

    def find_nearest_resource(self, world, resource_type):
        print(resource_type)
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