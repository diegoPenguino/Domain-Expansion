from typing import List, Tuple
import random

Board = List[List[str]]
Position = Tuple[int, int]

def get_moves(pos: Position):
    r, c = pos
    return [(r+1,c),   (r-1,c), (r,c+1),  (r,c-1)]

def is_valid(board: Board, move: Position, my_id: str):
    r, c = move


    if not (0 <= r < len(board) and 0 <= c < len(board[0])):
        return False
    return board[r][c]   == "." or board[r][c] == my_id

def score_move(board: Board, move: Position):
    r, c = move
    score = 0


    for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
        rr, cc = r+dr, c+dc
        if 0 <= rr < len(board) and 0 <= cc < len(board[0]):
            if board[rr][cc] == ".":
                score += 1
    return score

def next_step(board: Board, pos: Position):
    my_id = board[pos[0]][pos[1]]

    moves = get_moves(pos)
    valid = [m for m in moves if is_valid(board, m, my_id)]
    if not valid:
        return pos
    scores = [score_move(board, m) for m in valid]
    max_score = max(scores)

    best_moves = [m for m, s in zip(valid, scores) if s == max_score]
    return random.choice(best_moves)