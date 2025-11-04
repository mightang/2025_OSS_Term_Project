import sys
import random
from collections import deque
import pygame

ROWS = 20
COLS = 20
NUM_MINES = 80

CELL = 32
HUD_H = 80
FPS = 60

BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
WIN_W = BOARD_W
WIN_H = HUD_H + BOARD_H

COLOR_BG = (29, 31, 33)
COLOR_HUD_BG = (36, 39, 43)
COLOR_GRID = (58, 63, 68)

COLOR_CELL_COVERED = (43, 47, 51)
COLOR_CELL_REVEALED = (52, 56, 60)
COLOR_HOVER = (55, 60, 66)
COLOR_TEXT = (230, 233, 236)
COLOR_NUM = {
    1: (100, 170, 255),
    2: (120, 200, 120),
    3: (255, 110, 110),
    4: (120, 120, 220),
    5: (220, 120, 120),
    6: (120, 220, 220),
    7: (220, 220, 120),
    8: (200, 200, 200),
}
COLOR_MINE = (220, 80, 80)
COLOR_FLAG = (255, 200, 80)

class BoardState:
    def __init__(self, rows:int, cols: int, num_mines: int):
        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines

        self.first_move = True
        self.game_over = False
        self.victory = False

        self.mines = [[False]*cols for _ in range(rows)]
        self.revealed = [[False]*cols for _ in range(rows)]
        self.flagged = [[False]*cols for _ in range(rows)]
        self.adj = [[0]*cols for _ in range(rows)]

        self.revealed_safe = 0

    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols
    
    def neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if(self.in_bounds(nr, nc)):
                    yield nr, nc
    
    def place_mines_safe(self, safe_r, safe_c):
        forbidden = {(safe_r, safe_c)}
        for nr, nc in self.neighbors(safe_r, safe_c):
            forbidden.add((nr, nc))

        pool = [(r, c) for r in range(self.rows) for c in range(self.cols) if(r, c) not in forbidden]
        mines_coords = random.sample(pool, self.num_mines)
        for r, c in mines_coords:
            self.mines[r][c] = True

        for r in range(self.rows):
            for c in range(self.cols):
                if self.mines[r][c]:
                    self.adj[r][c] = -1
                else:
                    cnt = 0
                    for nr, nc in self.neighbors(r, c):
                        if self.mines[nr][nc]:
                            cnt += 1
                    self.adj[r][c] = cnt

    def toggle_flag(self, r, c):
        if self.game_over:
            return
        if not self.in_bounds(r, c):
            return
        if self.revealed[r][c]:
            return
        self.flagged[r][c] = not self.flagged[r][c]

    def reveal(self, r, c):
        if self.game_over:
            return
        if not self.in_bounds(r, c):
            return
        if self.revealed[r][c] or self.flagged[r][c]:
            return
        
        if self.first_move:
            self.place_mines_safe(r, c)
            self.first_move = False

        if self.mines[r][c]:
            self.revealed[r][c] = True
            self.game_over = True
            self.victory = False
            return
        
        q = deque()
        q.append((r, c))
        while q:
            cr, cc = q.popleft()
            if self.revealed[cr][cc]:
                continue
            self.revealed[cr][cc] = True
            self.revealed_safe += 1

            if self.adj[cr][cc] == 0:
                for nr, nc in self.neighbors(cr, cc):
                    if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                        if not self.mines[nr][nc]:
                            q.append((nr, nc))

        total_safe = self.rows * self.cols - self.num_mines
        if self.revealed_safe == total_safe:
            self.game_over = True
            self.victory = True

    def chord(self, r, c):
        if self.game_over or not self.in_bounds(r, c):
            return
        if not self.revealed[r][c]:
            return
        
        n = self.adj[r][c]
        if n <= 0:
            return
        flags = sum(1 for nr, nc in self.neighbors(r, c) if self.flagged[nr][nc])
        if flags != n:
            return
        for nr, nc in self.neighbors(r, c):
            if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                self.reveal(nr, nc)
                    
# 좌표 변환
def screen_to_cell(x : int, y : int):
    grid_y = y - HUD_H
    if grid_y < 0:
        return None
    
    r = grid_y // CELL
    c = x // CELL
    if 0 <= r < ROWS and 0 <= c < COLS:
        return (r, c)
    return None

