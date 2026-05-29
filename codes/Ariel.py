from typing import List, Tuple
import random

def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    # Implementa la lógica para determinar el siguiente paso del juego
    # Puedes usar la información del tablero actual y la posición actual para tomar una decisión
    """up=0
    down=0
    left=0
    right=0
    r1=0
    r2=0
    if current_pos[0]+1<len(current_board):
        up=1
    elif current_pos[0]-1<len(current_board):
        down=1
    if current_pos[1]+1<len(current_board[1]):
        right=1
    elif current_pos[1]-1<len(current_board[1]):
        left=1
    if up==1 and down==1:
        if left==1 and right==1:
            rd=random.randint(0,1)
            if rd==0:
                r2=random.randint(-1,0)
                if r2==0:
                    r2=1
            else:
                r1=random.randint(-1,0)
                if r1==0:
                    r1=1
        elif left==0 and right==1:
            rd=random.randint(0,1)
            if rd==0:
                r2=1
            else:
                r1=random.randint(-1,0)
                if r1==0:
                    r1=1
        elif left==1 and right==0:
            rd=random.randint(0,1)
            if rd==0:
                r2=-1
            else:
                r1=random.randint(-1,0)
                if r1==0:
                    r1=1
        elif left==0 and right==0:
            r1=random.randint(-1,0)
            if r1==0:
                r1=1
    if up==0 and down==1:
        if left==1 and right==1:
            rd=random.randint(0,1)
            if rd==0:
                r2=random.randint(-1,0)
                if r2==0:
                    r2=1
            else:
                r1=1
        elif left==0 and right==1:
            rd=random.randint(0,1)
            if rd==0:
                r2=1
            else:
                r1=1
        elif left==1 and right==0:
            rd=random.randint(0,1)
            if rd==0:
                r2=-1
            else:
                r1=1
        elif left==0 and right==0:
            r1=1
    if up==1 and down==0:
        if left==1 and right==1:
            rd=random.randint(0,1)
            if rd==0:
                r2=random.randint(-1,0)
                if r2==0:
                    r2=1
            else:
                r1=-1
        elif left==0 and right==1:
            rd=random.randint(0,1)
            if rd==0:
                r2=1
            else:
                r1=-1
        elif left==1 and right==0:
            rd=random.randint(0,1)
            if rd==0:
                r2=-1
            else:
                r1=-1
        elif left==0 and right==0:
            r1=-1
    if up==0 and down==0:
        if left==1 and right==1:
            r2=random.randint(-1,0)
            if r2==0:
                r2=1
        elif left==0 and right==1:
            r2=1
        elif left==1 and right==0:
            e2=-1
        elif left==0 and right==0:
            r1=1
    """
    rd=random.randint(0,1)
    r1=0
    r2=0
    if rd==0:
        r1=random.randint(-1,1)
        if r1==0:
            r1=1
    else:
        r2=random.randint(-1,1)
        if r2==0:
            r2=1
    return (
        current_pos[0]+r1,
        current_pos[1]+r2,
    )
