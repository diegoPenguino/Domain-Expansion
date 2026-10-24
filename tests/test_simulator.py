import pytest

from simulator import (
    BOTS_DIR,
    EMPTY,
    BotLoadError,
    TerritoryWarSimulator,
    load_bot_file,
    load_bot_from_source,
)


def make_pacer():
    """A bot that steps out of its corner and back forever, so it never dies."""
    home = None

    def next_step(board, pos, positions, me):
        nonlocal home
        if home is None:
            home = pos
        if pos != home:
            return home
        r, c = pos
        return (r, c + 1) if c == 0 else (r, c - 1)

    return next_step


def pacers(n):
    return [make_pacer() for _ in range(n)]


def make_sim(rows=6, cols=6, bots=None):
    bots = bots or pacers(4)
    return TerritoryWarSimulator(rows, cols, bots)


def board_from(rows):
    return [list(row) for row in rows]


# Movement rules


def test_players_start_in_the_corners():
    sim = make_sim(rows=4, cols=5)
    assert sim.players["1"].pos == (0, 0)
    assert sim.players["2"].pos == (0, 4)
    assert sim.players["3"].pos == (3, 0)
    assert sim.players["4"].pos == (3, 4)


def test_valid_step_claims_the_cell():
    sim = make_sim()
    sim.apply_move("1", (0, 1))
    assert sim.players["1"].alive
    assert sim.players["1"].pos == (0, 1)
    assert sim.board[0][1] == "1"


def test_stepping_back_onto_own_territory_is_allowed():
    sim = make_sim()
    sim.apply_move("1", (0, 1))
    sim.apply_move("1", (0, 0))
    assert sim.players["1"].alive


@pytest.mark.parametrize(
    "move, reason",
    [
        ((1, 1), "invalid move"),  # diagonal
        ((0, 2), "invalid move"),  # two cells
        ((-1, 0), "out of bounds"),
        ("up", "invalid move"),
        (None, "invalid move"),
        ([0, 1], "invalid move"),  # a list, not a tuple
        (ValueError("boom"), "error: ValueError: boom"),
    ],
)
def test_bad_moves_eliminate_the_player(move, reason):
    sim = make_sim()
    sim.apply_move("1", move)
    assert not sim.players["1"].alive
    assert sim.players["1"].death_reason.startswith(reason)
    assert sim.players["1"].pos == (0, 0)


def test_stepping_on_another_players_territory_eliminates():
    sim = make_sim(rows=2, cols=3)
    sim.board[0][1] = "2"
    sim.apply_move("1", (0, 1))
    assert not sim.players["1"].alive
    assert sim.players["1"].death_reason.startswith("collision")
    assert sim.board[0][1] == "2"


def test_bot_exception_eliminates_and_keeps_the_message():
    def crash(board, pos, positions, me):
        raise RuntimeError("bad bot")

    sim = make_sim(bots=[crash, *pacers(3)])
    sim.step()
    assert not sim.players["1"].alive
    assert sim.players["1"].death_reason == "error: RuntimeError: bad bot"


def test_relative_move_format():
    sim = TerritoryWarSimulator(6, 6, pacers(4), move_format="relative")
    sim.apply_move("1", (1, 0))
    assert sim.players["1"].pos == (1, 0)


def test_bot_gets_a_copy_of_the_board():
    def vandal(board, pos, positions, me):
        board[3][3] = me
        return pos

    sim = make_sim(bots=[vandal, *pacers(3)])
    sim.step()
    assert sim.board[3][3] == EMPTY


# Enclosure


def test_enclosed_empty_area_is_captured():
    sim = make_sim(rows=5, cols=5)
    sim.board = board_from(
        [
            "111..",
            "1.1..",
            "1....",
            ".....",
            ".....",
        ]
    )
    sim.players["1"].pos = (2, 0)
    sim.apply_move("1", (2, 1))
    sim.apply_move("1", (2, 2))
    assert sim.board[1][1] == "1"
    assert sim.board[2][3] == EMPTY


