// Runs one bot with Pyodide. Each seat gets its own worker, so the runner can stop a
// bot that takes too long without touching the others, and every match gets fresh
// workers, so nothing a bot changes in Python carries over to the next one.
//
// Receives {type: "load", id, name, code, engine} and {type: "move", id, input}, and
// answers {type: "reply", id, answer} where answer is {ok}, {move: [r, c]} or {reason}.

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/";

importScripts(PYODIDE_URL + "pyodide.js");

const GLUE = `
import json
import simulator

bot = None

def load(code, name):
    global bot
    try:
        bot = simulator.load_bot_from_source(code, name)
    except simulator.BotLoadError as exc:
        return json.dumps({"reason": f"error: {exc}"})
    return json.dumps({"ok": True})

def move(input_json):
    data = json.loads(input_json)
    cols = data["cols"]
    flat = data["board"]
    board = [list(flat[r * cols:(r + 1) * cols]) for r in range(data["rows"])]
    positions = [tuple(p) for p in data["positions"]]
    try:
        result = bot(board, tuple(data["pos"]), positions, data["me"])
    except Exception as exc:
        return json.dumps({"reason": simulator.error_reason(exc)})
    reason = simulator.invalid_move_reason(result)
    if reason is not None:
        return json.dumps({"reason": reason})
    return json.dumps({"move": [int(result[0]), int(result[1])]})
`;

let pyodide = null;
let engineSource = null;

const ready = (async () => {
  pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  postMessage({ type: "ready" });
})().catch((err) => {
  postMessage({ type: "fatal", message: "No se pudo cargar Python: " + err.message });
  throw err;
});

function call(name, ...args) {
  const fn = pyodide.globals.get(name);
  try {
    return JSON.parse(fn(...args));
  } finally {
    fn.destroy();
  }
}

onmessage = async (event) => {
  const msg = event.data;
  await ready;
  let answer;
  try {
    if (msg.type === "load") {
      if (msg.engine !== engineSource) {
        pyodide.FS.writeFile("/home/pyodide/simulator.py", msg.engine);
        pyodide.runPython(GLUE);
        engineSource = msg.engine;
      }
      answer = call("load", msg.code, msg.name);
    } else if (msg.type === "move") {
      answer = call("move", msg.input);
    } else {
      return;
    }
  } catch (err) {
    answer = { reason: "error: " + err.message };
  }
  postMessage({ type: "reply", id: msg.id, answer });
};
