// Play page: picks the bots, sends their code to the sandboxed runner, and plays back the
// frames it returns. This page never runs bot code itself.
//
// Bots come from three places: the repo's codes/ folder ("repo:<name>"), the challenge
// bots in challenge/ ("challenge:<name>", whose code is not shown), and the ones people
// upload ("user:<uid>/<slot>"), which account.js loads from Firestore and hands over
// through the `game` object at the end of this file.

// scripts/build_site.py replaces this with a hash of the site's files. Every URL below
// carries it, so a visit never mixes files from two deploys (Cloudflare tells browsers to
// keep .js files for hours).
const VERSION = "__VERSION__";
const versioned = (path) => `${path}?v=${VERSION}`;
// How long Python may take to load before the page says something is wrong.
const LOAD_WARNING_MS = 60000;

const ROWS = 50;
const COLS = 50;
const MAX_TURNS = 1000;
// Time a bot gets to answer one move, and to load its code. A bot over the limit is
// eliminated; the runner stops its worker.
const LIMITS_MS = { move: 2000, load: 5000 };
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
// Overlays on the board: how many turns a capture stays lit, and how many past steps
// of each bot are marked.
const FLASH_TURNS = 8;
const TRAIL_STEPS = 12;
const EMPTY_CSS = "rgb(22, 22, 26)";

const CHALLENGE_GROUP = "Reto";
const REPO_GROUP = "Participantes originales";
// Display names for challenge bots; the first one starts in seat 1.
const CHALLENGE_NAMES = { claude_opus: "Claude Opus 5.5" };
const COMMUNITY_GROUP = "Comunidad";

// Before an uploaded bot is saved, it plays a few turns against these.
const TEST_TURNS = 10;
const TEST_OPPONENTS = ["diego", "mia", "ignacio"];

const REASONS = {
  error: "Su código lanzó un error",
  "invalid move": "Movimiento inválido",
  "out of bounds": "Salió del tablero",
  collision: "Pisó territorio ajeno",
  timeout: "Se pasó del tiempo",
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
  chart: $("chart"),
  codeDialog: $("code-dialog"),
  codeTitle: $("code-title"),
  codeBody: $("code-body"),
  codeBox: $("code-box"),
  codeSecret: $("code-secret"),
};

const state = {
  engine: null,
  workerSources: null,
  bots: [],
  challenge: [],
  userBots: [],
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
  validation: null,
  validationCount: 0,
};

// ---------- Loading ----------

