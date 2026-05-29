from typing import List, Tuple
import random
def next_step(current_board:List[List[str]],current_pos:Tuple[int, int],all_player_positions:List[Tuple[int, int]],your_character:str)->Tuple[int, int]:
    # Implementa la lógica para determinar el siguiente paso del juego
    # Puedes usar la información del tablero actual y la posición actual para tomar una decisión
    #ir 13 derecha y 12 abajo
    #pos 12 y 11
    de=13
    ab=12
    if(your_character=="1"):
        if(current_pos[0]==0 and current_pos[1]<de-1 and (current_board[1][1]!=your_character)):
            return (current_pos[0],current_pos[1]+1)
        if(current_pos[0]<ab-1 and current_pos[1]==de-1 and (current_board[1][1]!=your_character)):
            return (current_pos[0]+1,current_pos[1])
        if(current_pos[0]==ab-1 and current_pos[1]>0 and (current_board[1][1]!=your_character)):
            return (current_pos[0],current_pos[1]-1)
        if(current_pos[0]>0 and current_pos[1]==0 and (current_board[1][1]!=your_character)):
            return (current_pos[0]-1,current_pos[1])
    elif(your_character=="2"):
        if(current_pos[0]==0 and current_pos[1]>49-de+1 and (current_board[1][48]!=your_character)):
            return (current_pos[0],current_pos[1]-1)
        if(current_pos[0]<ab-1 and current_pos[1]==49-de+1 and (current_board[1][48]!=your_character)):
            return (current_pos[0]+1,current_pos[1])
        if(current_pos[0]==ab-1 and current_pos[1]<49 and (current_board[1][48]!=your_character)):
            return (current_pos[0],current_pos[1]+1)
        if(current_pos[0]>0 and current_pos[1]==49 and (current_board[1][48]!=your_character)):
            return (current_pos[0]-1,current_pos[1])
    elif(your_character=="3"):
        if(current_pos[0]==49 and current_pos[1]<de-1 and current_board[48][1]!=your_character):
            return (current_pos[0],current_pos[1]+1)
        if(current_pos[0]>49-ab+1 and current_pos[1]==de-1 and current_board[48][1]!=your_character):
            return (current_pos[0]-1,current_pos[1])
        if(current_pos[0]==49-ab+1 and current_pos[1]>0 and current_board[48][1]!=your_character):
            return (current_pos[0],current_pos[1]-1)
        if(current_pos[0]<49 and current_pos[1]==0 and current_board[48][1]!=your_character):
            return (current_pos[0]+1,current_pos[1])
    else:
        if(current_pos[0]==49 and current_pos[1]>49-de+1 and current_board[48][48]!=your_character):
            return (current_pos[0],current_pos[1]-1)
        if(current_pos[0]>49-ab+1 and current_pos[1]==49-de+1 and current_board[48][48]!=your_character):
            return (current_pos[0]-1,current_pos[1])
        if(current_pos[0]==49-ab+1 and current_pos[1]<49 and current_board[48][48]!=your_character):
            return (current_pos[0],current_pos[1]+1)
        if(current_pos[0]<49 and current_pos[1]==49 and current_board[48][48]!=your_character):
            return (current_pos[0]+1,current_pos[1])
    #return (current_pos[0]+1,current_pos[1])
    if((your_character=="1" or your_character=="2") and current_pos[0]<=ab-1):
        return (current_pos[0]+1,current_pos[1])
    if((your_character=="3" or your_character=="4") and current_pos[0]>=49-ab+1):
        return (current_pos[0]-1,current_pos[1])
    posi=[(1,0),(-1,0),(0,1),(0,-1)]
    # ab,arr,de,iz
    chance=[]
    chance2=[]
    for i in range(4):
        nuepos=tuple(current_pos)
        nuepos[0]+=posi[i][0]
        nuepos[1]+=posi[i][1]
        if(nuepos[0]<0 or nuepos[0]>=50 or nuepos[1]<0 or nuepos[1]>=50):
            continue
        if(current_board[nuepos[0]][nuepos[1]]!="." and current_board[nuepos[0]][nuepos[1]]!=your_character):
            continue
        xd=True
        for j in range(4):
            if(j==(int(your_character)-1)):
                continue
            dist=abs(all_player_positions[j][0]-nuepos[0])+abs(all_player_positions[j][1]-nuepos[1])
            if(dist==2):
                xd=False
                break
        if(not xd):
            continue
        if(current_board[nuepos[0]][nuepos[1]]=="."):
            chance.append(nuepos)
        else:
            chance2.append(nuepos)
    if(len(chance)!=0):
        move=random.randint(0,len(chance)-1)
        return chance[move]
    move=random.randint(0,len(chance2)-1)
    return chance2[move]