from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Dict, List, Sequence, Tuple, TypedDict, cast


Board = List[List[str]]
Position = Tuple[int, int]
Move = Tuple[int, int]
NextStepFn = Callable[[Board, Position, List[Position], str], Move]

EMPTY = "."

# Simulation constants (edit these values directly to configure matches)
DEFAULT_ROWS = 25
DEFAULT_COLS = 25
DEFAULT_MAX_TURNS = DEFAULT_COLS * DEFAULT_ROWS
DEFAULT_REALTIME = True
DEFAULT_FRAME_DELAY_SECONDS = 0.1
DEFAULT_RENDER_MODE = "turn"  # Allowed: "turn", "move"
DEFAULT_RENDER_BACKEND = "pygame"  # Allowed: "terminal", "pygame"
DEFAULT_PLAYERS = ["player1", "player2", "player3", "player4"]
MOVE_FORMAT = "absolute"  # Allowed: "absolute", "relative"

PLAYER_COLORS = {
    EMPTY: (22, 22, 26),
    "1": (232, 78, 65),
    "2": (248, 171, 72),
    "3": (78, 173, 96),
    "4": (61, 149, 214),
}


@dataclass
class PlayerState:
    player_id: str
    next_step: NextStepFn
    pos: Position
    alive: bool = True


class SimulationResult(TypedDict):
    turns: int
    board: Board
    alive: Dict[str, bool]
    positions: Dict[str, Position]
    territory: Dict[str, int]


