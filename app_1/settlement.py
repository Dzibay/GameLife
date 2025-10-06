# -*- coding: utf-8 -*-
import pygame
from config import *
import random

class Settlement:
    """Базовый класс для всех поселений (племя, город, государство)."""
    def __init__(self, x, y, world, population, initial_resources):
        self.world = world
        self.x = x
        self.y = y
        self.population = population
        self.resources = initial_resources
        self.size = TILE_SIZE
        self.color = WHITE
        self.type = "Settlement"
        self.evolution_progress = 0

    def update(self):
        """Обновляет состояние поселения."""
        self.produce_resources()
        self.consume_resources()
        self.check_evolution()

        if self.population <= 0:
            self.world.remove_settlement(self)

    def produce_resources(self):
        """Производство ресурсов."""
        # Базовый класс не производит, переопределяется в потомках
        pass

    def consume_resources(self):
        """Потребление ресурсов населением."""
        food_needed = self.population * 0.01
        water_needed = self.population * 0.02
        
        if self.resources["food"] >= food_needed:
            self.resources["food"] -= food_needed
        else:
            self.population -= 1 # Люди умирают от голода
            print('Люди умирают от голода')

        if self.resources["water"] >= water_needed:
            self.resources["water"] -= water_needed
        else:
            self.population -= 1 # Люди умирают от жажды
            print('Люди умирают от жажды')
        
        # Рост населения, если достаточно еды
        if self.resources.get("food", 0) > self.population * 2:
            self.population += 0.1

    def check_evolution(self):
        """Проверка возможности эволюции."""
        pass # Переопределяется в потомках

    def draw(self, screen):
        """Отрисовка поселения."""
        rect = pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
        pygame.draw.rect(screen, self.color, rect)

        # Отрисовка полосы прогресса эволюции
        if self.evolution_progress > 0:
            progress_bar_width = self.size * self.evolution_progress
            progress_bar_height = 5
            progress_bar_rect = pygame.Rect(
                self.x - self.size // 2,
                self.y + self.size // 2 + 2,
                progress_bar_width,
                progress_bar_height
            )
            pygame.draw.rect(screen, CYAN, progress_bar_rect)
            
    def get_info(self):
        """Возвращает информацию о поселении."""
        return {
            "Тип": self.type,
            "Население": f"{int(self.population)}",
            "Еда": f"{int(self.resources['food'])}",
            "Вода": f"{int(self.resources['water'])}",
            "Дерево": f"{int(self.resources['wood'])}",
            "Камень": f"{int(self.resources['stone'])}"
        }

class Tribe(Settlement):
    """Класс, представляющий племя."""
    def __init__(self, x, y, world, population, initial_resources):
        super().__init__(x, y, world, population, initial_resources)
        self.size = TRIBE_SIZE
        self.color = TRIBE_COLOR
        self.type = "Племя"

    def produce_resources(self):
        self.resources["food"] = self.resources.get("food", 0) + self.population * 0.05
        self.resources["water"] = self.resources.get("water", 0) + self.population * 0.05
        self.resources["wood"] = self.resources.get("wood", 0) + self.population * 0.02
        self.resources["stone"] = self.resources.get("stone", 0) + self.population * 0.02

    def check_evolution(self):
        pop_ok = self.population >= CITY_EVOLUTION_POPULATION
        wood_ok = self.resources.get("wood", 0) >= CITY_EVOLUTION_RESOURCES["wood"]
        stone_ok = self.resources.get("stone", 0) >= CITY_EVOLUTION_RESOURCES["stone"]
        
        progress = []
        progress.append(min(1, self.population / CITY_EVOLUTION_POPULATION))
        progress.append(min(1, self.resources.get("wood", 0) / CITY_EVOLUTION_RESOURCES["wood"]))
        progress.append(min(1, self.resources.get("stone", 0) / CITY_EVOLUTION_RESOURCES["stone"]))
        self.evolution_progress = sum(progress) / len(progress)

        if pop_ok and wood_ok and stone_ok:
            self.world.evolve_settlement(self, City)

class City(Settlement):
    """Класс, представляющий город."""
    def __init__(self, x, y, world, population, initial_resources):
        super().__init__(x, y, world, population, initial_resources)
        self.size = CITY_SIZE
        self.color = CITY_COLOR
        self.type = "Город"

    def produce_resources(self):
        self.resources["food"] = self.resources.get("food", 0) + self.population * 0.1
        self.resources["water"] = self.resources.get("water", 0) + self.population * 0.1
        self.resources["wood"] = self.resources.get("wood", 0) + self.population * 0.05
        self.resources["stone"] = self.resources.get("stone", 0) + self.population * 0.05

    def check_evolution(self):
        pop_ok = self.population >= STATE_EVOLUTION_POPULATION
        wood_ok = self.resources.get("wood", 0) >= STATE_EVOLUTION_RESOURCES["wood"]
        stone_ok = self.resources.get("stone", 0) >= STATE_EVOLUTION_RESOURCES["stone"]

        progress = []
        progress.append(min(1, self.population / STATE_EVOLUTION_POPULATION))
        progress.append(min(1, self.resources.get("wood", 0) / STATE_EVOLUTION_RESOURCES["wood"]))
        progress.append(min(1, self.resources.get("stone", 0) / STATE_EVOLUTION_RESOURCES["stone"]))
        self.evolution_progress = sum(progress) / len(progress)

        if pop_ok and wood_ok and stone_ok:
            self.world.evolve_settlement(self, State)