def cell_to_rect(r: int, c : int) -> pygame.Rect:
    x = c * CELL
    y = HUD_H + r * CELL
    return pygame.Rect(x, y, CELL, CELL)

# HUD 그리기(상단 게임 진행 바)
def draw_hud(surf: pygame.Surface, font: pygame.font.Font, elapsed_sec: int, state: BoardState, hover_cell=None):
    pygame.draw.rect(surf, COLOR_HUD_BG, (0, 0, WIN_W, HUD_H))

    title = font.render(
        f"MINESWEEPER {'WIN!' if state.victory else 'LOSE!' if state.game_over else ''}",
        True, COLOR_TEXT
    )
    surf.blit(title, (16, 16))

    flags_used = sum(state.flagged[r][c] for r in range(state.rows) for c in range(state.cols))
    info_text = f"TIME {elapsed_sec:03d} MINES {state.num_mines:02d} FLAGS {flags_used:02d}"
    info = font.render(info_text, True, COLOR_TEXT)
    surf.blit(info, (WIN_W - info.get_width() - 16, 16))

    pygame.draw.line(surf, COLOR_GRID, (0, HUD_H - 1), (WIN_W, HUD_H - 1), 1)

# 보드 그리기
def draw_board(surf: pygame.Surface, font: pygame.font.Font, state: BoardState, hover_cell = None):
    for r in range(ROWS):
        for c in range(COLS):
            rect = cell_to_rect(r, c)

            base_color = COLOR_CELL_REVEALED if state.revealed[r][c] else COLOR_CELL_COVERED
            pygame.draw.rect(surf, base_color, rect)

            if state.revealed[r][c] or (state.game_over and state.mines[r][c]):
                if state.mines[r][c]:
                    pygame.draw.circle(surf, COLOR_MINE, rect.center, CELL // 4)
                else:
                    n = state.adj[r][c]
                    if n > 0:
                        text = font.render(str(n), True, COLOR_NUM.get(n, COLOR_TEXT))
                        text_rect = text.get_rect(center = rect.center)
                        surf.blit(text, text_rect)
                    else:
                        pass
            else:
                if state.flagged[r][c]:
                    px = rect.x + CELL // 3
                    py = rect.y + CELL // 3
                    flag_pts = [(px, py + CELL // 2), (px, py), (px + CELL // 2, py + CELL // 4)]
                    pygame.draw.polygon(surf, COLOR_FLAG, flag_pts)

                if hover_cell is not None and (r, c) == hover_cell and not state.revealed[r][c] and not state.game_over:
                    pygame.draw.rect(surf, COLOR_HOVER, rect)

    for c in range(COLS + 1):
        x = c * CELL
        pygame.draw.line(surf, COLOR_GRID, (x, HUD_H), (x, HUD_H + BOARD_H), 1)

    for r in range(ROWS + 1):
        y = HUD_H + r * CELL
        pygame.draw.line(surf, COLOR_GRID, (0, y), (BOARD_W, y), 1)

def main():
    pygame.init()
    pygame.display.set_caption("Minesweeper")
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock = pygame.time.Clock()

    pygame.font.init()
    font = pygame.font.Font(None, 28)

    state = BoardState(ROWS, COLS, NUM_MINES)
    hover_cell = None
    elapsed_ms = 0
    timer_running = False

    running = True
    while running:
        dt = clock.tick(FPS)
        if timer_running and not state.game_over:
            elapsed_ms += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    state=BoardState(ROWS, COLS, NUM_MINES)
                    hover_cell = None
                    elapsed_ms = 0
                    timer_running = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                hover_cell = screen_to_cell(mx, my)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                cell = screen_to_cell(mx, my)
                if cell is not None:
                    r, c = cell
                    if event.button == 1:
                        if state.revealed[r][c]:
                            state.chord(r, c)
                        else:
                            if state.first_move and not state.game_over:
                                timer_running = True
                            state.reveal(r, c)
                    elif event.button == 3:
                        state.toggle_flag(r, c)

        screen.fill(COLOR_BG)
        draw_hud(screen, font, elapsed_ms // 1000, state)
        draw_board(screen, font, state, hover_cell)

        pygame.display.flip()
    
    pygame.quit()
    sys.exit()
    
if __name__ == "__main__":
    main()