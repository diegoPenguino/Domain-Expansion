// Relays messages between the parent page and the worker that runs the bots.
//
// The worker is built from source text sent by the parent: a sandboxed iframe has an
// opaque origin, so it cannot start a worker from a URL on the site, only from a blob.

let worker = null;
let workerSource = null;

function startWorker() {
  if (worker) worker.terminate();
  const url = URL.createObjectURL(new Blob([workerSource], { type: "text/javascript" }));
  worker = new Worker(url);
  URL.revokeObjectURL(url);
  worker.onmessage = (event) => parent.postMessage(event.data, "*");
  worker.onerror = (event) => {
    event.preventDefault();
    parent.postMessage({ type: "error", message: event.message || "The worker crashed" }, "*");
  };
}

addEventListener("message", (event) => {
  if (event.source !== parent) return;
  const msg = event.data;
  if (msg.type === "boot") {
    workerSource = msg.workerSource;
    startWorker();
  } else if (msg.type === "reset") {
    startWorker();
  } else if (worker) {
    worker.postMessage(msg);
  }
});

parent.postMessage({ type: "runner-ready" }, "*");
