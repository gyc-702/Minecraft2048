import pygame
import random
import sys
import json

# ===================== 基础配置 =====================
pygame.init()
WIDTH = 400
HEIGHT = 470
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048 MC矿石版")

GRID_SIZE = 4
CELL_SIZE = 80  # 格子大小，16x16原图放大5倍正好80
GAP = 10
GRID_TOP = 60

# 颜色定义
BG_COLOR = (187, 173, 160)
CELL_EMPTY_COLOR = (205, 192, 180)
FONT_COLOR_DARK = (119, 110, 101)

# 图片资源目录
IMAGE_DIR = "ORE"
# 记录保存文件名
SAVE_FILE = "best_tile.json"

# 字体
FONT = pygame.font.Font(None, 48)
SMALL_FONT = pygame.font.Font(None, 32)
TIP_FONT = pygame.font.Font(None, 36)

# ===================== 矿石方块映射表（合成链） =====================
TILE_IMAGE_MAP = {
    2: "coal_ore.png",
    4: "deepslate_coal_ore.png",
    8: "copper_ore.png",
    16: "deepslate_copper_ore.png",
    32: "iron_ore.png",
    64: "deepslate_iron_ore.png",
    128: "gold_ore.png",
    256: "deepslate_gold_ore.png",
    512: "lapis_ore.png",
    1024: "deepslate_lapis_ore.png",
    2048: "emerald_ore.png",
    4096: "deepslate_emerald_ore.png",
    8192: "diamond_ore.png",
    16384: "deepslate_diamond_ore.png",
    32768: "diamond_block.png",
    65536: "netherite_block.png",
}

# ===================== 预加载图片资源（最近邻缩放，不糊） =====================
def load_tile_textures():
    textures = {}
    for value, filename in TILE_IMAGE_MAP.items():
        path = f"{IMAGE_DIR}/{filename}"
        try:
            img = pygame.image.load(path).convert_alpha()
            # 关键：使用 scale 最近邻缩放，保留像素锐利边缘，不做平滑模糊
            img = pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
            textures[value] = img
        except Exception as e:
            print(f"警告：无法加载图片 {path}，{e}")
    return textures

def load_ui_icons():
    icon_size = 24
    current_icon = None
    best_icon = None
    try:
        current_icon = pygame.image.load(f"{IMAGE_DIR}/emerald.png").convert_alpha()
        current_icon = pygame.transform.scale(current_icon, (icon_size, icon_size))
    except:
        pass
    try:
        best_icon = pygame.image.load(f"{IMAGE_DIR}/diamond.png").convert_alpha()
        best_icon = pygame.transform.scale(best_icon, (icon_size, icon_size))
    except:
        pass
    return current_icon, best_icon

tile_textures = load_tile_textures()
current_max_icon, best_icon = load_ui_icons()


# ===================== 记录持久化功能 =====================
def load_best_tile():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return int(data.get("best_tile", 0))
    except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
        return 0

def save_best_tile(value):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"best_tile": value}, f, ensure_ascii=False, indent=2)


# ===================== 核心游戏逻辑 =====================
def init_grid():
    grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    add_new_tile(grid)
    add_new_tile(grid)
    return grid

def add_new_tile(grid):
    empty_cells = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if grid[i][j] == 0]
    if not empty_cells:
        return
    i, j = random.choice(empty_cells)
    grid[i][j] = 2 if random.random() < 0.9 else 4

def slide_row_left(row):
    new_row = [num for num in row if num != 0]
    for i in range(len(new_row) - 1):
        if new_row[i] == new_row[i + 1]:
            new_row[i] *= 2
            new_row[i + 1] = 0
    new_row = [num for num in new_row if num != 0]
    while len(new_row) < GRID_SIZE:
        new_row.append(0)
    return new_row