class TerritoryWarSimulator:
    def __init__(
        self,
        rows: int,
        cols: int,
        player_functions: Sequence[NextStepFn],
        move_format: str = "absolute",
    ):
        if len(player_functions) != 4:
            raise ValueError("Exactly 4 player functions are required")
        if rows < 2 or cols < 2:
            raise ValueError("Board must be at least 2x2")
        if move_format not in ("absolute", "relative"):
            raise ValueError("move_format must be 'absolute' or 'relative'")

        self.rows = rows
        self.cols = cols
        self.move_format = move_format
        self.board: Board = [[EMPTY for _ in range(cols)] for _ in range(rows)]

        corners: List[Position] = [
            (0, 0),
            (0, cols - 1),
            (rows - 1, 0),
            (rows - 1, cols - 1),
        ]

        self.players: Dict[str, PlayerState] = {}
        for i, next_step in enumerate(player_functions, start=1):
            pid = str(i)
            pos = corners[i - 1]
            self.players[pid] = PlayerState(player_id=pid, next_step=next_step, pos=pos)
            self.board[pos[0]][pos[1]] = pid

        self.turn = 0

    def run(
        self,
        max_turns: int = 200,
        realtime: bool = False,
        frame_delay: float = 0.12,
        render_mode: str = "turn",
        render_backend: str = "terminal",
    ) -> SimulationResult:
        if frame_delay < 0:
            raise ValueError("frame_delay must be >= 0")
        if render_mode not in ("turn", "move"):
            raise ValueError("render_mode must be 'turn' or 'move'")
        if render_backend not in ("terminal", "pygame"):
            raise ValueError("render_backend must be 'terminal' or 'pygame'")

        pygame_renderer: PygameRenderer | None = None
        render_enabled = realtime

        if render_enabled and render_backend == "pygame":
            try:
                pygame_renderer = PygameRenderer(self.rows, self.cols)
            except ImportError:
                print("pygame is not installed. Falling back to terminal renderer.")
                render_backend = "terminal"

        if render_enabled:
            render_enabled = self._render_frame(render_backend, pygame_renderer)
            time.sleep(frame_delay)

        for _ in range(max_turns):
            if self._finished():
                break

            self.turn += 1
            for pid in ("1", "2", "3", "4"):
                player = self.players[pid]
                if player.alive:
                    self._play_turn(player)

                if render_enabled and render_mode == "move":
                    render_enabled = self._render_frame(render_backend, pygame_renderer)
                    time.sleep(frame_delay)

            if render_enabled and render_mode == "turn":
                render_enabled = self._render_frame(render_backend, pygame_renderer)
                time.sleep(frame_delay)

        if (
            render_enabled
            and render_backend == "pygame"
            and pygame_renderer is not None
        ):
            pygame_renderer.wait_until_closed(self.board, self.turn, self.players)

        if pygame_renderer is not None:
            pygame_renderer.close()

        result: SimulationResult = {
            "turns": self.turn,
            "board": self.board,
            "alive": {pid: p.alive for pid, p in self.players.items()},
            "positions": {pid: p.pos for pid, p in self.players.items()},
            "territory": self.territory_count(),
        }
        return result

    def _render_frame(
        self,
        render_backend: str,
        pygame_renderer: PygameRenderer | None,
    ) -> bool:
        if render_backend == "terminal":
            render_terminal(self.board, self.turn, self.players, clear_screen=True)
            return True

        if pygame_renderer is None:
            return False
        return pygame_renderer.render(self.board, self.turn, self.players)

    def territory_count(self) -> Dict[str, int]:
        counts = {"1": 0, "2": 0, "3": 0, "4": 0}
        for row in self.board:
            for cell in row:
                if cell in counts:
                    counts[cell] += 1
        return counts

    def _finished(self) -> bool:
        any_alive = any(player.alive for player in self.players.values())
        any_empty = any(EMPTY in row for row in self.board)
        return (not any_alive) or (not any_empty)

    def _play_turn(self, player: PlayerState) -> None:
        move = self._safe_next_step(player)
        if move is None:
            player.alive = False
            return

        target_pos = self._resolve_target_position(player.pos, move)
        if target_pos is None:
            player.alive = False
            return

        nr, nc = target_pos

        if not self._in_bounds(nr, nc):
            player.alive = False
            return

        target = self.board[nr][nc]

        if target not in (EMPTY, player.player_id):
            player.alive = False
            return

        player.pos = (nr, nc)
        self.board[nr][nc] = player.player_id
        self._capture_enclosed_empty(player.player_id)

    def _safe_next_step(self, player: PlayerState) -> Move | None:
        board_snapshot = [row[:] for row in self.board]
        all_player_positions = [self.players[pid].pos for pid in ("1", "2", "3", "4")]
        try:
            move = player.next_step(
                board_snapshot,
                player.pos,
                all_player_positions,
                player.player_id,
            )
        except Exception:
            return None

        if (
            not isinstance(move, tuple)
            or len(move) != 2
            or not isinstance(move[0], int)
            or not isinstance(move[1], int)
        ):
            return None

        return move

    def _capture_enclosed_empty(self, player_id: str) -> None:
        reachable = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        q: deque[Position] = deque()

        def try_push(r: int, c: int) -> None:
            if reachable[r][c]:
                return
            if self.board[r][c] == player_id:
                return
            reachable[r][c] = True
            q.append((r, c))

        for r in range(self.rows):
            try_push(r, 0)
            try_push(r, self.cols - 1)
        for c in range(self.cols):
            try_push(0, c)
            try_push(self.rows - 1, c)

        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if not self._in_bounds(rr, cc):
                    continue
                if reachable[rr][cc]:
                    continue
                if self.board[rr][cc] == player_id:
                    continue
                reachable[rr][cc] = True
                q.append((rr, cc))

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == EMPTY and not reachable[r][c]:
                    self.board[r][c] = player_id

    def _in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def _is_adjacent_move(self, dr: int, dc: int) -> bool:
        # Only allow one-step orthogonal moves: up, down, left, right.
        return (abs(dr) + abs(dc)) == 1

    def _resolve_target_position(
        self, current_pos: Position, move: Move
    ) -> Position | None:
        r, c = current_pos
        mr, mc = move

        if self.move_format == "relative":
            if self._is_adjacent_move(mr, mc):
                return (r + mr, c + mc)
            return None

        # absolute mode
        dr = mr - r
        dc = mc - c
        if self._is_adjacent_move(dr, dc):
            return (mr, mc)
        return None


def import_player_functions(
    module_names: Sequence[str],
) -> Tuple[NextStepFn, NextStepFn, NextStepFn, NextStepFn]:
    if len(module_names) != 4:
        raise ValueError("Exactly 4 module names are required")

    def load(module_name: str) -> NextStepFn:
        module = import_module(module_name)
        next_step = getattr(module, "next_step", None)
        if next_step is None or not callable(next_step):
            raise AttributeError(
                f"Module '{module_name}' must define callable next_step"
            )
        return cast(NextStepFn, next_step)

    next_step_player1 = load(module_names[0])
    next_step_player2 = load(module_names[1])
    next_step_player3 = load(module_names[2])
    next_step_player4 = load(module_names[3])

    return (
        next_step_player1,
        next_step_player2,
        next_step_player3,
        next_step_player4,
    )


def print_board(board: Board) -> None:
    for row in board:
        print(" ".join(row))


