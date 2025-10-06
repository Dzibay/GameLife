# -*- coding: utf-8 -*-
import pygame
import random
from config import *
from person import Person
from settlement import Tribe

class World:
    """Класс, управляющий миром, ресурсами и всеми сущностями."""
    def __init__(self):
        self.people = []
        self.settlements = []
        self.resources_grid = self.generate_resources()
        self.ticks = 0

    def generate_resources(self):
        """Генерирует сетку с ресурсами."""
        grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if random.random() < RESOURCE_SPAWN_CHANCE:
                    res_type, (color, amount) = random.choice(list(RESOURCES.items()))
                    grid[y][x] = (res_type, amount)
        return grid

    def add_person(self, x, y):
        """Добавляет нового человека в мир."""
        self.people.append(Person(x, y, self))

    def remove_person(self, person):
        """Удаляет человека из мира и передает его ресурсы ближайшему."""
        if person in self.people:
            # Найти ближайшего человека для передачи ресурсов
            nearest_person = None
            min_dist = float('inf')
            
            for other_person in self.people:
                if person != other_person:
                    dist = ((person.x - other_person.x)**2 + (person.y - other_person.y)**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        nearest_person = other_person
            
            # Передать ресурсы, если найден сосед в радиусе 50 пикселей
            if nearest_person and min_dist < 50:
                for res, amount in person.resources.items():
                    nearest_person.resources[res] = nearest_person.resources.get(res, 0) + amount

            self.people.remove(person)
            
    def add_settlement(self, settlement):
        """Добавляет новое поселение."""
        self.settlements.append(settlement)

    def remove_settlement(self, settlement):
        """Удаляет поселение."""
        if settlement in self.settlements:
            self.settlements.remove(settlement)

    def evolve_settlement(self, old_settlement, new_settlement_class):
        """Эволюция поселения."""
        new_settlement = new_settlement_class(
            old_settlement.x, 
            old_settlement.y, 
            self, 
            old_settlement.population, 
            old_settlement.resources
        )
        self.remove_settlement(old_settlement)
        self.add_settlement(new_settlement)

    def update(self):
        """Обновляет состояние всего мира."""
        self.ticks += 1
        
        # Обновляем людей
        for person in self.people[:]:
            person.update()
            
        # Обновляем поселения
        for settlement in self.settlements[:]:
            settlement.update()

        # Проверяем формирование племен
        self.check_tribe_formation()
        
        # Периодически добавляем ресурсы
        if self.ticks % RESOURCE_SPAWN_RATE == 0:
            self.spawn_random_resource()


    def check_tribe_formation(self):
        """Проверяет, могут ли группы людей сформировать племя."""
        if len(self.people) < TRIBE_FORMATION_POPULATION:
            return

        # Простой алгоритм: проверяем людей в случайном порядке
        random.shuffle(self.people)
        for person in self.people:
            nearby_people = []
            for other_person in self.people:
                if person != other_person:
                    dist = ((person.x - other_person.x)**2 + (person.y - other_person.y)**2)**0.5
                    if dist < 100: # Радиус поиска 50 пикселей
                        nearby_people.append(other_person)
            
            if len(nearby_people) + 1 >= TRIBE_FORMATION_POPULATION:
                group = [person] + nearby_people[:TRIBE_FORMATION_POPULATION-1]
                total_res = {}
                avg_x, avg_y = 0, 0
                
                for p in group:
                    avg_x += p.x
                    avg_y += p.y
                    for res, amount in p.resources.items():
                        total_res[res] = total_res.get(res, 0) + amount
                
                # Проверяем, достаточно ли ресурсов
                res_ok = all(total_res.get(res, 0) >= amount for res, amount in TRIBE_FORMATION_RESOURCES.items())

                if res_ok:
                    avg_x /= len(group)
                    avg_y /= len(group)
                    
                    tribe = Tribe(avg_x, avg_y, self, len(group), total_res)
                    self.add_settlement(tribe)
                    
                    # Удаляем людей, сформировавших племя
                    for p in group:
                        self.remove_person(p)
                    
                    # Выходим, чтобы не создавать несколько племен за один тик
                    return

    def spawn_random_resource(self):
        """Создает случайный ресурс в пустой клетке."""
        x, y = random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1)
        if self.resources_grid[y][x] is None:
            res_type, (color, amount) = random.choice(list(RESOURCES.items()))
            self.resources_grid[y][x] = (res_type, amount)


    def draw(self, screen):
        """Отрисовывает весь мир."""
        # Рисуем ресурсы
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.resources_grid[y][x]:
                    res_type, _ = self.resources_grid[y][x]
                    color, _ = RESOURCES[res_type]
                    pygame.draw.rect(screen, color, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        
        # Рисуем людей
        for person in self.people:
            person.draw(screen)

        # Рисуем поселения
        for settlement in self.settlements:
            settlement.draw(screen)

