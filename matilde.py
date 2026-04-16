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

    posibles = []

    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if abs(dx) + abs(dy) != 1:
                continue

            nx = current_pos[0] + dx
            ny = current_pos[1] + dy

            if 0 <= nx < n and 0 <= ny < m and board[nx][ny] == ".":
                posibles.append((nx, ny))

    if posibles:
        return random.choice(posibles)

    return current_pos