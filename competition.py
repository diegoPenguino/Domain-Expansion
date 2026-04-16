from simulator import run_program
from itertools import permutations as perms

PLAYERS = ["MrPython", "mia", "ignacio", "ming"]
# PLAYERS = ["Ariel", "matilde", "Niconiconi", "santi"]
# PLAYERS = ["wilson", "diego", "candiositos", "Gabriel"]

# PLAYERS = ["mia", "Niconiconi", "candiositos", "Gabriel"]

total_score = {player: 0 for player in PLAYERS}


if __name__ == "__main__":
    permutations = list(perms(PLAYERS))
    print(f"Total permutations: {len(permutations)}")
    for idx, perm in enumerate(permutations):
        print(f"Running permutation {idx + 1}/{len(permutations)}")
        result = run_program(players=perm)
        for player, score in result["territory"].items():
            total_score[player] += score

        print(f"Scores for this permutation: {result['territory']}")

    print("\nTotal scores after all permutations:")
    for player in PLAYERS:
        print(f"{player}: {total_score[player]}")

    print("GANADOR: ", max(total_score, key=total_score.get))
    print("SEGUNDO LUGAR: ", sorted(total_score, key=total_score.get, reverse=True)[1])
