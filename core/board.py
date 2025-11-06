from collections import defaultdict
from .grid import HexGrid

C_COVERED = 0
C_REVEALED = 1
C_FLAGGED = 2
C_BLOCKED = 3

class Tile:
    __slots__ = ("q", "r", "state", "is_mine", "number")
    def __init__(self, q, r):
        self.q = q
        self.r = r
        self.state = C_COVERED
        self.is_mine = False
        self.number = 0

class Board:
    def __init__(self, grid, stage_data):
        self.grid = grid
        self.tiles = {(q, r):Tile(q, r) for (q, r) in grid.cells}
        self.apply_stage(stage_data)
        self.compute_numbers()

    def apply_stage(self, st):
        mines = set(map(tuple, st.get("mines", [])))
        blocked = set(map(tuple, st.get("blocked", [])))
        for coord, tile in self.tiles.items():
            if coord in blocked:
                tile.state = C_BLOCKED
            if coord in mines:
                tile.is_mine = True
        
    def compute_numbers(self):
        for(q, r), t in self.tiles.items():
            if t.is_mine:
                t.number = -1
                continue
            cnt = 0
            for nq, nr in self.grid.neighbors(q, r):
                if self.tiles[(nq, nr)].is_mine:
                    cnt += 1
            t.number = cnt

    def reveal(self, q, r):
        tile = self.tiles.get((q, r))
        if not tile or tile.state in (C_REVEALED, C_BLOCKED):
            return "noop"
        if tile.is_mine:
            return "boom"
        self.flood_open(q, r)
        return "ok"
    
    def toggle_flag(self, q, r):
        tile = self.tiles.get((q, r))
        if not tile or tile.state == C_REVEALED or tile.state == C_BLOCKED:
            return
        tile.state = C_FLAGGED if tile.state == C_COVERED else C_COVERED

    def flood_open(self, q, r):
        stack = [(q, r)]
        while stack:
            cq, cr = stack.pop()
            t = self.tiles.get((cq, cr))
            if not t or t.state in(C_REVEALED, C_BLOCKED):
                continue
            if t.is_mine:
                continue
            t.state = C_REVEALED
            if t.number == 0:
                for nq, nr in self.grid.neighbors(cq, cr):
                    nt = self.tiles[(nq, nr)]
                    if nt.state == C_COVERED and not nt.is_mine:
                        stack.append((nq, nr))