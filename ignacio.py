
import random
from typing import List, Tuple, Set
#ILD
# Memoria de casillas donde hubo enemigos
historial_enemigos: Set[Tuple[int, int]] = set()

def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    global historial_enemigos
    
    filas = len(current_board)
    columnas = len(current_board[0]) if filas > 0 else 0

    # Guardar enemgos
    for f in range(filas):
        for c in range(columnas):
            celda = current_board[f][c]
            if celda != '.' and celda != your_character:
                historial_enemigos.add((f, c))

    # evitar choques con enemigos
    zona_peligro: Set[Tuple[int, int]] = set()
    for pos_enemigo in all_player_positions:
        if pos_enemigo != current_pos:
            ef, ec = pos_enemigo
            zona_peligro.add((ef - 1, ec))
            zona_peligro.add((ef + 1, ec))
            zona_peligro.add((ef, ec - 1))
            zona_peligro.add((ef, ec + 1))

    f_act, c_act = current_pos
    movimientos_validos = []
    movimientos_ganadores = []
    
    # bucar legales
    direcciones = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    for df, dc in direcciones:
        nf, nc = f_act + df, c_act + dc
        
        if 0 <= nf < filas and 0 <= nc < columnas:
            celda_destino = current_board[nf][nc]
            
            # Solo vacio o nuestro propio territorio
            if celda_destino == '.' or celda_destino == your_character:
                if (nf, nc) in historial_enemigos or (nf, nc) in zona_peligro:
                    continue  
                
                movimientos_validos.append((nf, nc))
                if celda_destino == '.':
                    movimientos_ganadores.append((nf, nc))
                    
    # Priorida
    if movimientos_ganadores:
        return random.choice(movimientos_ganadores)

    # salir de mi territorio
    pos_objetivo = None
    distancia_min = float('inf')
    
    for f2 in range(filas):
        for c2 in range(columnas):
            if current_board[f2][c2] == '.':
                dist = abs(f2 - f_act) + abs(c2 - c_act)
                if dist < distancia_min:
                    distancia_min = dist
                    pos_objetivo = (f2, c2)
                    
    # si hay salida -> salir :V
    if pos_objetivo:
        of, oc = pos_objetivo
        
        # ve a y
        if oc != c_act:
            paso_c = 1 if oc > c_act else -1
            mov_x = (f_act, c_act + paso_c)
            if mov_x in movimientos_validos:
                return mov_x
                
        # ve a x
        if of != f_act:
            paso_f = 1 if of > f_act else -1
            mov_y = (f_act + paso_f, c_act)
            if mov_y in movimientos_validos:
                return mov_y

    # movimiento aux
    if movimientos_validos:
        return random.choice(movimientos_validos)
    
    # harakiri
    emergencia = random.randint(1, 4)
    if emergencia == 1:
        return (f_act - 1, c_act)   
    elif emergencia == 2:
        return (f_act, c_act + 1)   
    elif emergencia == 3:
        return (f_act + 1, c_act)   
    return (f_act, c_act - 1)
