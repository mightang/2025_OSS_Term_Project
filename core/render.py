import pygame
from .hexmath import axial_to_pixel, hex_corners
from .board import C_BLOCKED, C_COVERED, C_FLAGGED, C_REVEALED
from settings import (
    COL_BG, COL_GRID, COL_COVERED, COL_BLOCKED,COL_REVEAL, COL_MINE, COL_TEXT, COL_FLAG_TILE,
    COL_BTN_BG, COL_BTN_BORDER, COL_BTN_TEXT, COL_BTN_RETRY, COL_BTN_MENU, COL_BTN_NEXT
)

def draw_board(surface, board, center, size, font):
    cx, cy = center
    for (q, r), t in board.tiles.items():
        x, y = axial_to_pixel(q, r, size)
        x += cx
        y += cy
        corners = hex_corners((x, y), size - 1)

        if t.state == C_BLOCKED:
            fill = COL_BLOCKED
        elif t.state == C_FLAGGED:
            fill = COL_FLAG_TILE
        elif t.state == C_COVERED:
            fill = COL_COVERED
        elif t.state == C_REVEALED:
            fill = COL_REVEAL
        else:
            fill = COL_COVERED
        
        pygame.draw.polygon(surface, fill, corners)
        pygame.draw.polygon(surface, COL_GRID, corners, width = 1)

        if t.state == C_REVEALED and (not t.is_mine):
            text = font.render(str(t.number), True, COL_TEXT)
            rect = text.get_rect(center = (x, y))
            surface.blit(text, rect)

def draw_topright_info(surface, board, font, pad=12):
    w, _ = surface.get_size()
    s = f"남은 지뢰 {board.mines_left}   실수 {board.mistakes}"
    img = font.render(s, True, COL_TEXT)
    rect = img.get_rect(topright=(w - pad, pad))
    surface.blit(img, rect)

def draw_success_modal(surface, stage_label:str, mistakes:int, font, *, pad=20):
    """클리어 모달을 그린다. 반환값: 버튼명→Rect 딕셔너리"""
    w, h = surface.get_size()

    # 1) 어둡게 덮는 오버레이(반투명)
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    # 2) 패널(중앙)
    panel_w, panel_h = 520, 300
    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (w // 2, h // 2)

    # 패널 배경/테두리
    pygame.draw.rect(surface, COL_REVEAL, panel_rect, border_radius=16)
    pygame.draw.rect(surface, COL_GRID, panel_rect, width=2, border_radius=16)

    # 3) 텍스트들
    y = panel_rect.top + pad
    title = font.render(f"Stage: {stage_label}", True, COL_TEXT)
    surface.blit(title, (panel_rect.left + pad, y))
    y += title.get_height() + 8

    msg = font.render("성공! 클리어를 축하합니다.", True, COL_TEXT)
    surface.blit(msg, (panel_rect.left + pad, y))
    y += msg.get_height() + 6

    mist = font.render(f"실수 횟수: {mistakes}", True, COL_TEXT)
    surface.blit(mist, (panel_rect.left + pad, y))

    # 4) 버튼들 (가로 3개)
    btn_w, btn_h = 130, 44
    gap = 20
    total_w = btn_w * 3 + gap * 2
    start_x = panel_rect.centerx - total_w // 2
    btn_y = panel_rect.bottom - pad - btn_h

    def button(x, y, label, bg = COL_BTN_BG, border = COL_BTN_BORDER, text = COL_BTN_TEXT):
        r = pygame.Rect(x, y, btn_w, btn_h)
        pygame.draw.rect(surface, bg, r, border_radius=10)
        pygame.draw.rect(surface, border, r, width=2, border_radius=10)
        t = font.render(label, True, COL_TEXT)
        surface.blit(t, t.get_rect(center=r.center))
        return r

    rects = {}
    rects["retry"] = button(start_x, btn_y, "재시도", bg = COL_BTN_RETRY)
    rects["menu"]  = button(start_x + btn_w + gap, btn_y, "메뉴", bg = COL_BTN_MENU)
    rects["next"]  = button(start_x + (btn_w + gap) * 2, btn_y, "다음 스테이지", bg = COL_BTN_NEXT)

    return rects
