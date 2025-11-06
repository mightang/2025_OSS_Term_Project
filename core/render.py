import pygame
from .hexmath import axial_to_pixel, hex_corners
from .board import C_BLOCKED, C_COVERED, C_FLAGGED, C_REVEALED

COL_BG      = (18, 20, 24)
COL_GRID    = (55, 60, 70)
COL_COVERED = (38, 44, 52)
COL_BLOCKED = (24, 26, 30)
COL_REVEAL  = (210, 214, 220)
COL_MINE    = (220, 70, 70)
COL_FLAG    = (230, 180, 60)
COL_TEXT    = (30, 30, 35)

def draw_board(surface, board, center, size, font):
    cx, cy = center
    for (q, r), t in board.tiles.items():
        x, y = axial_to_pixel(q, r, size)
        x += cx
        y += cy
        poly = hex_corners((x, y), size - 1)

        if t.state == C_BLOCKED:
            fill = COL_BLOCKED
        elif t.state == C_COVERED:
            fill = COL_COVERED
        elif t.is_mine and t.state == 1:
            fill = COL_MINE
        else:
            fill = COL_REVEAL
        
        pygame.draw.polygon(surface, fill, poly)
        pygame.draw.polygon(surface, COL_GRID, poly, width = 1)

        if t.state == 2:
            pygame.draw.circle(surface, COL_FLAG, (int(x), int(y)), max(3, int(size * 0.35)))

        if t.state == 1 and (not t.is_mine) and t.number > 0:
            text = font.render(str(t.number), True, COL_TEXT)
            rect = text.get_rect(center = (x, y))
            surface.blit(text, rect)