def render_terminal(
    board: Board,
    turn: int,
    players: Dict[str, PlayerState],
    clear_screen: bool = True,
) -> None:
    symbol = {
        EMPTY: " .",
        "1": " 1",
        "2": " 2",
        "3": " 3",
        "4": " 4",
    }
    alive_text = " | ".join(
        f"P{pid}: {'ALIVE' if p.alive else 'DEAD '}" for pid, p in players.items()
    )

    positions = " | ".join(
        f"P{pid} Pos: ({p.pos[0]:02d},{p.pos[1]:02d})" for pid, p in players.items()
    )

    if clear_screen:
        print("\x1b[2J\x1b[H", end="")

    print(f"Territory War - Turn {turn}")
    print(alive_text)
    print(positions)
    print("Legend: . empty | 1..4 player territory")
    print()
    for row in board:
        print("".join(symbol.get(cell, " ?") for cell in row))
    print(flush=True)


class PygameRenderer:
    def __init__(self, rows: int, cols: int):
        try:
            import pygame
        except ImportError as exc:
            raise ImportError("Install pygame with: pip install pygame") from exc

        self.pygame = pygame
        pygame.init()

        self.rows = rows
        self.cols = cols
        self.header_height = 74
        max_board_width_px = 720
        max_window_height_px = 760
        max_board_height_px = max_window_height_px - self.header_height
        size_by_width = max_board_width_px // cols
        size_by_height = max_board_height_px // rows
        self.cell_size = max(9, min(22, size_by_width, size_by_height))
        self.board_width = cols * self.cell_size
        self.board_height = rows * self.cell_size

        self.screen = pygame.display.set_mode(
            (self.board_width, self.board_height + self.header_height)
        )
        pygame.display.set_caption("Territory War Simulator")
        self.font = pygame.font.SysFont("consolas", 20)
        self.small_font = pygame.font.SysFont("consolas", 16)

    def close(self) -> None:
        self.pygame.quit()

    def render(
        self,
        board: Board,
        turn: int,
        players: Dict[str, PlayerState],
    ) -> bool:
        pygame = self.pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        self.screen.fill((12, 12, 14))
        pygame.draw.rect(
            self.screen,
            (28, 29, 35),
            pygame.Rect(0, 0, self.board_width, self.header_height),
        )

        title = self.font.render(
            f"Territory War  |  Turn {turn}", True, (230, 230, 236)
        )
        self.screen.blit(title, (12, 10))

        status = " | ".join(
            f"P{pid}:{'ALIVE' if p.alive else 'DEAD'}" for pid, p in players.items()
        )
        status_text = self.small_font.render(status, True, (195, 198, 210))
        self.screen.blit(status_text, (12, 36))

        scores = {"1": 0, "2": 0, "3": 0, "4": 0}
        for row in board:
            for cell in row:
                if cell in scores:
                    scores[cell] += 1
        score_text = self.small_font.render(
            (
                f"Score  P1:{scores['1']}  "
                f"P2:{scores['2']}  "
                f"P3:{scores['3']}  "
                f"P4:{scores['4']}"
            ),
            True,
            (215, 217, 226),
        )
        self.screen.blit(score_text, (12, 54))

        for r, row in enumerate(board):
            for c, cell in enumerate(row):
                color = PLAYER_COLORS.get(cell, (110, 110, 110))
                x = c * self.cell_size
                y = self.header_height + r * self.cell_size
                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(x, y, self.cell_size, self.cell_size),
                )

        pygame.display.flip()
        return True

    def wait_until_closed(
        self,
        board: Board,
        turn: int,
        players: Dict[str, PlayerState],
    ) -> None:
        while self.render(board, turn, players):
            self.pygame.time.wait(30)


if __name__ == "__main__":
    if DEFAULT_REALTIME:
        print(
            "Realtime ON | "
            f"render_mode={DEFAULT_RENDER_MODE} | "
            f"render_backend={DEFAULT_RENDER_BACKEND} | "
            f"frame_delay={DEFAULT_FRAME_DELAY_SECONDS:.3f}s"
        )
    else:
        print("Realtime OFF | running without visual delay")

    p1, p2, p3, p4 = import_player_functions(DEFAULT_PLAYERS)
    simulator = TerritoryWarSimulator(
        rows=DEFAULT_ROWS,
        cols=DEFAULT_COLS,
        player_functions=[p1, p2, p3, p4],
        move_format=MOVE_FORMAT,
    )
    result = simulator.run(
        max_turns=DEFAULT_MAX_TURNS,
        realtime=DEFAULT_REALTIME,
        frame_delay=DEFAULT_FRAME_DELAY_SECONDS,
        render_mode=DEFAULT_RENDER_MODE,
        render_backend=DEFAULT_RENDER_BACKEND,
    )

    print(f"Turns played: {result['turns']}")
    print(f"Alive: {result['alive']}")
    print(f"Territory: {result['territory']}")
    print_board(result["board"])
