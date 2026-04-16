from typing import List, Tuple


_initialized = False
_side_length = 4
_segment_index = 0
_steps_in_segment = 0


def _reset_path(side_length: int) -> None:
    global _side_length, _segment_index, _steps_in_segment
    _side_length = side_length
    _segment_index = 0
    _steps_in_segment = 0


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    del all_player_positions, your_character

    global _initialized, _segment_index, _steps_in_segment

    if not _initialized:
        rows = len(current_board)
        cols = len(current_board[0]) if rows > 0 else 0
        max_safe_side = min(max(1, rows - 2), max(1, cols - 2), 8)
        _reset_path(max_safe_side)
        _initialized = True

    # From bottom-right corner, trace a square: up -> left -> down -> right.
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
    dr, dc = directions[_segment_index]
    next_pos = (current_pos[0] + dr, current_pos[1] + dc)

    _steps_in_segment += 1
    if _steps_in_segment >= _side_length:
        _steps_in_segment = 0
        _segment_index = (_segment_index + 1) % 4

    return next_pos
