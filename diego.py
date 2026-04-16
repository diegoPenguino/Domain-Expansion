from typing import List, Tuple


EMPTY = "."

# Direction order is clockwise: up -> right -> down -> left.
_DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]

_initialized = False
_direction_idx = 3  # Start moving left from bottom-right spawn.
_visited: set[Tuple[int, int]] = set()
_board_shape: Tuple[int, int] = (0, 0)


def _reset_state(rows: int, cols: int, current_pos: Tuple[int, int]) -> None:
    global _initialized, _direction_idx, _visited, _board_shape
    _initialized = True
    _direction_idx = 3
    _visited = {current_pos}
    _board_shape = (rows, cols)


def _is_legal(
    board: List[List[str]],
    pos: Tuple[int, int],
    your_character: str,
) -> bool:
    r, c = pos
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0
    if r < 0 or c < 0 or r >= rows or c >= cols:
        return False
    cell = board[r][c]
    return cell in (EMPTY, your_character)


def _neighbor(pos: Tuple[int, int], direction_idx: int) -> Tuple[int, int]:
    dr, dc = _DIRECTIONS[direction_idx]
    return (pos[0] + dr, pos[1] + dc)


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    del all_player_positions

    global _initialized, _direction_idx, _visited, _board_shape

    rows = len(current_board)
    cols = len(current_board[0]) if rows > 0 else 0

    if (not _initialized) or _board_shape != (rows, cols):
        _reset_state(rows, cols, current_pos)
    else:
        _visited.add(current_pos)

    # First pass: keep direction if possible, else rotate clockwise,
    # prioritizing cells we have not visited yet.
    for turn in range(4):
        candidate_dir = (_direction_idx + turn) % 4
        candidate_pos = _neighbor(current_pos, candidate_dir)
        if not _is_legal(current_board, candidate_pos, your_character):
            continue
        if candidate_pos in _visited:
            continue
        _direction_idx = candidate_dir
        return candidate_pos

    # Second pass: if every legal move is already visited, allow revisiting.
    for turn in range(4):
        candidate_dir = (_direction_idx + turn) % 4
        candidate_pos = _neighbor(current_pos, candidate_dir)
        if not _is_legal(current_board, candidate_pos, your_character):
            continue
        _direction_idx = candidate_dir
        return candidate_pos

    # No legal move available; return current position so simulator eliminates us.
    return current_pos
