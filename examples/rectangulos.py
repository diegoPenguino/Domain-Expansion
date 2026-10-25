"""
Rectángulos: sale de su territorio, dibuja un rectángulo y lo cierra.

La regla clave del juego: si tus casillas forman un lazo cerrado, todo lo vacío de
adentro pasa a ser tuyo. Un rectángulo de lado L cuesta unos 4·L pasos y encierra
(L-1)·(L-1) casillas: mucho más que una casilla por turno.

La idea:
  1. Desde la casilla actual (que siempre es propia), prueba rectángulos que tengan
     una esquina ahí, de distintos tamaños y hacia distintos lados.
  2. Descarta los que tienen en el borde una casilla de otro jugador o fuera del tablero.
  3. Para cada uno calcula cuántas casillas NUEVAS ganaría (las vacías del borde y las
     del interior) y se queda con el que gana más por cada paso.
  4. Recorre ese borde paso a paso. Al volver a la esquina de partida, el lazo se
     cierra y el interior es suyo.
  5. Si alguien se mete en el camino, abandona el plan y busca otro rectángulo
     desde donde está. Su propio camino ya es territorio suyo, así que siempre
     está "en casa".
  6. Un rectángulo solo vale la pena si gana al menos dos casillas por paso: caminando
     hacia lo vacío ya se gana una por paso. Si ninguno lo logra (por ejemplo, porque
     está en medio de su propio territorio), camina hacia la casilla vacía más cercana
     y prueba de nuevo desde ahí.

Ojo: el borde del tablero NO sirve de pared. Solo cuentan tus propias casillas.
"""

from collections import deque
from typing import List, Tuple

DIRECCIONES = [(-1, 0), (0, 1), (1, 0), (0, -1)]
TAMANO_MAXIMO = 14
TAMANO_MINIMO = 2
# Caminando hacia lo vacío se gana 1 casilla por paso. Un rectángulo tiene que ganar
# bastante más, o conviene caminar primero hasta el borde del territorio propio.
VALOR_MINIMO = 2.0

plan = []  # casillas que faltan recorrer del rectángulo actual


def libre(board, f, c, yo):
    return 0 <= f < len(board) and 0 <= c < len(board[0]) and board[f][c] in (".", yo)


def rectangulo(inicio, d1, d2, lado):
    """El borde de un rectángulo con una esquina en `inicio`: avanza en d1, luego en
    d2, vuelve en -d1 y termina volviendo en -d2 hasta la esquina de partida."""
    camino = []
    f, c = inicio
    for (df, dc) in (d1, d2, (-d1[0], -d1[1]), (-d2[0], -d2[1])):
        for _ in range(lado):
            f, c = f + df, c + dc
            camino.append((f, c))
    return camino


def sumas_vacias(board):
    """Sumas acumuladas de casillas vacías: S[f][c] cuenta las vacías del rectángulo que
    va de (0, 0) a (f - 1, c - 1). Con ellas, las vacías de cualquier rectángulo se
    cuentan con 4 operaciones en vez de recorrer todas sus casillas."""
    filas, columnas = len(board), len(board[0])
    S = [[0] * (columnas + 1) for _ in range(filas + 1)]
    for f in range(filas):
        en_fila = 0
        for c in range(columnas):
            en_fila += board[f][c] == "."
            S[f + 1][c + 1] = S[f][c + 1] + en_fila
    return S


def vacias_en(S, f0, c0, f1, c1):
    """Casillas vacías entre las filas f0..f1 y las columnas c0..c1 (inclusive)."""
    if f0 > f1 or c0 > c1:
        return 0
    return S[f1 + 1][c1 + 1] - S[f0][c1 + 1] - S[f1 + 1][c0] + S[f0][c0]


def ganancia(S, inicio, d1, d2, lado, vacias_del_borde):
    """Casillas que gana al cerrar el rectángulo: las vacías del borde que pisa más
    las vacías del interior, que quedan encerradas."""
    f, c = inicio
    f2, c2 = f + lado * (d1[0] + d2[0]), c + lado * (d1[1] + d2[1])
    interior = vacias_en(S, min(f, f2) + 1, min(c, c2) + 1, max(f, f2) - 1, max(c, c2) - 1)
    return vacias_del_borde + interior


def buscar_plan(board, pos, yo):
    S = sumas_vacias(board)
    mejor, mejor_valor = [], VALOR_MINIMO
    for lado in range(TAMANO_MAXIMO, TAMANO_MINIMO - 1, -1):
        for d1 in DIRECCIONES:
            for d2 in DIRECCIONES:
                if d1[0] * d2[0] + d1[1] * d2[1] != 0:
                    continue  # d2 tiene que ser perpendicular a d1
                camino = rectangulo(pos, d1, d2, lado)
                if not all(libre(board, f, c, yo) for f, c in camino):
                    continue
                vacias_del_borde = sum(1 for f, c in camino if board[f][c] == ".")
                gana = ganancia(S, pos, d1, d2, lado, vacias_del_borde)
                if gana / len(camino) > mejor_valor:
                    mejor, mejor_valor = camino, gana / len(camino)
    return mejor


def paso_hacia_vacio(board, pos, yo):
    """Primer paso del camino más corto (por casillas libres) a una casilla vacía."""
    previo = {pos: None}
    cola = deque([pos])
    while cola:
        actual = cola.popleft()
        if board[actual[0]][actual[1]] == "." and actual != pos:
            while previo[actual] != pos:
                actual = previo[actual]
            return actual
        for df, dc in DIRECCIONES:
            sig = (actual[0] + df, actual[1] + dc)
            if sig not in previo and libre(board, sig[0], sig[1], yo):
                previo[sig] = actual
                cola.append(sig)
    return None


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    global plan
    yo = your_character

    # Seguir el plan mientras la siguiente casilla siga libre.
    if plan and libre(current_board, plan[0][0], plan[0][1], yo):
        return plan.pop(0)

    plan = buscar_plan(current_board, current_pos, yo)
    if plan:
        return plan.pop(0)

    # Ningún rectángulo cabe aquí: caminar hacia la casilla vacía más cercana.
    paso = paso_hacia_vacio(current_board, current_pos, yo)
    if paso:
        return paso
    # Sin casillas vacías alcanzables: moverse por territorio propio.
    f, c = current_pos
    for df, dc in DIRECCIONES:
        if libre(current_board, f + df, c + dc, yo):
            return f + df, c + dc
    return f + 1, c
