from typing import List, Tuple
import secrets
def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    Movimientox = [0, 1, 0, -1]
    Movimientoy = [1, 0, -1, 0]
    px = 0
    py = 0
    Color = your_character
    x = current_pos[0]
    y = current_pos[1]
    if current_board[0][0] == Color:
        px = 0
        py = 0
    if current_board[len(current_board) - 1][0] == Color:
        px = len(current_board) - 1
        py = 0
    if current_board[0][len(current_board) - 1] == Color:
        px = 0
        py = len(current_board) - 1
    if current_board[len(current_board) - 1][len(current_board) - 1] == Color:
        px = len(current_board) - 1
        py = len(current_board) - 1
    Posibles = []
    for i in range(4):
        nx = x + Movimientox[i]
        ny = y + Movimientoy[i]
        if not (nx >= 0 and nx < len(current_board) and ny >= 0 and ny < len(current_board[0])):
            continue
        if current_board[nx][ny] not in [Color, "."]:
            continue
        Posibles.append((nx, ny))
        if(current_board[nx][ny] == "."):
            Posibles.append((nx, ny))
            Posibles.append((nx, ny))
            Posibles.append((nx, ny))
            if(abs(nx - px) + abs(ny - py) > abs(x - px) + abs(y - py)):
                Posibles.append((nx, ny))
                Posibles.append((nx, ny))
                Posibles.append((nx, ny))
    A = secrets.randbelow(len(Posibles))
    return (Posibles[A][0], Posibles[A][1])