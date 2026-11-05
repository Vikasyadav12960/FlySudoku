"""4x4 Mini Sudoku environment. The solver is used only by the puzzle generator."""
from __future__ import annotations
import random
from typing import Optional

SIZE = 4
DIGITS = (1, 2, 3, 4)
Board = list[list[int]]

def valid(board: Board, row: int, col: int, value: int) -> bool:
    if value not in DIGITS or not (0 <= row < 4 and 0 <= col < 4):
        return False
    if board[row][col] != 0:
        return False
    if value in board[row]:
        return False
    if any(board[r][col] == value for r in range(4)):
        return False
    br, bc = (row // 2) * 2, (col // 2) * 2
    return not any(board[r][c] == value for r in range(br, br + 2) for c in range(bc, bc + 2))

def count_solutions(board: Board, limit: int = 2) -> int:
    work = [row[:] for row in board]
    def search() -> int:
        best = None
        best_options = None
        for r in range(4):
            for c in range(4):
                if work[r][c] == 0:
                    opts = [v for v in DIGITS if valid(work, r, c, v)]
                    if best is None or len(opts) < len(best_options):
                        best, best_options = (r, c), opts
                    if not opts:
                        return 0
        if best is None:
            return 1
        total = 0
        r, c = best
        for v in best_options:
            work[r][c] = v
            total += search()
            work[r][c] = 0
            if total >= limit:
                break
        return total
    return search()

def solve_one(board: Board) -> Optional[Board]:
    work = [row[:] for row in board]
    def search() -> bool:
        for r in range(4):
            for c in range(4):
                if work[r][c] == 0:
                    for v in DIGITS:
                        if valid(work, r, c, v):
                            work[r][c] = v
                            if search():
                                return True
                            work[r][c] = 0
                    return False
        return True
    return [row[:] for row in work] if search() else None

class SudokuEnv:
    """Agent-facing environment. Feedback is rule validity and terminal completion only."""
    def __init__(self, seed: int = 0, clues: int = 7):
        self.rng = random.Random(seed)
        self.clues = max(4, min(12, clues))
        self.board: Board = []
        self.solution: Board = []
        self.fixed: set[tuple[int, int]] = set()
        self.done = False
        self.reset()

    def reset(self) -> Board:
        # Generate a random valid full grid using randomized backtracking.
        grid = [[0] * 4 for _ in range(4)]
        def fill() -> bool:
            blanks = [(r, c) for r in range(4) for c in range(4) if grid[r][c] == 0]
            if not blanks:
                return True
            r, c = self.rng.choice(blanks)
            vals = list(DIGITS)
            self.rng.shuffle(vals)
            for v in vals:
                if valid(grid, r, c, v):
                    grid[r][c] = v
                    if fill():
                        return True
                    grid[r][c] = 0
            return False
        if not fill():
            raise RuntimeError("Puzzle generator failed to construct a valid grid.")
        self.solution = [row[:] for row in grid]
        positions = [(r, c) for r in range(4) for c in range(4)]
        self.rng.shuffle(positions)
        target = self.clues
        puzzle = [[0] * 4 for _ in range(4)]
        for r, c in positions:
            if sum(v != 0 for row in puzzle for v in row) >= target:
                break
            puzzle[r][c] = self.solution[r][c]
        # Keep only puzzles with a unique solution; add clues if needed.
        remaining = positions[target:]
        while count_solutions(puzzle) != 1 and remaining:
            r, c = remaining.pop()
            puzzle[r][c] = self.solution[r][c]
        self.board = puzzle
        self.fixed = {(r, c) for r in range(4) for c in range(4) if puzzle[r][c]}
        self.done = False
        return self.observation()

    def observation(self) -> Board:
        return [row[:] for row in self.board]

    def legal_actions(self) -> list[tuple[int, int, int]]:
        return [(r, c, v) for r in range(4) for c in range(4)
                if self.board[r][c] == 0 for v in DIGITS if valid(self.board, r, c, v)]

    def step(self, action: tuple[int, int, int]) -> tuple[Board, float, bool, str]:
        if self.done:
            return self.observation(), 0.0, True, "Episode already complete."
        r, c, v = action
        if (r, c) in self.fixed:
            return self.observation(), -2.0, False, "Clue cells cannot be changed."
        if not (0 <= r < 4 and 0 <= c < 4 and v in DIGITS) or self.board[r][c] != 0:
            return self.observation(), -1.0, False, "Invalid cell or digit."
        if not valid(self.board, r, c, v):
            return self.observation(), -1.0, False, "Rule violation: duplicate in row, column or box."
        # A locally legal but incorrect placement is permitted; the agent must discover consequences.
        self.board[r][c] = v
        if all(self.board[i][j] for i in range(4) for j in range(4)):
            if self.board == self.solution:
                self.done = True
                return self.observation(), 20.0, True, "Puzzle solved."
            self.done = True
            return self.observation(), -5.0, True, "Board filled but solution is incorrect."
        return self.observation(), 1.0, False, "Locally valid placement."

    def is_solved(self) -> bool:
        return self.done and self.board == self.solution
