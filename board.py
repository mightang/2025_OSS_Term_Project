C_COVERED  = 0
C_REVEALED = 1
C_FLAGGED  = 2
C_BLOCKED  = 3

class Tile:
    __slots__ = ("is_mine","number","state")
    def __init__(self):
        self.is_mine = False
        self.number  = 0
        self.state   = C_COVERED

class Board:
    def __init__(self, grid, stage_data):
        self.grid = grid
        self.stage = stage_data
        self.tiles = {pos: Tile() for pos in grid.cells}

        # 게임 상태
        self.first_click_done = False
        self.is_game_over = False
        self.is_win = False
        self.mistakes = 0  # ← 실수 횟수

        # 차단/지뢰 배치
        for q, r in stage_data.get("blocked", []):
            if (q, r) in self.tiles:
                self.tiles[(q, r)].state = C_BLOCKED
        for q, r in stage_data.get("mines", []):
            if (q, r) in self.tiles and self.tiles[(q, r)].state != C_BLOCKED:
                self.tiles[(q, r)].is_mine = True

        self._recompute_numbers()

        for q, r in stage_data.get("start_revealed", []):
            if (q, r) in self.tiles:
                t = self.tiles[(q, r)]
                if t.state != C_BLOCKED and not t.is_mine:
                    t.state = C_REVEALED

        for q, r in stage_data.get("start_flagged", []):
            if (q, r) in self.tiles:
                t = self.tiles[(q, r)]
                if t.state != C_BLOCKED:
                    t.state = C_FLAGGED

        self._recompute_counters()
        self._check_win_and_update()

    def _neighbors(self, q, r):
        for nq, nr in self.grid.neighbors(q, r):
            yield (nq, nr)

    def _recompute_numbers(self):
        for (q, r), t in self.tiles.items():
            if t.state == C_BLOCKED:
                t.number = 0
                continue
            if t.is_mine:
                t.number = -1
                continue
            cnt = 0
            for (nq, nr) in self._neighbors(q, r):
                if self.tiles[(nq, nr)].is_mine:
                    cnt += 1
            t.number = cnt

    def _recompute_counters(self):
        self.total_cells = sum(1 for t in self.tiles.values() if t.state != C_BLOCKED)
        self.total_mines = sum(1 for t in self.tiles.values() if t.is_mine and t.state != C_BLOCKED)
        self.flag_count  = sum(1 for t in self.tiles.values() if t.state == C_FLAGGED)
        self.revealed_count = sum(1 for t in self.tiles.values() if t.state == C_REVEALED and not t.is_mine and t.state != C_BLOCKED)
        self.mines_left = max(0, self.total_mines - self.flag_count)

    def toggle_flag(self, q, r):
        if self.is_game_over:
            return
        t = self.tiles.get((q, r))
        if not t or t.state in (C_REVEALED, C_BLOCKED):
            return

        if t.state == C_COVERED:
            # 커버드 → 플래그 로 전환할 때만 실수 판정
            if not t.is_mine:
                self.mistakes += 1   # 안전칸에 깃발 = 실수 +1
            t.state = C_FLAGGED
        elif t.state == C_FLAGGED:
            # 플래그 해제는 실수로 치지 않음
            t.state = C_COVERED

        self._recompute_counters()

    def reveal(self, q, r):
        """좌클릭 오픈: 지뢰여도 게임오버 없이 그 칸만 공개 + mistakes++"""
        if self.is_game_over: return None
        if (q, r) not in self.tiles: return None
        t = self.tiles[(q, r)]
        if t.state in (C_FLAGGED, C_BLOCKED, C_REVEALED): return None

        if t.is_mine:
            # 게임오버 금지: 이 칸만 드러내고 실수 +1
            self.mistakes += 1
            self._recompute_counters()
            self._check_win_and_update()
            return "mine"
        
        t.state = C_REVEALED
        # (0이면 연쇄 오픈 로직이 있다면 이어서 호출)
        self._recompute_counters()
        self._check_win_and_update()
        return "ok"

        self._recompute_counters()
        # 승리 판정(선택): 모든 비지뢰 공개 시 승리 유지
        all_safe = all(
            (tt.state == C_REVEALED) if (not tt.is_mine and tt.state != C_BLOCKED) else True
            for tt in self.tiles.values()
        )
        if all_safe:
            self.is_game_over = True
            self.is_win = True
        return "ok"

    def reset_reveals_and_flags(self):
        self.first_click_done = False
        self.is_game_over = False
        self.is_win = False
        self.mistakes = 0
        for t in self.tiles.values():
            if t.state != C_BLOCKED:
                t.state = C_COVERED
        self._recompute_counters()

    def _all_safe_revealed(self) -> bool:
        for t in self.tiles.values():
            if t.state == C_BLOCKED:
                continue
            if (not t.is_mine) and t.state != C_REVEALED:
                return False
        return True

    def _all_mines_flagged(self) -> bool:
        for t in self.tiles.values():
            if t.state == C_BLOCKED:
                continue
            if t.is_mine and t.state != C_FLAGGED:
                return False
        return True

    def _check_win_and_update(self):
        if self._all_safe_revealed() and self._all_mines_flagged():
            self.is_game_over = True
            self.is_win = True
