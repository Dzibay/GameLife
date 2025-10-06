from tile import Tile


class World:
    """Управляет всеми клетками (тайлами) мира."""
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.grid = [[Tile(x, y) for y in range(height)] for x in range(width)]

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]
        return None

    def get_neighbors(self, tile, radius=1):
        neighbors = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0: continue
                nx, ny = tile.x + dx, tile.y + dy
                neighbor_tile = self.get_tile(nx, ny)
                if neighbor_tile:
                    neighbors.append(neighbor_tile)
        return neighbors

    def draw(self, surface):
        for row in self.grid:
            for tile in row:
                tile.draw(surface)
    
    def nuclear_explosion(self, target_tile, radius=7):
        affected_tiles = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                distance = (dx**2 + dy**2)**0.5
                if distance <= radius:
                    nx, ny = target_tile.x + dx, target_tile.y + dy
                    tile = self.get_tile(nx, ny)
                    if tile:
                        affected_tiles.append(tile)

        state_tiles = 0
        for tile in affected_tiles:
            tile.radioactive = True
            tile.resource_amount = 0
            if tile.owner_state:
                state_tiles += 1
                tile.owner_state.population *= 1 - (state_tiles / len(tile.owner_state.territory))
                tile.owner_state.starting_nuclear_war = 1
                tile.owner_state = None

        print(f"💥 Ядерный взрыв уничтожил {state_tiles} государственных клеток!")
        