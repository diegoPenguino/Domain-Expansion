"""
Explorador: va hacia donde puede llegar antes que sus rivales.

La idea: para cada movimiento posible, imagina que ya lo hizo y cuenta cuántas
casillas vacías alcanzaría ANTES que cualquier rival. Para eso usa búsqueda en
anchura (BFS), que calcula la distancia más corta caminando desde un punto:

  * un BFS desde la casilla nueva da "mi distancia" a cada casilla vacía;
  * un BFS desde todos los rivales a la vez da "su distancia" a cada casilla;
  * las casillas donde mi distancia es menor son "mías" (como un mapa de Voronoi).

Entre las casillas vacías vecinas, elige la que le deja más casillas "suyas". Así
gana una casilla en cada turno y se va hacia las zonas abiertas que le disputa menos
gente. Si no tiene ninguna vacía al lado, camina por su territorio hacia la más
cercana (otro BFS), para no perder turnos.

Truco: un bot vivo SIEMPRE cambia de posición, porque está obligado a moverse una
casilla por turno. Si un rival está en el mismo lugar que el turno anterior, está
eliminado (o su asiento está vacío) y no hay que preocuparse por él.
"""

import random
from collections import deque
from typing import List, Tuple

DIRECCIONES = [(-1, 0), (0, 1), (1, 0), (0, -1)]

posiciones_anteriores = None


def rivales_vivos(board, posiciones, yo):
    """Las posiciones de los rivales que se movieron desde el turno anterior."""
    global posiciones_anteriores
    vivos = []
    for i, pos in enumerate(posiciones):
        if str(i + 1) == yo:
            continue
        if board[pos[0]][pos[1]] == ".":
            continue  # asiento vacío: nadie empezó en esa esquina
        if posiciones_anteriores is None or posiciones_anteriores[i] != pos:
            vivos.append(pos)
    posiciones_anteriores = list(posiciones)
    return vivos


def distancias(board, inicios):
    """BFS por casillas vacías desde varias casillas a la vez."""
    filas, columnas = len(board), len(board[0])
    dist = {p: 0 for p in inicios}
    cola = deque(inicios)
    while cola:
        f, c = cola.popleft()
        for df, dc in DIRECCIONES:
            nf, nc = f + df, c + dc
            if 0 <= nf < filas and 0 <= nc < columnas and (nf, nc) not in dist and board[nf][nc] == ".":
                dist[(nf, nc)] = dist[(f, c)] + 1
                cola.append((nf, nc))
    return dist


def paso_hacia_vacio(board, pos, yo):
    """Primer paso del camino más corto (por casillas vacías o propias) a una vacía."""
    filas, columnas = len(board), len(board[0])
    previo = {pos: None}
    cola = deque([pos])
    while cola:
        actual = cola.popleft()
        if actual != pos and board[actual[0]][actual[1]] == ".":
            while previo[actual] != pos:
                actual = previo[actual]
            return actual
        for df, dc in DIRECCIONES:
            f, c = actual[0] + df, actual[1] + dc
            if 0 <= f < filas and 0 <= c < columnas and (f, c) not in previo and board[f][c] in (".", yo):
                previo[(f, c)] = actual
                cola.append((f, c))
    return None


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    filas = len(current_board)
    columnas = len(current_board[0])
    fila, columna = current_pos

    rivales = rivales_vivos(current_board, all_player_positions, your_character)
    dist_rivales = distancias(current_board, rivales)

    # Entre las casillas vacías vecinas, la que deja más casillas "mías".
    mejor, mejor_puntaje = None, -1
    for df, dc in DIRECCIONES:
        f, c = fila + df, columna + dc
        if not (0 <= f < filas and 0 <= c < columnas) or current_board[f][c] != ".":
            continue
        mias = distancias(current_board, [(f, c)])
        puntaje = sum(1 for p, d in mias.items() if d < dist_rivales.get(p, 10**9))
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = (f, c), puntaje
    if mejor is not None:
        return mejor

    # Ninguna vecina vacía: caminar por territorio propio hacia la vacía más cercana.
    paso = paso_hacia_vacio(current_board, current_pos, your_character)
    if paso is not None:
        return paso
    propias = [
        (fila + df, columna + dc)
        for df, dc in DIRECCIONES
        if 0 <= fila + df < filas and 0 <= columna + dc < columnas
        and current_board[fila + df][columna + dc] == your_character
    ]
    return random.choice(propias)
