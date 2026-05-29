from typing import List, Tuple
def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    i: int=current_pos[0]
    j: int=current_pos[1]
    if(i<49):
        if (current_board[i+1][j]=='.'):
            return (i+1, j,)
    if(j>0):
        if (current_board[i][j-1]=='.'):
            return (i, j-1,)
    if(j<49):
        if (current_board[i][j+1]=='.'):
            return (i, j+1,)
    if(i>0):
        if (current_board[i-1][j]=='.'):
            return (i-1, j,)
    if(j<49):
        if (current_board[i][j+1]==your_character):
            return (i, j+1,)
    if(i>0):
        if (current_board[i-1][j]==your_character):
            return (i-1, j,)
    if(i<49):
        if (current_board[i+1][j]==your_character):
            return (i+1, j,)
    if(j>0):
        if (current_board[i][j-1]==your_character):
            return (i, j-1,)