async function fetchText(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: ${res.status}`);
  return res.text();
}

function challengeCode(name) {
  const key = `challenge:${name}`;
  if (!state.codeCache.has(key)) {
    state.codeCache.set(key, fetchText(versioned(`challenge/${encodeURIComponent(name)}.py`)));
  }
  return state.codeCache.get(key);
}

async function botCode(name) {
  if (!state.codeCache.has(name)) {
    state.codeCache.set(name, fetchText(versioned(`codes/${encodeURIComponent(name)}.py`)));
  }
  return state.codeCache.get(name);
}

// The runner is created here, after the message listener, so its "runner-ready" message
// cannot arrive before anyone is listening.
function createRunner() {
  const iframe = document.createElement("iframe");
  iframe.src = versioned("runner.html");
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
    const [manifest, engine, engineWorker, botWorker] = await Promise.all([
      fetchText(versioned("bots.json")).then(JSON.parse),
      fetchText(versioned("simulator.py")),
      fetchText(versioned("engine-worker.js")),
      fetchText(versioned("bot-worker.js")),
    ]);
    state.bots = manifest.bots;
    state.challenge = manifest.challenge || [];
    state.engine = engine;
    state.workerSources = { engineWorker, botWorker };
  } catch (err) {
    setStatus("No se pudieron cargar los archivos del juego. Recarga la página.", true);
    console.error(err);
    return;
  }
  renderSeats();
  bootRunner();
  drawBoard(emptyBoard(), null);
  els.boardMsg.textContent = "Cargando Python…";
  setTimeout(() => {
    if (state.pythonReady || els.status.classList.contains("is-error")) return;
    setStatus("Python no termina de cargar. Recarga la página; si sigue igual, prueba con otro navegador.", true);
    els.boardMsg.textContent = "Python no termina de cargar";
  }, LOAD_WARNING_MS);
}

function bootRunner() {
  if (state.runnerReady && state.workerSources) {
    els.runner.contentWindow.postMessage({ type: "boot", version: VERSION, ...state.workerSources }, "*");
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

    const view = document.createElement("button");
    view.type = "button";
    view.className = "btn btn--ghost seat-code";
    view.textContent = "Código";
    view.setAttribute("aria-label", `Ver el código del jugador ${i + 1}`);
    view.addEventListener("click", () => showCode(select.value));

    row.append(swatch, label, select, view);
    els.seats.append(row);
    const name = state.bots.includes(fallback) ? fallback : state.bots[i % state.bots.length];
    fillSeat(select, i === 0 && state.challenge.length ? `challenge:${state.challenge[0]}` : `repo:${name}`);
  });
}

// Rebuilds a seat's options and keeps `wanted` selected if it still exists.
function fillSeat(select, wanted) {
  const groups = [];
  if (state.challenge.length) {
    groups.push([CHALLENGE_GROUP, state.challenge.map((name) => [`challenge:${name}`, challengeLabel(name)])]);
  }
  groups.push([REPO_GROUP, state.bots.map((name) => [`repo:${name}`, name])]);
  if (state.userBots.length) {
    groups.push([COMMUNITY_GROUP, state.userBots.map((bot) => [`user:${bot.id}`, botLabel(bot)])]);
  }
  select.replaceChildren(
    ...groups.map(([title, items]) => {
      const group = document.createElement("optgroup");
      group.label = title;
      for (const [value, text] of items) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = text;
        group.append(option);
      }
      return group;
    }),
  );
  select.value = wanted;
  if (select.value !== wanted) select.selectedIndex = 0;
}

function challengeLabel(name) {
  return CHALLENGE_NAMES[name] || name;
}

function botLabel(bot) {
  return `${bot.name} — ${bot.ownerName}`;
}

// What a seat's value refers to: {name, label, code: Promise<string>, secret?}, or null if
// an uploaded bot was deleted.
function seatBot(value) {
  if (value.startsWith("challenge:")) {
    const name = value.slice("challenge:".length);
    return { name, label: challengeLabel(name), code: challengeCode(name), secret: true };
  }
  if (value.startsWith("user:")) {
    const bot = state.userBots.find((b) => `user:${b.id}` === value);
    return bot ? { name: bot.name, label: botLabel(bot), code: Promise.resolve(bot.code) } : null;
  }
  const name = value.slice("repo:".length);
  return { name, label: name, code: botCode(name) };
}

async function showCode(value) {
  const bot = seatBot(value);
  if (!bot) return;
  els.codeTitle.textContent = bot.label;
  els.codeSecret.hidden = !bot.secret;
  els.codeBox.hidden = !!bot.secret;
  if (bot.secret) {
    els.codeSecret.textContent =
      "Es el único bot con el código secreto. Lo escribió Claude Opus 5.5 y gana más del 90 % " +
      "de sus partidas contra los participantes originales. ¿Puedes escribir uno que le gane sin ver cómo juega?";
    els.codeDialog.showModal();
    return;
  }
  els.codeBody.textContent = "Cargando…";
  els.codeDialog.showModal();
  try {
    els.codeBody.textContent = await bot.code;
  } catch (err) {
    els.codeBody.textContent = "No se pudo cargar el código.";
  }
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
  if (state.validation && msg.matchId === state.validation.id) {
    onTestMessage(msg);
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
    if (!state.frames.length) els.boardMsg.textContent = "No se pudo iniciar el juego";
  }
}

// ---------- Match ----------

async function startMatch(event) {
  event.preventDefault();
  if (!state.pythonReady) return;

  const bots = [...els.seats.querySelectorAll("select")].map((s) => seatBot(s.value));
  if (bots.includes(null)) {
    setStatus("Uno de los bots ya no existe. Elige otro.", true);
    return;
  }
  let codes;
  try {
    codes = await Promise.all(bots.map((bot) => bot.code));
  } catch (err) {
    setStatus("No se pudo descargar el código de un bot.", true);
    return;
  }

  // If a match or a test is still running, the runner stops it before starting this one.
  finishTest({ ok: false, message: "La prueba se interrumpió porque empezó una partida." });
  state.matchId += 1;
  state.names = bots.map((bot) => bot.label);
  state.frames = [];
  state.deathTurns = [null, null, null, null];
  state.simulating = true;
  state.playhead = 0;
  state.carry = 0;
  els.boardMsg.hidden = true;
  els.playback.hidden = false;
  els.chart.hidden = false;
  els.play.textContent = "Reiniciar";
  setStatus("Simulando…");
  setPlaying(true);

  els.runner.contentWindow.postMessage(
    {
      type: "play",
      matchId: state.matchId,
      engine: state.engine,
      bots: bots.map((bot, i) => ({ name: bot.name, code: codes[i] })),
      rows: ROWS,
      cols: COLS,
      maxTurns: MAX_TURNS,
      limits: LIMITS_MS,
    },
    "*",
  );
}

// ---------- Testing an uploaded bot ----------

// Plays TEST_TURNS turns with the bot in seat 1. Resolves to {ok, message?, warning?}:
// errors, timeouts and invalid answers fail; losing (a collision, leaving the board) is
// a strategy problem, so the bot can still be saved.
async function validateBot(name, code) {
  if (!state.pythonReady) {
    return { ok: false, message: "Python todavía está cargando. Prueba en unos segundos." };
  }
  finishTest({ ok: false, message: "La prueba se interrumpió." });

  const opponents = TEST_OPPONENTS.filter((n) => state.bots.includes(n));
  while (opponents.length < 3) opponents.push(state.bots[opponents.length]);
  let codes;
  try {
    codes = await Promise.all(opponents.map(botCode));
  } catch (err) {
    return { ok: false, message: "No se pudieron descargar los bots de prueba." };
  }

  // The runner plays one match at a time, so a match being watched stops here.
  if (state.simulating) {
    state.simulating = false;
    els.play.textContent = "Jugar";
    setStatus("La partida se detuvo para probar tu bot.");
  }

  state.validationCount += 1;
  const id = `test-${state.validationCount}`;
  return new Promise((resolve) => {
    state.validation = { id, resolve, last: null };
    els.runner.contentWindow.postMessage(
      {
        type: "play",
        matchId: id,
        engine: state.engine,
        bots: [{ name, code }, ...opponents.map((n, i) => ({ name: n, code: codes[i] }))],
        rows: ROWS,
        cols: COLS,
        maxTurns: TEST_TURNS,
        limits: LIMITS_MS,
      },
      "*",
    );
  });
}

function onTestMessage(msg) {
  if (msg.type === "frame") {
    state.validation.last = msg;
  } else if (msg.type === "done") {
    const me = state.validation.last && state.validation.last.players[0];
    if (!me || me.alive) {
      finishTest({ ok: true });
    } else if (/^(error|timeout|invalid move):/.test(me.reason || "")) {
      finishTest({ ok: false, message: describeReason(me.reason) });
    } else {
      finishTest({ ok: true, warning: describeReason(me.reason) });
    }
  } else if (msg.type === "error") {
    finishTest({ ok: false, message: msg.message });
  }
}

function finishTest(result) {
  const test = state.validation;
  if (!test) return;
  state.validation = null;
  test.resolve(result);
}

function addFrame(frame) {
  frame.players.forEach((p, i) => {
    if (!p.alive && state.deathTurns[i] === null) state.deathTurns[i] = frame.turn;
  });
  frame.counts = countCells(frame.board);
  frame.captured = capturedCells(state.frames[state.frames.length - 1], frame);
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
  drawBoard(frame.board, frame.players, index);
  drawChart(index);
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

function countCells(board) {
  const counts = [0, 0, 0, 0];
  for (const c of board) if (c !== ".") counts[Number(c) - 1] += 1;
  return counts;
}

// Cells that went from empty to a player's color without the player stepping on them:
// the area a loop just closed.
function capturedCells(prev, frame) {
  if (!prev) return [];
  const heads = new Set(frame.players.map((p) => p.pos[0] * COLS + p.pos[1]));
  const cells = [];
  for (let i = 0; i < ROWS * COLS; i++) {
    if (prev.board[i] === "." && frame.board[i] !== "." && !heads.has(i)) cells.push(i);
  }
  return cells;
}

// Fits a canvas's backing store to its CSS size times the pixel ratio.
function fitCanvas(canvas, width, height) {
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  return canvas.getContext("2d");
}

// index: the frame being shown, used to draw captures and trails from earlier frames.
function drawBoard(board, players, index = null) {
  const canvas = els.canvas;
  const cssSize = canvas.clientWidth || 600;
  const cell = Math.max(1, Math.floor((cssSize * (devicePixelRatio || 1)) / COLS));
  const size = cell * COLS;
  const ctx = fitCanvas(canvas, size, cell * ROWS);

  const image = ctx.createImageData(COLS, ROWS);
  for (let i = 0; i < ROWS * COLS; i++) {
    const [r, g, b] = COLORS[board[i]] || [110, 110, 110];
    image.data.set([r, g, b, 255], i * 4);
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

  if (index !== null) {
    drawCaptures(ctx, cell, index);
    drawTrails(ctx, cell, index);
  }
  if (players) drawHeads(ctx, cell, players);
}

// Recent captures glow white and fade over FLASH_TURNS turns.
function drawCaptures(ctx, cell, index) {
  for (let age = FLASH_TURNS - 1; age >= 0; age--) {
    const frame = state.frames[index - age];
    if (!frame || !frame.captured.length) continue;
    ctx.fillStyle = `rgba(255, 255, 255, ${0.55 * (1 - age / FLASH_TURNS)})`;
    for (const i of frame.captured) {
      ctx.fillRect((i % COLS) * cell, Math.floor(i / COLS) * cell, cell, cell);
    }
  }
}

// A dot on each of the last TRAIL_STEPS cells a bot stood on, stronger when recent.
function drawTrails(ctx, cell, index) {
  const dot = Math.max(1, Math.round(cell * 0.34));
  const inset = (cell - dot) / 2;
  for (let back = TRAIL_STEPS; back >= 1; back--) {
    const frame = state.frames[index - back];
    if (!frame) continue;
    ctx.fillStyle = `rgba(255, 255, 255, ${0.15 + 0.45 * (1 - back / TRAIL_STEPS)})`;
    for (const p of frame.players) {
      ctx.fillRect(p.pos[1] * cell + inset, p.pos[0] * cell + inset, dot, dot);
    }
  }
}

// Each bot's current cell in a darker shade; living bots also get a white outline.
function drawHeads(ctx, cell, players) {
  const line = Math.max(1, Math.round(cell * 0.14));
  players.forEach((p, i) => {
    const x = p.pos[1] * cell;
    const y = p.pos[0] * cell;
    const [r, g, b] = COLORS[i + 1].map((v) => Math.floor(v * MARKER_FACTOR));
    ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
    ctx.fillRect(x, y, cell, cell);
    if (!p.alive) return;
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = line;
    ctx.strokeRect(x + line / 2, y + line / 2, cell - line, cell - line);
  });
}

// Cells per bot over the turns played so far, up to the frame being shown.
function drawChart(index) {
  const canvas = els.chart;
  const dpr = devicePixelRatio || 1;
  const w = Math.round((canvas.clientWidth || 600) * dpr);
  const h = Math.round((canvas.clientHeight || 120) * dpr);
  const ctx = fitCanvas(canvas, w, h);
  ctx.fillStyle = EMPTY_CSS;
  ctx.fillRect(0, 0, w, h);

  const frames = state.frames;
  if (!frames.length) return;
  const pad = 10 * dpr;
  const lastX = Math.max(1, frames.length - 1);
  let top = 1;
  for (const f of frames) top = Math.max(top, ...f.counts);
  const x = (k) => pad + (k / lastX) * (w - 2 * pad);
  const y = (n) => h - pad - (n / top) * (h - 2 * pad);

  ctx.lineWidth = 2 * dpr;
  ctx.lineJoin = "round";
  for (let p = 0; p < 4; p++) {
    const [r, g, b] = COLORS[p + 1];
    ctx.strokeStyle = `rgb(${r}, ${g}, ${b})`;
    ctx.beginPath();
    for (let k = 0; k <= index; k++) {
      const px = x(k);
      const py = y(frames[k].counts[p]);
      if (k === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
  }
}

function renderScores(frame) {
  const counts = frame.counts;
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
  const when = turn === 0 ? " antes de empezar" : turn ? ` en el turno ${turn}` : "";
  return `Eliminado${when}. ${describeReason(reason)}`;
}

// "collision: (3, 4) belongs to player 2" -> "Pisó territorio ajeno: (3, 4) belongs to player 2"
function describeReason(reason) {
  const text = reason || "";
  const key = Object.keys(REASONS).find((k) => text.startsWith(k + ":"));
  const label = key ? REASONS[key] : "Eliminado";
  // A timeout's detail is in English and adds nothing to the label.
  const detail = key === "timeout" ? "" : key ? text.slice(key.length + 1).trim() : text;
  return `${label}${detail ? ": " + detail : ""}`;
}

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle("is-error", isError);
}

// ---------- Wiring ----------

els.setup.addEventListener("submit", startMatch);
for (const button of document.querySelectorAll("dialog [data-close]")) {
  button.addEventListener("click", () => button.closest("dialog").close());
}
els.toggle.addEventListener("click", onToggle);
els.scrub.addEventListener("input", onScrub);
addEventListener("resize", () => {
  if (state.frames[state.playhead]) {
    showFrame(state.playhead);
  } else {
    drawBoard(emptyBoard(), null);
  }
});

init();

// ---------- For account.js ----------

// account.js is a module loaded after this script; it reaches this object by name.
const game = {
  // bots: [{id: "<uid>/<slot>", name, ownerName, code, updatedAt (ms)}]
  setUserBots(bots) {
    state.userBots = [...bots].sort((a, b) => b.updatedAt - a.updatedAt);
    for (const select of els.seats.querySelectorAll("select")) fillSeat(select, select.value);
  },
  validateBot,
};
