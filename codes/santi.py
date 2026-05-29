from typing import List, Tuple


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    r, c = current_pos;
    n = len(current_board)
    m = len(current_board[0])
    if current_pos == (0, 0):
        return (0, 1)
    if current_pos == (0, m-1):
        return (0, m-2)
    if current_pos == (n-1, 0):
        return (n-1, 1)
    if current_pos == (n-1, m-1):
        return (n-1, m-2)
    
    moves = [(0,1), (1,0), (0,-1), (-1,0)]

    for i, (er, ec) in enumerate(all_player_positions):
        if str(i+1) == your_character:
            continue

        dist = abs(r - er) + abs(c - ec)

        if dist <= 2:
            best_move = None
            best_dist = dist

            for dr, dc in moves:
                nr, nc = r + dr, c + dc

                if 0 <= nr < n and 0 <= nc < m:
                    if current_board[nr][nc] in (".", your_character):
                        
                        new_dist = abs(nr - er) + abs(nc - ec)

                        if new_dist > best_dist:
                            best_dist = new_dist
                            best_move = (nr, nc)

            if best_move:
                return best_move

    if c-1 >= 0 and current_board[r][c-1] == your_character:
        if r-1 >= 0 and current_board[r-1][c] == '.':
            return (r-1, c)
        if r+1 < len(current_board) and current_board[r+1][c] == '.':
            return (r+1, c)
    
    if c-1 >= 0 and current_board[r][c-1] == '.' and r-1 >= 0 and current_board[r-1][c] == '.':
        return (r, c-1) 
    moves = [(r, c+1), (r+1, c), (r, c-1), (r-1, c)]

    for nr, nc in moves:
        if 0 <= nr < n and 0 <= nc < m:
            if current_board[nr][nc] == ".":
                return (nr, nc)

    return (
        current_pos[0],
        current_pos[1] + 1,
    )

