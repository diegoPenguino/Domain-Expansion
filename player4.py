from typing import List, Tuple


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    # Implementa la lógica para determinar el siguiente paso del juego
    # Puedes usar la información del tablero actual y la posición actual para tomar una decisión

    return (
        current_pos[0],
        current_pos[1] - 1,
    )
