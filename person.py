# -*- coding: utf-8 -*-
import random
import pygame
from config import *

class Person:
    """Класс, представляющий человека в симуляции."""
    def __init__(self, x, y, world):
        self.world = world
        self.x = x
        self.y = y
        self.radius = PERSON_RADIUS
        self.color = PERSON_COLOR
        self.speed = PERSON_SPEED

        self.age = 0
        self.lifespan = PERSON_LIFESPAN * (1 + random.uniform(-0.2, 0.2))
        self.hunger = 100
        
        self.resources = {"food": 0, "water": 0, "wood": 0, "stone": 0}
        self.target_resource = None
        self.reproduce_cooldown = PERSON_REPRODUCE_COOLDOWN

    def update(self):
        """Обновляет состояние человека."""
        self.age += 1
        self.hunger -= PERSON_HUNGER_RATE
        if self.age > self.lifespan or self.hunger <= 0:
            self.world.remove_person(self)
            return

        self.move()
        self.gather_resources()
        self.consume_resources()
        self.check_settlement_near()

        if self.reproduce_cooldown > 0:
            self.reproduce_cooldown -= 1
        
        if self.resources["food"] > PERSON_REPRODUCE_THRESHOLD and self.reproduce_cooldown <= 0:
            self.reproduce()

    def move(self):
        """Логика передвижения человека."""
        if self.target_resource:
            tx, ty = self.target_resource
            dx, dy = tx - self.x, ty - self.y
            dist = (dx**2 + dy**2)**0.5
            if dist < self.speed:
                self.x, self.y = tx, ty
                self.target_resource = None
            else:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
        else:
            # Случайное блуждание или поиск ресурса
            if random.random() < 0.1:
                self.find_nearest_resource()
            else:
                self.x += random.randint(-self.speed, self.speed)
                self.y += random.randint(-self.speed, self.speed)

        # Ограничение передвижения границами мира
        self.x = max(0, min(self.x, SCREEN_WIDTH))
        self.y = max(0, min(self.y, SCREEN_HEIGHT))
    
    def check_settlement_near(self):
        for settlement in self.world.settlements:
            if abs(self.x - settlement.x) < PERSON_FOUND_SETTLEMENT_RADIUS:
                if abs(self.y - settlement.y) < PERSON_FOUND_SETTLEMENT_RADIUS:
                    settlement.population += 1
                    self.world.remove_person(self)

    def find_nearest_resource(self):
        """Находит ближайший ресурс."""
        grid_x, grid_y = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
        min_dist = float('inf')
        target = None
        
        # Поиск в радиусе 10 клеток
        for i in range(max(0, grid_x - 10), min(GRID_WIDTH, grid_x + 10)):
            for j in range(max(0, grid_y - 10), min(GRID_HEIGHT, grid_y + 10)):
                if self.world.resources_grid[j][i]:
                    dist = ((i * TILE_SIZE - self.x)**2 + (j * TILE_SIZE - self.y)**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        target = (i * TILE_SIZE, j * TILE_SIZE)
        
        self.target_resource = target

    def gather_resources(self):
        """Сбор ресурсов."""
        grid_x, grid_y = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            resource_info = self.world.resources_grid[grid_y][grid_x]
            if resource_info:
                res_type, amount = resource_info
                self.resources[res_type] += 1
                self.world.resources_grid[grid_y][grid_x] = (res_type, amount - 1)
                if amount - 1 <= 0:
                    self.world.resources_grid[grid_y][grid_x] = None

    def consume_resources(self):
        """Потребление ресурсов для выживания."""
        if self.hunger < 50 and self.resources["food"] > 0:
            self.resources["food"] -= 1
            self.hunger += 20
        if self.resources["water"] > 0:
            # Вода просто нужна для жизни, но не влияет на голод в этой модели
             self.resources["water"] -= 0.5


    def reproduce(self):
        """Размножение."""
        self.resources["food"] -= PERSON_REPRODUCE_THRESHOLD / 2
        self.world.add_person(self.x + random.randint(-5, 5), self.y + random.randint(-5, 5))
        self.reproduce_cooldown = PERSON_REPRODUCE_COOLDOWN

    def draw(self, screen):
        """Отрисовка человека."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
