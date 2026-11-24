"""Rules shared by the arcade window and automated checks."""
import random

DIGITS = set(range(1, 7))
CELLS = range(36)


def group(i):
    row, col = divmod(i, 6)
    return row, col, (row // 2, col // 3)


PEERS = [{j for j in CELLS if j != i and
          any(a == b for a, b in zip(group(i), group(j)))} for i in CELLS]


def count_solutions(board, limit=2):
    best = None
    for i, value in enumerate(board):
        if value:
            continue
        choices = DIGITS - {board[j] for j in PEERS[i]}
        if not choices:
            return 0
        if best is None or len(choices) < len(best[1]):
            best = i, choices
    if best is None:
        return int(all(board[i] not in {board[j] for j in PEERS[i]} for i in CELLS))
    index, choices = best
    count = 0
    for choice in choices:
        board[index] = choice
        count += count_solutions(board, limit - count)
        board[index] = 0
        if count >= limit:
            break
    return count


def puzzle(blanks, rng=random):
    digits = rng.sample(sorted(DIGITS), 6)
    rows = [2*b+r for b in rng.sample(range(3), 3) for r in rng.sample(range(2), 2)]
    cols = [3*b+c for b in rng.sample(range(2), 2) for c in rng.sample(range(3), 3)]
    answer = [digits[(3*r + r//2 + c) % 6] for r in rows for c in cols]
    board = answer.copy()
    removed = 0
    for i in rng.sample(list(CELLS), 36):
        board[i] = 0
        if count_solutions(board) == 1:
            removed += 1
        else:
            board[i] = answer[i]
        if removed == blanks:
            break
    return board, answer


PORTALS = {4:22, 13:34, 26:47, 42:64, 60:81, 78:96,
           28:8, 52:31, 68:48, 83:61, 94:71, 98:79}


def race_move(position, die):
    landing = position + die
    if landing > 100:
        return position, position
    return landing, PORTALS.get(landing, landing)


# Bubbles occupy staggered rows. Odd rows have one fewer socket.
def sockets(row):
    return range(10 - row % 2)


def center(cell):
    r, c = cell
    return 16 + 32*c + 16*(r % 2), 16 + 28*r


def neighbors(cell):
    r, c = cell
    shift = r % 2
    for nr, nc in ((r, c-1), (r, c+1), (r-1, c-1+shift), (r-1, c+shift),
                   (r+1, c-1+shift), (r+1, c+shift)):
        if nr >= 0 and nc in sockets(nr):
            yield nr, nc


def connected(board, seeds, color=None):
    stack = list(seeds)
    seen = set(stack)
    while stack:
        for other in neighbors(stack.pop()):
            if other in seen or other not in board:
                continue
            if color is None or board[other] == color:
                seen.add(other)
                stack.append(other)
    return seen


def attach(board, cell, color):
    board[cell] = color
    cluster = connected(board, [cell], color)
    if len(cluster) < 3:
        return 0
    for loc in cluster:
        del board[loc]
    anchored = connected(board, [loc for loc in board if loc[0] == 0])
    dropped = set(board) - anchored
    for loc in dropped:
        del board[loc]
    return len(cluster) + len(dropped)