def move_grid(grid, direction):
    moved = False
    new_grid = [row[:] for row in grid]

    if direction == "left":
        for i in range(GRID_SIZE):
            original = new_grid[i][:]
            new_grid[i] = slide_row_left(new_grid[i])
            if new_grid[i] != original:
                moved = True
    elif direction == "right":
        for i in range(GRID_SIZE):
            original = new_grid[i][:]
            reversed_row = new_grid[i][::-1]
            new_row = slide_row_left(reversed_row)
            new_grid[i] = new_row[::-1]
            if new_grid[i] != original:
                moved = True
    elif direction == "up":
        for j in range(GRID_SIZE):
            col = [new_grid[i][j] for i in range(GRID_SIZE)]
            original = col[:]
            new_col = slide_row_left(col)
            for i in range(GRID_SIZE):
                new_grid[i][j] = new_col[i]
            if new_col != original:
                moved = True
    elif direction == "down":
        for j in range(GRID_SIZE):
            col = [new_grid[i][j] for i in range(GRID_SIZE)]
            original = col[:]
            reversed_col = col[::-1]
            new_col = slide_row_left(reversed_col)[::-1]
            for i in range(GRID_SIZE):
                new_grid[i][j] = new_col[i]
            if new_col != original:
                moved = True

    return new_grid, moved

def get_max_tile(grid):
    return max(max(row) for row in grid)

def check_game_over(grid):
    for row in grid:
        if 0 in row:
            return False
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE - 1):
            if grid[i][j] == grid[i][j + 1]:
                return False
    for j in range(GRID_SIZE):
        for i in range(GRID_SIZE - 1):
            if grid[i][j] == grid[i + 1][j]:
                return False
    return True


# ===================== 绘制模块 =====================
def draw_tile(surface, value, x, y):
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

    if value == 0:
        pygame.draw.rect(surface, CELL_EMPTY_COLOR, rect, border_radius=8)
        return

    if value in tile_textures:
        surface.blit(tile_textures[value], (x, y))
    else:
        pygame.draw.rect(surface, (60, 58, 50), rect, border_radius=8)
        text_surface = FONT.render(str(value), True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)


def draw_ui(surface, grid, current_max, best_tile, game_over):
    surface.fill(BG_COLOR)

    # 左上角：本局当前最大（绿宝石图标）
    x_offset = GAP
    y_offset = GAP + 10
    if current_max_icon:
        surface.blit(current_max_icon, (x_offset, y_offset))
        x_offset += current_max_icon.get_width() + 5
    current_text = SMALL_FONT.render(str(current_max), True, FONT_COLOR_DARK)
    surface.blit(current_text, (x_offset, y_offset))

    # 右上角：历史最高（钻石图标）
    best_text = SMALL_FONT.render(str(best_tile), True, FONT_COLOR_DARK)
    best_x = WIDTH - best_text.get_width() - GAP
    if best_icon:
        icon_x = best_x - best_icon.get_width() - 5
        surface.blit(best_icon, (icon_x, y_offset))
    surface.blit(best_text, (best_x, y_offset))

    # 绘制网格
    grid_x_start = GAP
    grid_y_start = GRID_TOP
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x = grid_x_start + j * (CELL_SIZE + GAP)
            y = grid_y_start + i * (CELL_SIZE + GAP)
            draw_tile(surface, grid[i][j], x, y)

    # 游戏结束遮罩
    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((238, 228, 218, 180))
        surface.blit(overlay, (0, 0))

        tip = "Game Over! Press R to Restart"
        text_surface = TIP_FONT.render(tip, True, FONT_COLOR_DARK)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        surface.blit(text_surface, text_rect)


# ===================== 主循环 =====================
def main():
    grid = init_grid()
    current_max = get_max_tile(grid)
    best_tile = load_best_tile()
    game_over = False
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    grid = init_grid()
                    current_max = get_max_tile(grid)
                    game_over = False
                    continue

                if game_over:
                    continue

                direction = None
                if event.key == pygame.K_LEFT:
                    direction = "left"
                elif event.key == pygame.K_RIGHT:
                    direction = "right"
                elif event.key == pygame.K_UP:
                    direction = "up"
                elif event.key == pygame.K_DOWN:
                    direction = "down"

                if direction:
                    grid, moved = move_grid(grid, direction)
                    if moved:
                        add_new_tile(grid)
                        current_max = get_max_tile(grid)
                        if current_max > best_tile:
                            best_tile = current_max
                            save_best_tile(best_tile)

                        if check_game_over(grid):
                            game_over = True

        draw_ui(SCREEN, grid, current_max, best_tile, game_over)
        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
