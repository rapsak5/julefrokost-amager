// Topscorerlisten.
//
// Hver telefon gemmer altid sine egne point (save.js). Er SCORES_URL sat i config.js, sendes
// hver ny rekord også til den fælles liste (server/worker.js), og listen hentes derfra.
// Der er intet login: man spiller under det navn, man har valgt. Det er tillid.
// Highscoren lukker SCORES_CLOSE_UTC (julefrokostens start). Derefter tæller point ikke.
//
// Serverens API:
//   GET  /scores  -> { closesAt, closed, players: { <fisher>: { <bane>: point } } }
//   POST /score   { fisher, level, score }  -> { ok, best }

import { SCORES_URL, SCORES_CLOSE_UTC } from '../config.js';
import { FISHERS } from '../data/fishers.js';
import { LEVELS } from '../data/levels.js';
import * as Save from './save.js';

export function isClosed(now = Date.now()) { return now >= SCORES_CLOSE_UTC; }
export function isShared() { return !!SCORES_URL; }

/** Gemmer resultatet for en klaret bane. Næste bane åbnes også, når highscoren er lukket. */
export function recordLevel(fisherId, levelIndex, score) {
  const p = Save.player(fisherId);
  const id = LEVELS[levelIndex].id;
  p.unlocked = Math.min(LEVELS.length, Math.max(p.unlocked, levelIndex + 2));
  if (levelIndex === LEVELS.length - 1) p.done = true;
  if (isClosed()) { Save.persist(); return { isBest: false, closed: true, total: totalFor(fisherId) }; }
  const isBest = score > (p.best[id] || 0);
  if (isBest) { p.best[id] = score; send(fisherId, id, score); }
  Save.persist();
  return { isBest, closed: false, total: totalFor(fisherId) };
}

export function totalFor(fisherId) {
  return Object.values(Save.player(fisherId).best).reduce((a, b) => a + b, 0);
}

function rows(bestFor) {
  return FISHERS.map((f) => {
    const best = bestFor(f.id) || {};
    const reached = LEVELS.reduce((max, l, i) => (best[l.id] != null ? i + 1 : max), 0);
    const score = LEVELS.reduce((sum, l) => sum + (best[l.id] || 0), 0);
    return { id: f.id, name: f.name, score, reached };
  }).sort((a, b) => b.score - a.score);
}

/** Listen fra denne telefon alene. */
export function localBoard() { return rows((id) => Save.player(id).best); }

/**
 * Den fælles liste. Slår telefonens egne point sammen med serverens, så en rekord, der ikke
 * nåede frem (fx uden net), stadig vises og bliver sendt igen. Returnerer null uden server.
 */
export async function fetchBoard() {
  if (!SCORES_URL) return null;
  try {
    const res = await fetch(`${SCORES_URL}/scores`, { cache: 'no-store' });
    if (!res.ok) return null;
    const data = await res.json();
    const server = data.players || {};
    const merged = {};
    for (const f of FISHERS) {
      const local = Save.player(f.id).best;
      const remote = server[f.id] || {};
      merged[f.id] = { ...remote };
      for (const [lvl, sc] of Object.entries(local)) {
        if (sc > (remote[lvl] || 0)) {
          merged[f.id][lvl] = sc;
          if (!isClosed()) send(f.id, lvl, sc);
        }
      }
    }
    return { rows: rows((id) => merged[id]), closed: !!data.closed };
  } catch (e) {
    return null;
  }
}

function send(fisher, level, score) {
  if (!SCORES_URL) return;
  try {
    fetch(`${SCORES_URL}/score`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fisher, level, score }), keepalive: true,
    }).catch(() => {});
  } catch (e) { /* prøves igen næste gang listen hentes */ }
}
