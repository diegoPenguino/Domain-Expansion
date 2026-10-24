// Runs the game engine (simulator.py) with Pyodide. It never runs bot code: for each
// move it sends an "ask" to the runner, which forwards it to that bot's own worker and
// answers with the move, a death reason, or a timeout.
//
// Receives {type: "play", matchId, engine, bots: [{name, code}], rows, cols, maxTurns}
// and sends back one "frame" per turn, then "done", or "error".

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/";
const PLAYER_IDS = ["1", "2", "3", "4"];

importScripts(PYODIDE_URL + "pyodide.js");

const GLUE = `
import json
import simulator

def _remote(*args):
    raise RuntimeError("bots run in their own workers")

sim = None

def new_match(names_json, rows, cols):
    global sim
    sim = simulator.TerritoryWarSimulator(rows, cols, [_remote] * 4, json.loads(names_json))

def start_turn():
    return sim.start_turn()

def is_alive(pid):
    return sim.players[pid].alive

def bot_input(pid):
    board, pos, positions, me = sim.bot_input(pid)
    return json.dumps({
        "board": "".join("".join(row) for row in board),
        "rows": sim.rows,
        "cols": sim.cols,
        "pos": pos,
        "positions": positions,
        "me": me,
    })

def apply(pid, r, c):
    sim.apply_move(pid, (r, c))

def eliminate(pid, reason):
    sim.eliminate(pid, reason)

def frame():
    players = [sim.players[pid] for pid in simulator.PLAYER_IDS]
    return json.dumps({
        "type": "frame",
        "turn": sim.turn,
        "board": "".join("".join(row) for row in sim.board),
        "players": [
            {"pos": list(p.pos), "alive": p.alive, "reason": p.death_reason}
            for p in players
        ],
    })
`;

let pyodide = null;
let engineSource = null;
const py = {};

const ready = (async () => {
  postMessage({ type: "status", text: "Cargando Python…" });
  pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  postMessage({ type: "ready" });
})().catch((err) => {
  postMessage({ type: "error", message: "No se pudo cargar Python: " + err.message });
  throw err;
});

function loadEngine(source) {
  if (source === engineSource) return;
  pyodide.FS.writeFile("/home/pyodide/simulator.py", source);
  pyodide.runPython(GLUE);
  for (const name of ["new_match", "start_turn", "is_alive", "bot_input", "apply", "eliminate", "frame"]) {
    py[name] = pyodide.globals.get(name);
  }
  engineSource = source;
}

// ---------- Asking the bots, through the runner ----------

let activeMatch = null;
let nextAskId = 0;
const pending = new Map();

function ask(matchId, seat, payload) {
  const id = ++nextAskId;
  return new Promise((resolve) => {
    pending.set(id, resolve);
    postMessage({ type: "ask", matchId, seat, id, payload });
  });
}

function applyAnswer(pid, answer) {
  if (answer.move) {
    py.apply(pid, answer.move[0], answer.move[1]);
  } else {
    py.eliminate(pid, answer.reason || "error: the bot did not answer");
  }
}

// ---------- Match ----------

async function play(msg) {
  activeMatch = msg.matchId;
  const stale = () => activeMatch !== msg.matchId;
  const send = (data) => postMessage({ ...data, matchId: msg.matchId });

  loadEngine(msg.engine);
  py.new_match(JSON.stringify(msg.bots.map((bot) => bot.name)), msg.rows, msg.cols);

  const loads = await Promise.all(
    msg.bots.map((bot, seat) =>
      ask(msg.matchId, seat, { type: "load", name: bot.name, code: bot.code, engine: msg.engine }),
    ),
  );
  if (stale()) return;
  loads.forEach((answer, seat) => {
    if (!answer.ok) py.eliminate(PLAYER_IDS[seat], answer.reason || "error: the bot did not load");
  });
  send(JSON.parse(py.frame()));

  let turn = 0;
  while (turn < msg.maxTurns && py.start_turn()) {
    turn += 1;
    for (let seat = 0; seat < 4; seat++) {
      const pid = PLAYER_IDS[seat];
      if (!py.is_alive(pid)) continue;
      const answer = await ask(msg.matchId, seat, { type: "move", input: py.bot_input(pid) });
      if (stale()) return;
      applyAnswer(pid, answer);
    }
    send(JSON.parse(py.frame()));
  }
  send({ type: "done", turn });
}

onmessage = async (event) => {
  const msg = event.data;
  if (msg.type === "answer") {
    const resolve = pending.get(msg.id);
    if (resolve) {
      pending.delete(msg.id);
      resolve(msg.answer);
    }
    return;
  }
  if (msg.type !== "play") return;
  await ready;
  try {
    await play(msg);
  } catch (err) {
    postMessage({ type: "error", message: err.message, matchId: msg.matchId });
  }
};
