// Play page: picks the bots, sends their code to the sandboxed runner, and plays back the
// frames it returns. This page never runs bot code itself.

const ROWS = 50;
const COLS = 50;
const MAX_TURNS = 1000;
const DEFAULT_SEATS = ["ignacio", "mia", "diego", "ming"];

// Same colors as PLAYER_COLORS in simulator.py
const COLORS = {
  ".": [22, 22, 26],
  1: [232, 78, 65],
  2: [248, 171, 72],
  3: [78, 173, 96],
  4: [61, 149, 214],
};
const MARKER_FACTOR = 0.72;

const REASONS = {
  error: "Su código lanzó un error",
  "invalid move": "Movimiento inválido",
  "out of bounds": "Salió del tablero",
  collision: "Pisó territorio ajeno",
};

const $ = (id) => document.getElementById(id);
const els = {
  runner: null,
  canvas: $("board"),
  boardMsg: $("board-msg"),
  setup: $("setup"),
  seats: $("seats"),
  play: $("play"),
  speed: $("speed"),
  status: $("status"),
  scores: $("scores"),
  playback: $("playback"),
  toggle: $("toggle"),
  scrub: $("scrub"),
  turn: $("turn"),
};

const state = {
  engine: null,
  workerSource: null,
  bots: [],
  codeCache: new Map(),
  runnerReady: false,
  pythonReady: false,
  matchId: 0,
  names: [],
  frames: [],
  deathTurns: [],
  simulating: false,
  playhead: 0,
  playing: false,
  lastTick: 0,
  carry: 0,
};

// ---------- Loading ----------

