import pygame
from world import World
from config import *
from settlement import *
from human import Human
from tile import Tile


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