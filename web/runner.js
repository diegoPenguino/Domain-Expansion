// Referee between the parent page, the engine worker and one worker per bot.
//
// The engine asks for each move; the runner forwards the question to that seat's bot
// worker and starts a timer. A bot that does not answer in time has its worker
// terminated, and the engine is told it timed out. The other bots keep running.
//
// Workers are built from source text sent by the parent: a sandboxed iframe has an
// opaque origin, so it cannot start a worker from a URL on the site, only from a blob.

const SEATS = 4;

let sources = null;
let engine = null;
let seats = [];
let activeMatch = null;
let limits = { move: 2000, load: 5000 };

function makeWorker(source) {
  const url = URL.createObjectURL(new Blob([source], { type: "text/javascript" }));
  const worker = new Worker(url);
  URL.revokeObjectURL(url);
  worker.onerror = (event) => {
    event.preventDefault();
    parent.postMessage({ type: "error", message: event.message || "A worker crashed" }, "*");
  };
  return worker;
}

function toParent(msg) {
  parent.postMessage(msg, "*");
}

function answerEngine(id, answer) {
  engine.postMessage({ type: "answer", id, answer });
}

// ---------- Engine ----------

function startEngine() {
  engine = makeWorker(sources.engine);
  engine.onmessage = (event) => {
    const msg = event.data;
    if (msg.type === "ask") {
      forwardAsk(msg);
      return;
    }
    toParent(msg);
    if ((msg.type === "done" || msg.type === "error") && msg.matchId === activeMatch) {
      refreshUsedSeats();
    }
  };
}

// ---------- Bot seats ----------

// Replaces the seat's worker with a fresh one. Terminating a worker stops whatever
// the bot was running, even an infinite loop.
function spawnSeat(i) {
  if (seats[i]) seats[i].worker.terminate();
  const seat = { worker: makeWorker(sources.bot), used: false, pending: null };
  seat.ready = new Promise((resolve) => {
    seat.worker.onmessage = (event) => {
      const msg = event.data;
      if (msg.type === "ready") resolve();
      else if (msg.type === "reply") onReply(seat, msg);
      else if (msg.type === "fatal") toParent({ type: "error", message: msg.message });
    };
  });
  seats[i] = seat;
  return seat;
}

function onReply(seat, msg) {
  if (!seat.pending || seat.pending.id !== msg.id) return;
  clearTimeout(seat.pending.timer);
  seat.pending = null;
  answerEngine(msg.id, msg.answer);
}

async function forwardAsk(msg) {
  const i = msg.seat;
  const isLoad = msg.payload.type === "load";
  let seat = seats[i];
  if (isLoad) {
    if (seat.used) seat = spawnSeat(i);
    seat.used = true;
  }

  // The clock starts once Python is loaded in the bot's worker.
  await seat.ready;
  if (msg.matchId !== activeMatch || seats[i] !== seat) {
    answerEngine(msg.id, { cancelled: true });
    return;
  }

  const limit = isLoad ? limits.load : limits.move;
  const timer = setTimeout(() => {
    if (!seat.pending || seat.pending.id !== msg.id) return;
    seat.pending = null;
    spawnSeat(i);
    const what = isLoad ? "took more than" : "no move within";
    answerEngine(msg.id, { reason: `timeout: ${what} ${limit / 1000} s` });
  }, limit);
  seat.pending = { id: msg.id, timer };
  seat.worker.postMessage({ ...msg.payload, id: msg.id });
}

// A new match starts while the previous one may still be waiting on a bot: stop
// those bots and tell the engine their questions were cancelled.
function cancelPending() {
  seats.forEach((seat, i) => {
    if (!seat.pending) return;
    clearTimeout(seat.pending.timer);
    const id = seat.pending.id;
    seat.pending = null;
    spawnSeat(i);
    answerEngine(id, { cancelled: true });
  });
}

// After a match, swap the used workers for fresh ones in the background, so the
// next match starts clean without waiting for Python to load.
function refreshUsedSeats() {
  seats.forEach((seat, i) => {
    if (seat.used && !seat.pending) spawnSeat(i);
  });
}

// ---------- Messages from the parent page ----------

addEventListener("message", (event) => {
  if (event.source !== parent) return;
  const msg = event.data;
  if (msg.type === "boot") {
    sources = { engine: msg.engineWorker, bot: msg.botWorker };
    startEngine();
    for (let i = 0; i < SEATS; i++) spawnSeat(i);
  } else if (msg.type === "play" && engine) {
    cancelPending();
    activeMatch = msg.matchId;
    limits = msg.limits || limits;
    engine.postMessage(msg);
  }
});

toParent({ type: "runner-ready" });
