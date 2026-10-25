"""
Paseante: el bot más simple que nunca pierde por un movimiento inválido.

La idea: en cada turno mira sus cuatro vecinos (arriba, derecha, abajo, izquierda)
y elige uno al azar, pero solo entre los que son seguros:

  * una casilla vacía (".") la conquista;
  * una casilla propia la puede pisar sin problema;
  * salirse del tablero o pisar territorio ajeno lo elimina, así que las evita.

Prefiere las casillas vacías, porque cada una que pisa suma un punto. Si no hay
ninguna vacía al lado, vuelve sobre su propio territorio. Siempre existe al menos
una casilla propia vecina: la de la que vino.
"""

import random
from typing import List, Tuple

DIRECCIONES = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # arriba, derecha, abajo, izquierda


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    filas = len(current_board)
    columnas = len(current_board[0])
    fila, columna = current_pos

    vacias = []
    propias = []
    for df, dc in DIRECCIONES:
        f, c = fila + df, columna + dc
        if not (0 <= f < filas and 0 <= c < columnas):
            continue  # fuera del tablero
        if current_board[f][c] == ".":
            vacias.append((f, c))
        elif current_board[f][c] == your_character:
            propias.append((f, c))

    if vacias:
        return random.choice(vacias)
    return random.choice(propias)
