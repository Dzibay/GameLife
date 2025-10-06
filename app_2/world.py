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