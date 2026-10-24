// Runs a match with Pyodide (Python compiled to WebAssembly).
//
// Receives {type: "play", matchId, engine, bots: [{name, code}], rows, cols, maxTurns}
// and sends back one "frame" per turn, then "done", or "error".

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/";

importScripts(PYODIDE_URL + "pyodide.js");

const GLUE = `
import json
import simulator

def play(config_json, post):
    cfg = json.loads(config_json)
    names = [bot["name"] for bot in cfg["bots"]]
    try:
        bots = [simulator.load_bot_from_source(bot["code"], bot["name"]) for bot in cfg["bots"]]
    except simulator.BotLoadError as exc:
        post(json.dumps({"type": "error", "message": str(exc)}))
        return

    sim = simulator.TerritoryWarSimulator(cfg["rows"], cfg["cols"], bots, names)

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

    post(frame())
    while sim.turn < cfg["maxTurns"] and sim.step():
        post(frame())
    post(json.dumps({"type": "done", "turn": sim.turn}))
`;

let pyodide = null;
let engineSource = null;

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
  engineSource = source;
}

onmessage = async (event) => {
  const msg = event.data;
  if (msg.type !== "play") return;
  await ready;

  const post = (json) => postMessage({ ...JSON.parse(json), matchId: msg.matchId });
  try {
    loadEngine(msg.engine);
    const config = JSON.stringify({
      bots: msg.bots,
      rows: msg.rows,
      cols: msg.cols,
      maxTurns: msg.maxTurns,
    });
    const play = pyodide.globals.get("play");
    try {
      play(config, post);
    } finally {
      play.destroy();
    }
  } catch (err) {
    postMessage({ type: "error", message: err.message, matchId: msg.matchId });
  }
};
