from typing import List, Tuple

direction = 1  # 1 = derecha, -1 = izquierda

def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:

    global direction

    r, c = current_pos
    rows = len(current_board)
    cols = len(current_board[0])

    def is_safe(nr, nc):
        if not (0 <= nr < rows and 0 <= nc < cols):
            return False

        if current_board[nr][nc] not in (".", your_character):
            return False
        return True


    next_c = c + direction
    if is_safe(r, next_c):
        return (r, next_c)


    next_r = r + 1
    if is_safe(next_r, c):
        direction *= -1
        return (next_r, c)


    moves = [
        (r, c + 1),
        (r + 1, c),
        (r, c - 1),
        (r - 1, c),
    ]

    enemy_positions = set(all_player_positions)
    enemy_positions.discard(current_pos)

    safe_moves = []
    for nr, nc in moves:
        if is_safe(nr, nc) and (nr, nc) not in enemy_positions:
            safe_moves.append((nr, nc))

    if safe_moves:
        return safe_moves[0]


    for nr, nc in moves:
        if 0 <= nr < rows and 0 <= nc < cols:
            return (nr, nc)

    return current_pos