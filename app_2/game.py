import pygame
from world import World
from config import *
from settlement import *
from human import Human, Group
from tile import Tile


# --- Основной класс игры ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
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
        self.tick = 0

    def run(self):
        while self.running:
            self.handle_events()
            if not self.paused:
                for _ in range(self.game_speed):
                    self.update()
            self.draw()
            self.clock.tick(60)

            fps = self.clock.get_fps()
            pygame.display.set_caption(f"Эволюция Цивилизации - FPS: {fps:.2f}")
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
    
    def generate_state_color(self, existing_colors):
        while True:
            color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            if all(sum(abs(c1 - c2) for c1, c2 in zip(color, ex)) > 120 for ex in existing_colors):
                return color

    def update(self):

        self.tick += self.game_speed
        if self.tick % TICK_STEP < self.game_speed:
        
            # Обновление всех сущностей
            for human in self.humans: human.update(self.world, self.humans)
            for group in self.groups: group.update(self.world, self.groups)
            
            for s in self.settlements:
                if isinstance(s, State):
                    s.update(self.world, self.states)
                else: 
                    s.update(self.world)
                
                    if hasattr(s, 'can_evolve') and s.can_evolve():
                        if isinstance(s, City):
                            color = self.generate_state_color([st.color for st in self.states])
                            new_state = State(s, color)
                            self.states.append(new_state)
                            self.settlements.append(new_state)
                            self.settlements.remove(s)
                            new_state.update_territory(self.world); 
                            new_state.update_border_tiles(self.world)
                        elif isinstance(s, Tribe): 
                            self.settlements.append(City(s))
                            self.settlements.remove(s)

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
                    for res, amount in human.resources.items(): group.resources[res] += amount
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
                        for res, amount in g2.resources.items(): g1.resources[res] += amount
                        to_remove_g.append(g2)
                    elif g2.get_strength() > g1.get_strength() * 1.5:
                        g2.population += g1.population * 0.5
                        for res, amount in g1.resources.items(): g2.resources[res] += amount
                        to_remove_g.append(g1)
                    else: # Слияние
                        g1.population += g2.population
                        for res, amount in g2.resources.items(): g1.resources[res] += amount
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
        y = 20
        
        # Общая инфо
        self.draw_text(f"Симуляция: {'Пауза' if self.paused else 'Идет'}", 20, y)
        y += 30
        self.draw_text(f"Скорость: x{self.game_speed}", 20, y)
        y += 30
        self.draw_text(f"Год: x{self.tick // 50}", 20, y)
        y += 30
        self.draw_text(f"Люди: {len(self.humans)} | Группы: {len(self.groups)}", 20, y)
        y += 25
        self.draw_text(f"Поселения: {len([s for s in self.settlements if not isinstance(s, State)])} | Государства: {len(self.states)}", 20, y)
        y += 30
        
        # Кнопка
        btn_color = (100, 180, 100) if self.spawning_mode else (80, 80, 150)
        self.add_human_button_rect = pygame.Rect(GAME_WORLD_WIDTH + 20, y, UI_PANEL_WIDTH - 40, 40)
        pygame.draw.rect(self.screen, btn_color, self.add_human_button_rect, border_radius=5)
        btn_text = "Выберите место на карте" if self.spawning_mode else "Добавить человека"
        self.draw_text(btn_text, 0, 0, center_on_button=self.add_human_button_rect)
        y += 60

        # Инфо о выбранном объекте
        if self.selected_object:
            pygame.draw.line(self.screen, COLORS['text'], (GAME_WORLD_WIDTH + 10, y), (SCREEN_WIDTH - 10, y))
            y += 15
            obj = self.selected_object
            
            if isinstance(obj, Tile):
                self.draw_text("Клетка Мира", 20, y, font=self.big_font)
                y += 25
                self.draw_text(f"Координаты: ({obj.x}, {obj.y})", 20, y)
                y += 20
                self.draw_text(f"Ресурс: {obj.resource_type.capitalize()}", 20, y)
                y += 20
                self.draw_text(f"Количество: {int(obj.resource_amount)}", 20, y)
                y += 20
                if obj.owner_state:
                     self.draw_text("Владелец: Государство", 20, y)
                else:
                     self.draw_text("Владелец: Нет", 20, y)

            elif isinstance(obj, Human):
                self.draw_text("Человек", 20, y, font=self.big_font); y+=25
                self.draw_text(f"Возраст: {int(obj.age)} / {int(obj.lifespan)}", 20, y); y+=20
                self.draw_text(f"Голод: {int(obj.hunger)}/100", 20, y); y+=20
                self.draw_text(f"Жажда: {int(obj.thirst)}/100", 20, y); y+=25
                self.draw_text("Инвентарь:", 20, y); y+=20
                for res, amount in obj.resources.items(): self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y); y+=20
            elif isinstance(obj, Group):
                self.draw_text("Группа", 20, y, font=self.big_font); y+=25
                self.draw_text(f"Население: {int(obj.population)}", 20, y); y+=20
                self.draw_text(f"Инвентарь (Макс: {obj.inventory_capacity}):", 20, y); y+=20
                for res, amount in obj.resources.items(): self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y); y+=20
                self.draw_progress_bar("Эволюция в племя:", obj.population / TRIBE_CREATION_POPULATION, y)
            elif isinstance(obj, State):
                self.draw_text("Государство", 20, y, font=self.big_font)
                y += 25
                self.draw_text(f"Технологии: {int(obj.technology_lvl)} / {MAX_TECHNOLOGY_LVL}", 20, y)
                y += 20
                self.draw_text(f"Ядерное оружие: {int(obj.nuclear_bomb)}", 20, y)
                y += 20
                self.draw_progress_bar("Создание ядерного оружия:", obj.nuclear_progress, y)
                y += 35
                self.draw_progress_bar("Начало ядерной войны:", obj.starting_nuclear_war / 1, y)
                y += 60
                self.draw_text(f"Население: {int(obj.population)} / {obj.get_max_population()}", 20, y)
                y += 20
                self.draw_text(f"Территория: {len(obj.territory)} клеток", 20, y)
                y += 25
                self.draw_text("Ресурсы:", 20, y)
                y += 20
                for res, amount in obj.resources.items():
                    self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y)
                    y += 20
                y += 10
                self.draw_text("Дипломатия:", 20, y)
                y += 20
                if not obj.diplomacy: self.draw_text("  Нет контактов", 20, y)
                for other, status in obj.diplomacy.items():
                    self.draw_text(f"  Статус: {status.capitalize()}", 20, y, color=COLORS[status])
                    y += 20
            elif isinstance(obj, City):
                self.draw_text("Город", 20, y, font=self.big_font)
                y += 25
                self.draw_text(f"Население: {int(obj.population)}/{CITY_MAX_POPULATION}", 20, y)
                y += 20
                self.draw_progress_bar("Прогресс до Государства:", obj.progress_to_state, y) # Делим для наглядности
                y += 35
                self.draw_text("Ресурсы:", 20, y)
                y += 20
                for res, amount in obj.resources.items():
                    self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y)
                    y += 20
            elif isinstance(obj, Tribe):
                self.draw_text("Племя", 20, y, font=self.big_font)
                y += 25
                self.draw_text(f"Население: {int(obj.population)}/{TRIBE_MAX_POPULATION}", 20, y)
                y += 20
                self.draw_progress_bar("Прогресс до Города:", obj.progress_to_city, y)
                y += 35
                self.draw_text("Ресурсы:", 20, y)
                y += 20
                for res, amount in obj.resources.items():
                    self.draw_text(f"  {res.capitalize()}: {int(amount)}", 20, y)
                    y += 20
            
            
            
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


game = Game()
game.run()
