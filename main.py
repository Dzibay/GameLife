# -*- coding: utf-8 -*-
import pygame
import sys
import random
from config import *
from world import World
from settlement import State # Для проверки типа

class Game:
    """Основной класс игры, управляющий циклом, вводом и отображением."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.world = World()
        self.running = True
        self.paused = False
        self.time_speed = 1 # 1, 2, 4, 8
        self.selected_settlement = None

    def run(self):
        """Основной игровой цикл."""
        # Начальная популяция
        for _ in range(50):
            self.world.add_person(random.randint(SCREEN_WIDTH // 2, SCREEN_WIDTH), 
                                  random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT))

        while self.running:
            self.handle_events()
            if not self.paused:
                for _ in range(self.time_speed):
                    self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Обработка пользовательского ввода."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                if event.key == pygame.K_p: # Добавить 10 человек
                    for _ in range(10):
                       self.world.add_person(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
                if event.key == pygame.K_RIGHT: # Увеличить скорость
                    self.time_speed = min(16, self.time_speed * 2)
                if event.key == pygame.K_LEFT: # Уменьшить скорость
                    self.time_speed = max(1, self.time_speed // 2)
            if event.type == pygame.MOUSEBUTTONDOWN:
                 if event.button == 1: # Левая кнопка мыши
                    self.selected_settlement = None
                    pos = pygame.mouse.get_pos()
                    for settlement in self.world.settlements:
                        rect = pygame.Rect(
                            settlement.x - settlement.size // 2,
                            settlement.y - settlement.size // 2,
                            settlement.size,
                            settlement.size
                        )
                        if rect.collidepoint(pos):
                            self.selected_settlement = settlement
                            break


    def update(self):
        """Обновление состояния игры."""
        self.world.update()

    def draw(self):
        """Отрисовка всего на экране."""
        self.screen.fill(BLACK)
        self.world.draw(self.screen)
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        """Отрисовка пользовательского интерфейса."""
        # Статус симуляции
        pause_text = "ПАУЗА" if self.paused else ""
        ui_text = f"Людей: {len(self.world.people)} | Поселений: {len(self.world.settlements)} | Скорость: x{self.time_speed} {pause_text}"
        text_surface = self.font.render(ui_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))

        # Инструкции
        instructions = [
            "P - Добавить 10 людей",
            "Пробел - Пауза",
            "Стрелки <> - Изменить скорость",
            "ЛКМ по поселению - Инфо"
        ]
        for i, instruction in enumerate(instructions):
            inst_surface = self.font.render(instruction, True, WHITE)
            self.screen.blit(inst_surface, (10, 30 + i * 20))
            
        # Информация о выбранном поселении
        if self.selected_settlement:
            info = self.selected_settlement.get_info()
            y_offset = 10
            for key, value in info.items():
                info_text = f"{key}: {value}"
                info_surface = self.font.render(info_text, True, WHITE)
                # Рисуем на черной подложке для читаемости
                bg_rect = pygame.Rect(SCREEN_WIDTH - 210, y_offset-5, 200, 25)
                pygame.draw.rect(self.screen, BLACK, bg_rect)
                self.screen.blit(info_surface, (SCREEN_WIDTH - 200, y_offset))
                y_offset += 20
                
            # Выделение выбранного поселения
            if isinstance(self.selected_settlement, State):
                # Для государств выделяем всю территорию
                for gx, gy in self.selected_settlement.territory:
                    rect = pygame.Rect(gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.screen, YELLOW, rect, 2)
            else:
                rect = pygame.Rect(
                    self.selected_settlement.x - self.selected_settlement.size // 2,
                    self.selected_settlement.y - self.selected_settlement.size // 2,
                    self.selected_settlement.size,
                    self.selected_settlement.size
                )
                pygame.draw.rect(self.screen, YELLOW, rect, 2)


if __name__ == '__main__':
    game = Game()
    game.run()
