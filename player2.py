from typing import List, Tuple
import random


def next_step(
    board: List[List[str]],
    current_pos: Tuple[int, int],
    players: List[Tuple[int, int]],
    your_id: str,
) -> Tuple[int, int]:

    n = len(board)
    m = len(board[0])

    moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    random.shuffle(moves)

    for dx, dy in moves:
        nx = current_pos[0] + dx
        ny = current_pos[1] + dy

        if 0 <= nx < n and 0 <= ny < m and board[nx][ny] == ".":
            return (nx, ny)

    return current_pos