class State(Settlement):
    """Класс, представляющий государство."""
    def __init__(self, x, y, world, population, initial_resources):
        super().__init__(x, y, world, population, initial_resources)
        self.size = STATE_BASE_SIZE
        self.type = "Государство"
        self.territory = set([(int(x // TILE_SIZE), int(y // TILE_SIZE))])
        self.border = list(self.get_border_tiles())
        self.interactions = {} # {other_state: "war"/"peace"}
        
        states_number = len([i for i in self.world.settlements if i.type == "Государство"])
        self.color = STATE_COLORS[states_number-1] if states_number <= 10 else STATE_COLORS[states_number-11]

    def update(self):
        super().update()
        if self.world.ticks % 100 == 0:
            self.expand()
        self.update_interactions()

    def produce_resources(self):
        random_resources_choise = random.randint(1, 2)
        if random_resources_choise == 1:
            self.resources["food"] = self.resources.get("food", 0) + len(self.territory) * 0.2
            self.resources["wood"] = self.resources.get("wood", 0) + len(self.territory) * 0.5
        else:
            self.resources["water"] = self.resources.get("water", 0) + len(self.territory) * 1
            self.resources["stone"] = self.resources.get("stone", 0) + len(self.territory) * 0.5

    def expand(self):
        """Расширение территории государства."""
        state_size = len(self.territory)
        if not self.border or self.resources.get("food", 0) < self.population * 1.1 \
        or self.resources["wood"] < STATE_RESOURCES_NEEDED_TO_EXPAND["wood"] or \
            self.resources["stone"] < STATE_RESOURCES_NEEDED_TO_EXPAND["stone"]:
            return
        
        self.resources["wood"] -= STATE_RESOURCES_NEEDED_TO_EXPAND["wood"]
        self.resources["stone"] -= STATE_RESOURCES_NEEDED_TO_EXPAND["stone"]

        tile_to_expand = random.choice(self.border)
        gx, gy = tile_to_expand
        
        # Проверка, не занята ли клетка другим государством
        for other_state in self.world.settlements:
            if isinstance(other_state, State) and other_state != self:
                if (gx, gy) in other_state.territory:
                    return # Нельзя расширяться на чужую территорию

        self.territory.add((gx, gy))
        self.border = list(self.get_border_tiles())
        # Обновление размера для визуализации
        min_x = min(t[0] for t in self.territory) * TILE_SIZE
        max_x = max(t[0] for t in self.territory) * TILE_SIZE
        self.size = max(self.size, max_x - min_x)


    def get_border_tiles(self):
        """Получает клетки на границе территории."""
        border_tiles = set()
        for gx, gy in self.territory:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and (nx, ny) not in self.territory:
                    border_tiles.add((nx, ny))
        return border_tiles
    
    def update_interactions(self):
        """Обновление взаимодействий с другими государствами."""
        for other_state in self.world.settlements:
            if isinstance(other_state, State) and other_state != self:
                # Проверяем, есть ли уже взаимодействие
                if other_state not in self.interactions:
                     is_bordering = any(tile in other_state.territory for tile in self.get_border_tiles())
                     if is_bordering:
                         if random.random() < WAR_CHANCE:
                             self.interactions[other_state] = "war"
                             other_state.interactions[self] = "war"
                         else:
                             self.interactions[other_state] = "peace"
                             other_state.interactions[self] = "peace"
                
                # Логика войны
                if self.interactions.get(other_state) == "war":
                    self.population -= 0.1 # Потери в войне
                    
                    # Захват территории
                    if self.population > other_state.population * 1.2 and self.world.ticks % 50 == 0:

                        other_state.population -= 0.5

                        border_with_enemy = self.get_border_tiles().intersection(other_state.territory)
                        if border_with_enemy:
                            tile_to_capture = random.choice(list(border_with_enemy))
                            other_state.territory.remove(tile_to_capture)
                            self.territory.add(tile_to_capture)
                            # Обновляем границы
                            self.border = list(self.get_border_tiles())
                            other_state.border = list(other_state.get_border_tiles())
                            
                            if not other_state.territory:
                                self.world.remove_settlement(other_state)


    def draw(self, screen):
        """Отрисовка территории государства."""
        for gx, gy in self.territory:
            rect = pygame.Rect(gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, self.color, rect)
        
        # Отрисовка границ и фронтов
        for other, status in self.interactions.items():
            border_color = RED if status == "war" else GREEN
            common_border = self.get_border_tiles().intersection(other.territory)
            for gx, gy in common_border:
                 pygame.draw.line(screen, border_color, (gx * TILE_SIZE, gy * TILE_SIZE), ((gx+1) * TILE_SIZE, (gy+1) * TILE_SIZE), 2)
