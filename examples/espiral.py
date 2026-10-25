"""
Espiral: avanza en línea recta y gira a la derecha cuando se bloquea.

La idea: empieza recorriendo el borde del tablero en el sentido de las agujas del
reloj. Cuando la casilla de enfrente ya no está vacía (porque llegó al borde, a su
propio camino o al territorio de otro), gira a la derecha. Así dibuja una espiral
hacia adentro.

Tiene memoria: la variable global `direccion` guarda hacia dónde iba en el turno
anterior. Las variables globales se conservan durante toda la partida.

Truco del juego: si logra dar la vuelta completa al borde, encierra todo el centro
del tablero. Pero con rivales en las otras esquinas casi nunca lo consigue.
"""

from typing import List, Tuple

# En orden de las agujas del reloj: girar a la derecha es pasar a la siguiente.
DIRECCIONES = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # arriba, derecha, abajo, izquierda

direccion = None


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    global direccion
    filas = len(current_board)
    columnas = len(current_board[0])
    fila, columna = current_pos

    def casilla(d):
        df, dc = DIRECCIONES[d]
        return fila + df, columna + dc

    def dentro(f, c):
        return 0 <= f < filas and 0 <= c < columnas

    if direccion is None:
        # Desde cada esquina, la dirección que recorre el borde en sentido horario.
        arriba = fila == 0
        izquierda = columna == 0
        if arriba and izquierda:
            direccion = 1  # derecha
        elif arriba:
            direccion = 2  # abajo
        elif izquierda:
            direccion = 0  # arriba
        else:
            direccion = 3  # izquierda

    # 1. Seguir de frente o girar a la derecha hasta encontrar una casilla vacía.
    for giro in range(4):
        d = (direccion + giro) % 4
        f, c = casilla(d)
        if dentro(f, c) and current_board[f][c] == ".":
            direccion = d
            return f, c

    # 2. No hay vacías alrededor: caminar por territorio propio, con el mismo orden.
    for giro in range(4):
        d = (direccion + giro) % 4
        f, c = casilla(d)
        if dentro(f, c) and current_board[f][c] == your_character:
            direccion = d
            return f, c

    # No debería pasar: la casilla de la que vino siempre es propia.
    return casilla(direccion)
