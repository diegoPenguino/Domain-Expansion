from typing import List, Tuple
import random

def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    x, y = current_pos

    def inside(nx, ny):
        return 0 <= nx < 50 and 0 <= ny < 50

    cont=0
    for i in current_board:
        for j in i:
            if j==your_character:
                cont+=1

    if(current_board[0][0]==your_character and cont<25):
        if inside(x, y+1): return x,y+1
    elif(current_board[0][49]==your_character and cont<25):
        if inside(x, y-1): return x,y-1
    elif(current_board[49][0]==your_character and cont<25):
        if inside(x, y+1): return x,y+1
    elif(current_board[49][49]==your_character and cont<25):
        if inside(x, y-1): return x,y-1

    elif(current_board[0][0]==your_character and cont<46):
        if inside(x+1,y): return x+1,y
    elif(current_board[0][49]==your_character and cont<46):
        if inside(x+1,y): return x+1,y
    elif(current_board[49][0]==your_character and cont<46):
        if inside(x-1,y): return x-1,y
    elif(current_board[49][49]==your_character and cont<46):
        if inside(x-1,y): return x-1,y
    
    elif(current_board[0][0]==your_character and cont<75 and inside(x,y-1) and current_board[x][y-1]=='.'):
        return x,y-1
    elif(current_board[0][49]==your_character and cont<75 and inside(x,y+1) and current_board[x][y+1]=='.'):
        return x,y+1
    elif(current_board[49][0]==your_character and cont<75 and inside(x,y-1) and current_board[x][y-1]=='.'):
        return x,y-1
    elif(current_board[49][49]==your_character and cont<75 and inside(x,y+1) and current_board[x][y+1]=='.'):
        return x,y+1

    elif(current_board[0][0]==your_character and cont<100 and inside(x-1,y) and current_board[x-1][y]=='.'):
        return x-1,y
    elif(current_board[0][49]==your_character and cont<100 and inside(x-1,y) and current_board[x-1][y]=='.'):
        return x-1,y
    elif(current_board[49][0]==your_character and cont<100 and inside(x+1,y) and current_board[x+1][y]=='.'):
        return x+1,y
    elif(current_board[49][49]==your_character and cont<100 and inside(x+1,y) and current_board[x+1][y]=='.'):
        return x+1,y
    
    else:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if inside(nx, ny) and current_board[nx][ny] == '.':
            return nx, ny

    while True:
        dx, dy = random.choice(directions)
        nx, ny = x + dx, y + dy
        if inside(nx, ny) and current_board[nx][ny] == your_character:
            return nx, ny