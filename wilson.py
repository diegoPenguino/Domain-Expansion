from typing import List, Tuple
import random 
def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    # Implementa la lógica para determinar el siguiente paso del juego
    # Usa la información del tablero y las posiciones de todos los jugadores
    directions = [
        (1, 0),   # abajo
        (-1, 0),  # arriba
        (0, 1),   # derecha
        (0, -1),  # izquierda
    ]
    for _ in range(len(directions)):
        dx, dy = random.choice(directions)
        next_pos = (current_pos[0] + dx, current_pos[1] + dy)

        if next_pos not in all_player_positions:
            return next_pos

    # Si todas las posiciones aleatorias están ocupadas, permanecer en el mismo lugar
    return current_pos