def test_area_open_to_the_edge_is_not_captured():
    sim = make_sim(rows=5, cols=5)
    sim.board = board_from(
        [
            ".1...",
            ".1...",
            ".....",
            ".....",
            ".....",
        ]
    )
    sim.players["1"].pos = (1, 1)
    sim.apply_move("1", (2, 1))
    assert sim.board[0][0] == EMPTY


def test_enclosure_keeps_other_players_cells():
    sim = make_sim(rows=5, cols=5)
    sim.board = board_from(
        [
            "1111.",
            "1.21.",
            "1..1.",
            "111..",
            ".....",
        ]
    )
    sim.players["1"].pos = (3, 2)
    sim.apply_move("1", (3, 3))
    assert sim.board[1][1] == "1"
    assert sim.board[2][2] == "1"
    assert sim.board[1][2] == "2"


# Turns and end of game


def test_step_plays_every_alive_player_once():
    calls = []

    def recorder(board, pos, positions, me):
        calls.append(me)
        return pos

    sim = make_sim(bots=[recorder] * 4)
    sim.players["3"].alive = False
    assert sim.step()
    assert sim.turn == 1
    assert calls == ["1", "2", "4"]


def test_game_ends_when_everyone_is_dead():
    sim = make_sim()
    for player in sim.players.values():
        player.alive = False
    assert sim.is_finished()
    assert not sim.step()
    assert sim.turn == 0


def test_game_ends_when_the_board_is_full():
    sim = make_sim(rows=2, cols=2)
    assert sim.is_finished()


def test_run_respects_max_turns_and_reports_results():
    sim = TerritoryWarSimulator(4, 4, pacers(4), ["a", "b", "c", "d"])
    result = sim.run(max_turns=7)
    assert result["turns"] == 7
    assert result["alive"] == {"1": True, "2": True, "3": True, "4": True}
    assert result["territory"] == {"a": 2, "b": 2, "c": 2, "d": 2}
    assert result["death_reasons"] == {"1": None, "2": None, "3": None, "4": None}


# Loading bots


COUNTER_BOT = """
calls = 0

def next_step(board, pos, positions, me):
    global calls
    calls += 1
    return pos
"""


def test_load_bot_from_source():
    next_step = load_bot_from_source("def next_step(b, p, ps, me):\n    return p\n")
    assert next_step([], (2, 3), [], "1") == (2, 3)


def test_each_load_gets_its_own_globals():
    first = load_bot_from_source(COUNTER_BOT, "counter")
    second = load_bot_from_source(COUNTER_BOT, "counter")
    first(None, (0, 0), [], "1")
    first(None, (0, 0), [], "1")
    second(None, (0, 0), [], "1")
    assert first.__globals__["calls"] == 2
    assert second.__globals__["calls"] == 1


def test_bot_main_block_does_not_run():
    source = "if __name__ == '__main__':\n    raise SystemExit\ndef next_step(b, p, ps, me):\n    return p\n"
    load_bot_from_source(source)


@pytest.mark.parametrize(
    "source, message",
    [
        ("def next_step(:\n", "SyntaxError"),
        ("raise ValueError('nope')\n", "ValueError: nope"),
        ("x = 1\n", "must define a next_step function"),
        ("next_step = 5\n", "must define a next_step function"),
    ],
)
def test_bad_bot_source_raises_bot_load_error(source, message):
    with pytest.raises(BotLoadError, match=message):
        load_bot_from_source(source, "broken")


@pytest.mark.parametrize(
    "name", sorted(p.stem for p in BOTS_DIR.glob("*.py") if p.stem != "__init__")
)
def test_every_bot_in_codes_loads_and_plays(name):
    next_step = load_bot_file(name)
    sim = TerritoryWarSimulator(50, 50, [next_step, *pacers(3)])
    for _ in range(5):
        sim.step()
    assert sim.turn == 5


def test_missing_bot_file_raises_bot_load_error():
    with pytest.raises(BotLoadError, match="No bot named 'nobody'"):
        load_bot_file("nobody")
