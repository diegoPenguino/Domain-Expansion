// Uploaded bots: Google sign-in (Firebase Authentication) and Cloud Firestore, in the same
// Firebase project as the comments on penguino.space.
//
//   users/{uid}/bots/{slot}  {uid, ownerName, name, code, createdAt, updatedAt}, slot "1".."5"
//   botLimits/{uid}          {lastSaveAt}, one save every 10 seconds
//
// The rules live in the website repo (firebase/firestore.rules). This module only reads and
// writes data; bots are run by app.js in the sandboxed runner. If Firebase fails to load,
// the page keeps working with the repo's bots.
//
// On localhost, add ?emulator to the URL to use the Auth and Firestore emulators instead.

import { initializeApp } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";
import {
  getAuth, onAuthStateChanged, signInWithPopup, signInWithRedirect, getRedirectResult, signOut,
  GoogleAuthProvider, connectAuthEmulator,
} from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";
import {
  getFirestore, collectionGroup, doc, onSnapshot, writeBatch, deleteDoc, serverTimestamp,
  connectFirestoreEmulator,
} from "https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore.js";

// Public by design: Firestore rules protect the data, not this config.
const CONFIG = {
  apiKey: "AIzaSyCx6kz6L01-roRK4Co_qIbDoqa8OCbMwIg",
  authDomain: "penguin-blog-6526c.firebaseapp.com",
  projectId: "penguin-blog-6526c",
  appId: "1:728883874771:web:b168c3193682639fc4fd26",
};

const MAX_BOTS = 5;
const MAX_NAME = 40;
const MAX_CODE = 20000;

const TEMPLATE = `from typing import List, Tuple


def next_step(
    current_board: List[List[str]],
    current_pos: Tuple[int, int],
    all_player_positions: List[Tuple[int, int]],
    your_character: str,
) -> Tuple[int, int]:
    # current_board[fila][columna] es "." (vacía) o "1".."4" (territorio de cada jugador).
    # Devuelve la casilla vecina (arriba, abajo, izquierda o derecha) a la que te mueves.
    fila, columna = current_pos
    return (fila + 1, columna)
`;

const $ = (id) => document.getElementById(id);
const els = {
  section: $("account"),
  signedOut: $("signed-out"),
  signedIn: $("signed-in"),
  signIn: $("sign-in"),
  signOut: $("sign-out"),
  name: $("account-name"),
  list: $("my-bots"),
  newBot: $("new-bot"),
  status: $("account-status"),
  editor: $("editor"),
  form: $("editor-form"),
  title: $("editor-title"),
  botName: $("editor-name"),
  code: $("editor-code"),
  editorStatus: $("editor-status"),
  cancel: $("editor-cancel"),
  save: $("editor-save"),
};

const emulator =
  ["localhost", "127.0.0.1"].includes(location.hostname) &&
  new URLSearchParams(location.search).has("emulator");

const app = initializeApp(emulator ? { ...CONFIG, projectId: "demo-penguino" } : CONFIG);
export const auth = getAuth(app);
const db = getFirestore(app);
if (emulator) {
  connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
  connectFirestoreEmulator(db, "127.0.0.1", 8080);
}

let me = null;
let allBots = [];
let editing = null; // slot being edited, or null for a new bot

// ---------- Everyone's bots ----------

onSnapshot(
  collectionGroup(db, "bots"),
  (snap) => {
    allBots = snap.docs.map((d) => {
      const data = d.data({ serverTimestamps: "estimate" });
      return {
        id: `${data.uid}/${d.id}`,
        uid: data.uid,
        slot: d.id,
        name: data.name,
        ownerName: data.ownerName,
        code: data.code,
        updatedAt: data.updatedAt ? data.updatedAt.toMillis() : 0,
      };
    });
    game.setUserBots(allBots);
    renderMine();
  },
  (err) => {
    console.error(err);
    setStatus("No se pudieron cargar los bots de la comunidad.", true);
  },
);

// ---------- Sign-in ----------

// Popup is the default; browsers that block it fall back to a full-page redirect.
getRedirectResult(auth).catch((err) => console.error(err));

els.signIn.addEventListener("click", async () => {
  const provider = new GoogleAuthProvider();
  try {
    await signInWithPopup(auth, provider);
  } catch (err) {
    if (err.code === "auth/popup-blocked") {
      await signInWithRedirect(auth, provider);
    } else if (err.code !== "auth/popup-closed-by-user" && err.code !== "auth/cancelled-popup-request") {
      setStatus("No se pudo entrar. Prueba otra vez.", true);
      console.error(err);
    }
  }
});

els.signOut.addEventListener("click", () => signOut(auth));

onAuthStateChanged(auth, (user) => {
  me = user;
  game.setUser(user ? user.uid : null);
  els.signedOut.hidden = !!user;
  els.signedIn.hidden = !user;
  els.name.textContent = user ? ownerName(user) : "";
  setStatus("");
  renderMine();
});