async function fetchText(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: ${res.status}`);
  return res.text();
}

async function botCode(name) {
  if (!state.codeCache.has(name)) {
    state.codeCache.set(name, fetchText(`codes/${encodeURIComponent(name)}.py`));
  }
  return state.codeCache.get(name);
}

// The runner is created here, after the message listener, so its "runner-ready" message
// cannot arrive before anyone is listening.
function createRunner() {
  const iframe = document.createElement("iframe");
  iframe.src = "runner.html";
  iframe.sandbox = "allow-scripts";
  iframe.title = "Motor del juego";
  iframe.hidden = true;
  document.body.append(iframe);
  els.runner = iframe;
}

async function init() {
  addEventListener("message", onRunnerMessage);
  createRunner();
  try {
    const [manifest, engine, workerSource] = await Promise.all([
      fetchText("bots.json").then(JSON.parse),
      fetchText("simulator.py"),
      fetchText("worker.js"),
    ]);
    state.bots = manifest.bots;
    state.engine = engine;
    state.workerSource = workerSource;
  } catch (err) {
    setStatus("No se pudieron cargar los archivos del juego. Recarga la página.", true);
    console.error(err);
    return;
  }
  renderSeats();
  bootRunner();
  drawBoard(emptyBoard(), null);
  els.boardMsg.textContent = "Cargando Python…";
}

function bootRunner() {
  if (state.runnerReady && state.workerSource) {
    els.runner.contentWindow.postMessage({ type: "boot", workerSource: state.workerSource }, "*");
  }
}

function renderSeats() {
  els.seats.replaceChildren();
  DEFAULT_SEATS.forEach((fallback, i) => {
    const id = `seat-${i + 1}`;
    const row = document.createElement("div");
    row.className = "seat";

    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.setProperty("--color", `var(--p${i + 1})`);
    swatch.setAttribute("aria-hidden", "true");

    const label = document.createElement("label");
    label.className = "sr-only";
    label.htmlFor = id;
    label.textContent = `Jugador ${i + 1}`;

    const select = document.createElement("select");
    select.id = id;
    for (const name of state.bots) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      select.append(option);
    }
    select.value = state.bots.includes(fallback) ? fallback : state.bots[i % state.bots.length];

    row.append(swatch, label, select);
    els.seats.append(row);
  });
}

// ---------- Runner messages ----------

function onRunnerMessage(event) {
  if (!els.runner || event.source !== els.runner.contentWindow) return;
  const msg = event.data;
  if (!msg || typeof msg !== "object") return;

  if (msg.type === "runner-ready") {
    state.runnerReady = true;
    bootRunner();
    return;
  }
  if (msg.type === "status") {
    setStatus(msg.text);
    return;
  }
  if (msg.type === "ready") {
    state.pythonReady = true;
    els.play.disabled = false;
    setStatus("Listo. Elige los bots y pulsa Jugar.");
    if (!state.frames.length) els.boardMsg.textContent = "Elige los bots y pulsa Jugar";
    return;
  }
  if (msg.matchId !== undefined && msg.matchId !== state.matchId) return;

  if (msg.type === "frame") {
    addFrame(msg);
  } else if (msg.type === "done") {
    state.simulating = false;
    els.play.textContent = "Jugar otra vez";
    setStatus(`Partida terminada en ${msg.turn} turnos.`);
  } else if (msg.type === "error") {
    state.simulating = false;
    els.play.textContent = "Jugar";
    setStatus(msg.message, true);
  }
}

// ---------- Match ----------

async function startMatch(event) {
  event.preventDefault();
  if (!state.pythonReady) return;

  const names = [...els.seats.querySelectorAll("select")].map((s) => s.value);
  let codes;
  try {
    codes = await Promise.all(names.map(botCode));
  } catch (err) {
    setStatus("No se pudo descargar el código de un bot.", true);
    return;
  }

  // A match still running in the worker cannot be interrupted, so start a fresh worker.
  if (state.simulating) {
    state.pythonReady = false;
    els.play.disabled = true;
    els.runner.contentWindow.postMessage({ type: "reset" }, "*");
    await waitForPython();
  }

  state.matchId += 1;
  state.names = names;
  state.frames = [];
  state.deathTurns = [null, null, null, null];
  state.simulating = true;
  state.playhead = 0;
  state.carry = 0;
  els.boardMsg.hidden = true;
  els.playback.hidden = false;
  els.play.textContent = "Reiniciar";
  setStatus("Simulando…");
  setPlaying(true);

  els.runner.contentWindow.postMessage(
    {
      type: "play",
      matchId: state.matchId,
      engine: state.engine,
      bots: names.map((name, i) => ({ name, code: codes[i] })),
      rows: ROWS,
      cols: COLS,
      maxTurns: MAX_TURNS,
    },
    "*",
  );
}

function waitForPython() {
  return new Promise((resolve) => {
    const check = () => (state.pythonReady ? resolve() : setTimeout(check, 50));
    check();
  });
}

function addFrame(frame) {
  frame.players.forEach((p, i) => {
    if (!p.alive && state.deathTurns[i] === null) state.deathTurns[i] = frame.turn;
  });
  state.frames.push(frame);
  els.scrub.max = String(state.frames.length - 1);
  if (state.frames.length === 1) showFrame(0);
  if (state.simulating) setStatus(`Simulando… turno ${frame.turn}`);
}

// ---------- Playback ----------

function setPlaying(playing) {
  state.playing = playing;
  els.toggle.textContent = playing ? "Pausa" : "Seguir";
  if (playing) {
    state.lastTick = performance.now();
    requestAnimationFrame(tick);
  }
}

function tick(now) {
  if (!state.playing) return;
  const last = state.frames.length - 1;
  const speed = Number(els.speed.value);

  if (speed === 0) {
    state.playhead = last;
  } else {
    state.carry += ((now - state.lastTick) / 1000) * speed;
    const steps = Math.floor(state.carry);
    state.carry -= steps;
    state.playhead = Math.min(last, state.playhead + steps);
  }
  state.lastTick = now;
  showFrame(state.playhead);

  if (state.playhead >= last && !state.simulating) {
    setPlaying(false);
    els.toggle.textContent = "Ver de nuevo";
    return;
  }
  requestAnimationFrame(tick);
}

function showFrame(index) {
  const frame = state.frames[index];
  if (!frame) return;
  state.playhead = index;
  els.scrub.value = String(index);
  els.turn.textContent = `Turno ${frame.turn}`;
  drawBoard(frame.board, frame.players);
  renderScores(frame);
}

function onToggle() {
  if (state.playing) {
    setPlaying(false);
    return;
  }
  if (state.playhead >= state.frames.length - 1) state.playhead = 0;
  state.carry = 0;
  setPlaying(true);
}

function onScrub() {
  setPlaying(false);
  showFrame(Number(els.scrub.value));
}

// ---------- Drawing ----------

function emptyBoard() {
  return ".".repeat(ROWS * COLS);
}

function drawBoard(board, players) {
  const canvas = els.canvas;
  const cssSize = canvas.clientWidth || 600;
  const cell = Math.max(1, Math.floor((cssSize * (devicePixelRatio || 1)) / COLS));
  const size = cell * COLS;
  if (canvas.width !== size) {
    canvas.width = size;
    canvas.height = cell * ROWS;
  }

  const ctx = canvas.getContext("2d");
  const image = ctx.createImageData(COLS, ROWS);
  for (let i = 0; i < ROWS * COLS; i++) {
    const [r, g, b] = COLORS[board[i]] || [110, 110, 110];
    image.data.set([r, g, b, 255], i * 4);
  }
  if (players) {
    players.forEach((p, i) => {
      const [r, g, b] = COLORS[i + 1].map((v) => Math.floor(v * MARKER_FACTOR));
      image.data.set([r, g, b, 255], (p.pos[0] * COLS + p.pos[1]) * 4);
    });
  }

  // Draw at one pixel per cell, then scale up without smoothing.
  if (!drawBoard.small) {
    drawBoard.small = document.createElement("canvas");
    drawBoard.small.width = COLS;
    drawBoard.small.height = ROWS;
  }
  const small = drawBoard.small;
  small.getContext("2d").putImageData(image, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(small, 0, 0, size, cell * ROWS);
}

function renderScores(frame) {
  const counts = [0, 0, 0, 0];
  for (const c of frame.board) if (c !== ".") counts[Number(c) - 1] += 1;
  const best = Math.max(...counts);

  const items = state.names.map((name, i) => {
    const p = frame.players[i];
    const li = document.createElement("li");
    li.className = "score";
    if (!p.alive) li.classList.add("is-dead");
    if (counts[i] === best && best > 1) li.classList.add("is-leader");

    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.setProperty("--color", `var(--p${i + 1})`);
    swatch.setAttribute("aria-hidden", "true");

    const nameEl = document.createElement("span");
    nameEl.className = "score-name";
    nameEl.textContent = name;

    const cells = document.createElement("span");
    cells.className = "score-cells";
    cells.textContent = `${counts[i]} casillas`;

    const stateEl = document.createElement("span");
    stateEl.className = "score-state";
    stateEl.textContent = p.alive ? "Sigue en juego" : deathText(p.reason, state.deathTurns[i]);

    li.append(swatch, nameEl, cells, stateEl);
    return li;
  });
  els.scores.replaceChildren(...items);
}

function deathText(reason, turn) {
  const text = reason || "";
  const key = Object.keys(REASONS).find((k) => text.startsWith(k + ":"));
  const label = key ? REASONS[key] : "Eliminado";
  const detail = key ? text.slice(key.length + 1).trim() : text;
  const when = turn ? ` en el turno ${turn}` : "";
  return `Eliminado${when}. ${label}${detail ? ": " + detail : ""}`;
}

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle("is-error", isError);
}

// ---------- Wiring ----------

els.setup.addEventListener("submit", startMatch);
els.toggle.addEventListener("click", onToggle);
els.scrub.addEventListener("input", onScrub);
addEventListener("resize", () => {
  const frame = state.frames[state.playhead];
  drawBoard(frame ? frame.board : emptyBoard(), frame ? frame.players : null);
});

init();
