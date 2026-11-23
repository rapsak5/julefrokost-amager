// Gemmer valgt fisker, fremskridt og bedste point på telefonen (localStorage).
// Virker også, hvis lageret er spærret: så huskes tingene kun, mens siden er åben.

import { SAVE_KEY } from '../config.js';

let mem = null;

function blank() {
  return { v: 1, fisher: null, mute: false, players: {} };
}

export function load() {
  if (mem) return mem;
  try {
    const raw = window.localStorage.getItem(SAVE_KEY);
    mem = raw ? { ...blank(), ...JSON.parse(raw) } : blank();
  } catch (e) {
    mem = blank();
  }
  return mem;
}

export function persist() {
  try { window.localStorage.setItem(SAVE_KEY, JSON.stringify(load())); } catch (e) { /* lageret er ikke tilgængeligt */ }
}

/** Fremskridt for én fisker: bedste point pr. bane og hvor mange baner der er åbne. */
export function player(id) {
  const s = load();
  if (!s.players[id]) s.players[id] = { best: {}, unlocked: 1, done: false };
  return s.players[id];
}

export function setFisher(id) { load().fisher = id; persist(); }

export function reset() { mem = blank(); persist(); }