function ownerName(user) {
  const name = (user.displayName || (user.email || "").split("@")[0] || "Anónimo").trim();
  return name.slice(0, 80) || "Anónimo";
}

// ---------- My bots ----------

function myBots() {
  if (!me) return [];
  return allBots.filter((bot) => bot.uid === me.uid).sort((a, b) => a.slot.localeCompare(b.slot));
}

function renderMine() {
  if (!me) return;
  const mine = myBots();
  els.list.replaceChildren(
    ...mine.map((bot) => {
      const li = document.createElement("li");
      li.className = "my-bot";

      const name = document.createElement("span");
      name.className = "my-bot-name";
      name.textContent = bot.name;

      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "btn btn--ghost";
      edit.textContent = "Editar";
      edit.setAttribute("aria-label", `Editar ${bot.name}`);
      edit.addEventListener("click", () => openEditor(bot));

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "btn btn--ghost";
      remove.textContent = "Borrar";
      remove.setAttribute("aria-label", `Borrar ${bot.name}`);
      remove.addEventListener("click", () => removeBot(bot));

      li.append(name, edit, remove);
      return li;
    }),
  );
  els.list.hidden = mine.length === 0;
  els.newBot.disabled = mine.length >= MAX_BOTS;
  els.newBot.textContent = mine.length >= MAX_BOTS ? `Ya tienes ${MAX_BOTS} bots` : "Nuevo bot";
}

async function removeBot(bot) {
  if (!confirm(`¿Borrar “${bot.name}”? No se puede deshacer.`)) return;
  try {
    await deleteDoc(doc(db, "users", me.uid, "bots", bot.slot));
    setStatus(`Borraste “${bot.name}”.`);
  } catch (err) {
    console.error(err);
    setStatus("No se pudo borrar el bot.", true);
  }
}

// ---------- Editor ----------

function openEditor(bot) {
  editing = bot ? bot.slot : null;
  els.title.textContent = bot ? `Editar ${bot.name}` : "Nuevo bot";
  els.botName.value = bot ? bot.name : "";
  els.code.value = bot ? bot.code : TEMPLATE;
  setEditorStatus("");
  els.save.disabled = false;
  els.editor.showModal();
  els.botName.focus();
}

els.newBot.addEventListener("click", () => openEditor(null));
els.cancel.addEventListener("click", () => els.editor.close());

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!me) return;
  const name = els.botName.value.trim();
  const code = els.code.value;

  if (!name || name.length > MAX_NAME) {
    setEditorStatus(`El nombre debe tener entre 1 y ${MAX_NAME} caracteres.`, true);
    return;
  }
  if (!code.trim() || code.length > MAX_CODE) {
    setEditorStatus(`El código debe tener entre 1 y ${MAX_CODE} caracteres (tiene ${code.length}).`, true);
    return;
  }
  const slot = editing || freeSlot();
  if (!slot) {
    setEditorStatus(`Ya tienes ${MAX_BOTS} bots. Borra uno para subir otro.`, true);
    return;
  }

  els.save.disabled = true;
  setEditorStatus("Probando tu bot durante 10 turnos…");
  const test = await game.validateBot(name, code);
  if (!test.ok) {
    setEditorStatus(`No se guardó. ${test.message}`, true);
    els.save.disabled = false;
    return;
  }

  setEditorStatus("Guardando…");
  try {
    await saveBot(slot, name, code, !editing);
  } catch (err) {
    console.error(err);
    const wait = err.code === "permission-denied";
    setEditorStatus(wait ? "Espera 10 segundos entre guardados y prueba otra vez." : "No se pudo guardar el bot.", true);
    els.save.disabled = false;
    return;
  }
  els.editor.close();
  setStatus(test.warning
    ? `Guardaste “${name}”. Ojo: en la prueba quedó eliminado. ${test.warning}`
    : `Guardaste “${name}”. Ya aparece en Comunidad.`);
});

function freeSlot() {
  const used = new Set(myBots().map((bot) => bot.slot));
  for (let i = 1; i <= MAX_BOTS; i++) if (!used.has(String(i))) return String(i);
  return null;
}

// The bot and the rate-limit stamp go in one batch; the rules reject either one alone.
function saveBot(slot, name, code, isNew) {
  const batch = writeBatch(db);
  const ref = doc(db, "users", me.uid, "bots", slot);
  if (isNew) {
    batch.set(ref, {
      uid: me.uid,
      ownerName: ownerName(me),
      name,
      code,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    });
  } else {
    batch.update(ref, { ownerName: ownerName(me), name, code, updatedAt: serverTimestamp() });
  }
  batch.set(doc(db, "botLimits", me.uid), { lastSaveAt: serverTimestamp() });
  return batch.commit();
}

// ---------- Status ----------

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle("is-error", isError);
}

function setEditorStatus(text, isError = false) {
  els.editorStatus.textContent = text;
  els.editorStatus.classList.toggle("is-error", isError);
}

els.section.hidden = false;
