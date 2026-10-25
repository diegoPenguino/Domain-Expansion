"""
Prudente: dibuja rectángulos, pero solo del tamaño que alcanza a cerrar a tiempo.

Es el bot Rectángulos con una idea más: el riesgo. Mientras dibuja un rectángulo,
el interior todavía no es suyo. Si un rival llega antes de que lo cierre, puede
meterse adentro y arruinarle el lazo (o robarle el espacio).

La idea:
  1. Con búsqueda en anchura (BFS) desde cada rival vivo, calcula en cuántos turnos
     puede llegar alguno a cada casilla. Un rival solo camina por casillas vacías y por
     su propio territorio: no puede atravesar el de otros.
  2. Para cada rectángulo posible, cuenta cuántos pasos le faltan para pasar por
     cada casilla del borde. Si un rival llega a alguna antes que él (con un margen),
     ese rectángulo es demasiado arriesgado.
  3. Entre los seguros, elige el que gana más casillas nuevas por paso (las vacías del
     borde y las del interior, contadas con sumas acumuladas para que sea rápido).
  4. Revisa el peligro en cada turno: si el plan se volvió arriesgado, lo cambia.

Lejos de los rivales dibuja rectángulos grandes; cerca de ellos, chicos y rápidos.

Un resultado que sorprende: medido en partidas reales, Prudente gana MENOS que
Rectángulos. En este juego los rivales casi nunca cortan un lazo a propósito, así
que la prudencia cuesta más (rectángulos más chicos) de lo que protege. Prueba a
cambiar MARGEN o TAMANO_MAXIMO y mira qué pasa: ¿hay un punto medio que gane más?

Truco: un bot vivo SIEMPRE cambia de posición, porque está obligado a moverse una
casilla por turno. Si un rival no se movió desde el turno anterior, está eliminado
(o su asiento está vacío) y no hay que preocuparse por él.
"""

from collections import deque
from typing import List, Tuple

DIRECCIONES = [(-1, 0), (0, 1), (1, 0), (0, -1)]
TAMANO_MAXIMO = 18
TAMANO_MINIMO = 2
MARGEN = 1  # turnos de ventaja que exige sobre el rival más cercano
# Caminando hacia lo vacío se gana 1 casilla por paso. Un rectángulo tiene que ganar
# bastante más, o conviene caminar primero hasta el borde del territorio propio.
VALOR_MINIMO = 2.0

plan = []
posiciones_anteriores = None


def libre(board, f, c, yo):
    return 0 <= f < len(board) and 0 <= c < len(board[0]) and board[f][c] in (".", yo)


def rivales_vivos(board, posiciones, yo):
    """(posición, letra) de los rivales que se movieron desde el turno anterior."""
    global posiciones_anteriores
    vivos = []
    for i, pos in enumerate(posiciones):
        letra = str(i + 1)
        if letra == yo or board[pos[0]][pos[1]] == ".":
            continue
        if posiciones_anteriores is None or posiciones_anteriores[i] != pos:
            vivos.append((pos, letra))
    posiciones_anteriores = list(posiciones)
    return vivos


def llegada_rivales(board, rivales):
    """Turnos que tarda el rival más cercano en llegar a cada casilla vacía. Cada rival
    solo puede caminar por casillas vacías y por su propio territorio, así que se hace
    un BFS por rival y se queda con el menor."""
    filas, columnas = len(board), len(board[0])
    llegada = {}
    for inicio, letra in rivales:
        dist = {inicio: 0}
        cola = deque([inicio])
        while cola:
            f, c = cola.popleft()
            for df, dc in DIRECCIONES:
                nf, nc = f + df, c + dc
                if 0 <= nf < filas and 0 <= nc < columnas and (nf, nc) not in dist and board[nf][nc] in (".", letra):
                    dist[(nf, nc)] = dist[(f, c)] + 1
                    cola.append((nf, nc))
        for casilla, d in dist.items():
            if d < llegada.get(casilla, 10**9):
                llegada[casilla] = d
    return llegada


def rectangulo(inicio, d1, d2, lado):
    camino = []
    f, c = inicio
    for (df, dc) in (d1, d2, (-d1[0], -d1[1]), (-d2[0], -d2[1])):
        for _ in range(lado):
            f, c = f + df, c + dc
            camino.append((f, c))
    return camino


def es_seguro(camino, llegada, board, yo):
    """Cada casilla vacía del camino tiene que pisarse antes de que llegue un rival."""
    for pasos, (f, c) in enumerate(camino, start=1):
        if not libre(board, f, c, yo):
            return False
        if board[f][c] == "." and llegada.get((f, c), 10**9) <= pasos + MARGEN:
            return False
    return True


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


def buscar_plan(board, pos, yo, llegada):
    S = sumas_vacias(board)
    mejor, mejor_valor = [], VALOR_MINIMO
    for lado in range(TAMANO_MAXIMO, TAMANO_MINIMO - 1, -1):
        for d1 in DIRECCIONES:
            for d2 in DIRECCIONES:
                if d1[0] * d2[0] + d1[1] * d2[1] != 0:
                    continue
                camino = rectangulo(pos, d1, d2, lado)
                if not es_seguro(camino, llegada, board, yo):
                    continue
                vacias_del_borde = sum(1 for f, c in camino if board[f][c] == ".")
                gana = ganancia(S, pos, d1, d2, lado, vacias_del_borde)
                if gana / len(camino) > mejor_valor:
                    mejor, mejor_valor = camino, gana / len(camino)
    return mejor


def paso_hacia_vacio(board, pos, yo):
    """Sin rectángulo seguro: primer paso hacia la casilla vacía más cercana."""
    previo = {pos: None}
    cola = deque([pos])
    while cola:
        actual = cola.popleft()
        if actual != pos and board[actual[0]][actual[1]] == ".":
            while previo[actual] != pos:
                actual = previo[actual]
            return actual
        for df, dc in DIRECCIONES:
            sig = (actual[0] + df, actual[1] + dc)
            if sig not in previo and libre(board, sig[0], sig[1], yo):
                previo[sig] = actual
                cola.append(sig)
    return None


def paso_seguro(board, pos, yo, llegada):
    """Sin rectángulo seguro: ir a la casilla vacía vecina más lejos de los rivales."""
    f, c = pos
    opciones = []
    for df, dc in DIRECCIONES:
        nf, nc = f + df, c + dc
        if libre(board, nf, nc, yo):
            vacia = board[nf][nc] == "."
            opciones.append((vacia, llegada.get((nf, nc), 10**9), (nf, nc)))
    opciones.sort(reverse=True)
    return opciones[0][2]


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    global plan
    yo = your_character
    rivales = rivales_vivos(current_board, all_player_positions, yo)
    llegada = llegada_rivales(current_board, rivales)

    # Seguir el plan si sigue siendo seguro; si no, buscar otro desde aquí.
    if plan and es_seguro(plan, llegada, current_board, yo):
        return plan.pop(0)

    plan = buscar_plan(current_board, current_pos, yo, llegada)
    if plan:
        return plan.pop(0)
    return paso_hacia_vacio(current_board, current_pos, yo) or paso_seguro(current_board, current_pos, yo, llegada)
