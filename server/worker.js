// Fælles topscorerliste til Julefrokost på Amager. En lille Cloudflare Worker med ét KV-lager.
//
//   GET  /scores  -> { closesAt, closed, players: { <fisher>: { <bane>: point } } }
//   POST /score   { fisher, level, score }  -> { ok, best }
//   GET  /log     -> de seneste indsendelser (kræver ?key=<ADMIN_TOKEN>, findes kun hvis ADMIN_TOKEN er sat)
//
// Der er intet login. Serveren gemmer kun hver fiskers bedste point pr. bane og afviser alt
// efter julefrokostens start (søndag 27/12 kl. 13.00). Lister her skal passe med
// src/data/fishers.js og src/data/levels.js.
//
// Realismetjek mod snyd (24/11):
//   1. Loft pr. bane: banens højst mulige point (alle bajere, alle fjender, quiz, hjerter, boss) gange 1,5.
//   2. Rækkefølge: en bane tæller kun, hvis fiskeren allerede har point på banen før.
//   3. Tid: der skal gå mindst MIN_GAP_MS mellem to godkendte rekorder for samme fisker.
//      Den korteste bane tager ca. 95 sekunder at løbe igennem (25/11).
// Alle indsendelser logges (godkendte og afviste) med tid, land og et kort id for enheden.
// Afviste svarer stadig { ok: true }, så en snyder ikke kan se, hvilket tjek han ramte.
//
// Alt ligger i én KV-nøgle (state), så hver indsendelse koster højst én skrivning.
// Afviste logges højst MAX_REJECT_LOGS gange pr. døgn, så spam ikke æder gratiskvoten.

const FISHERS = ['andreas', 'anders', 'mark', 'claus', 'theis', 'kenni', 'kasper'];
const LEVELS = ['dragoer', 'lufthavn', 'blaaplanet', 'idraetspark', 'faelled', 'dr', 'campus', 'brygge', 'center', 'amagerbio', 'strandpark', 'jaguaren', 'copenhill'];
// Højst mulige point pr. bane (udregnet fra src/data/levels.js 25/11, 13 baner) gange 1,5, rundet op
const MAX = {
  dragoer: 31000, lufthavn: 38000, blaaplanet: 35000, idraetspark: 36000, faelled: 41000,
  dr: 43000, campus: 41000, brygge: 48000, center: 42000, amagerbio: 44000,
  strandpark: 42000, jaguaren: 40000, copenhill: 89000,
};
const CLOSES_AT = Date.UTC(2026, 11, 27, 12, 0, 0);
const MIN_GAP_MS = 55 * 1000;
const LOG_MAX = 400;
const MAX_REJECT_LOGS = 60;
const KEY = 'state';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const json = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...CORS },
});

async function load(env) {
  const s = (await env.SCORES.get(KEY, 'json')) || {};
  return { players: s.players || {}, last: s.last || {}, log: s.log || [], rejects: s.rejects || { day: '', n: 0 } };
}

async function device(request) {
  const ip = request.headers.get('CF-Connecting-IP') || '';
  const ua = request.headers.get('User-Agent') || '';
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`amager:${ip}:${ua}`));
  return [...new Uint8Array(buf)].slice(0, 3).map((b) => b.toString(16).padStart(2, '0')).join('');
}

function check(state, fisher, level, score, now) {
  if (score > MAX[level]) return 'over loftet';
  const i = LEVELS.indexOf(level);
  const mine = state.players[fisher] || {};
  if (i > 0 && mine[LEVELS[i - 1]] == null) return 'forrige bane mangler';
  const last = state.last[fisher] || 0;
  if (now - last < MIN_GAP_MS) return `for hurtigt (${Math.round((now - last) / 1000)} sek.)`;
  return null;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const { pathname } = url;
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    const now = Date.now();
    const closed = now >= CLOSES_AT;

    if (request.method === 'GET' && pathname === '/scores') {
      const state = await load(env);
      return json({ closesAt: CLOSES_AT, closed, players: state.players });
    }

    if (request.method === 'GET' && pathname === '/log') {
      if (!env.ADMIN_TOKEN || url.searchParams.get('key') !== env.ADMIN_TOKEN) return json({ ok: false, error: 'Ikke fundet' }, 404);
      const state = await load(env);
      return json({ players: state.players, log: state.log.slice().reverse() });
    }

    if (request.method === 'POST' && pathname === '/score') {
      if (closed) return json({ ok: false, error: 'Highscoren er lukket' }, 403);
      let body;
      try { body = await request.json(); } catch (e) { return json({ ok: false, error: 'Ugyldig JSON' }, 400); }
      const { fisher, level } = body || {};
      const score = Math.floor(Number(body?.score));
      if (!FISHERS.includes(fisher) || !LEVELS.includes(level) || !Number.isFinite(score) || score < 0) {
        return json({ ok: false, error: 'Ugyldige data' }, 400);
      }
      const state = await load(env);
      const mine = state.players[fisher] || {};
      if (score <= (mine[level] || 0)) return json({ ok: true, best: mine[level] || 0 });   // ingen ny rekord, intet at gemme

      const reason = check(state, fisher, level, score, now);
      // Samme rekord sendt to gange lige efter hinanden (telefonen sender igen, når listen hentes): ignorér
      if (reason && state.log.some((e) => e.ok && e.fisher === fisher && e.level === level && e.score === score)) {
        return json({ ok: true, best: Math.max(score, mine[level] || 0) });
      }
      const entry = {
        t: new Date(now).toLocaleString('da-DK', { timeZone: 'Europe/Copenhagen' }),
        fisher, level, score,
        ok: !reason,
        ...(reason ? { why: reason } : {}),
        land: request.cf?.country || '',
        enhed: await device(request),
      };

      if (reason) {
        const day = new Date(now).toISOString().slice(0, 10);
        if (state.rejects.day !== day) state.rejects = { day, n: 0 };
        if (state.rejects.n >= MAX_REJECT_LOGS) return json({ ok: true, best: mine[level] || 0 });
        state.rejects.n += 1;
      } else {
        mine[level] = score;
        state.players[fisher] = mine;
        state.last[fisher] = now;
      }
      state.log.push(entry);
      if (state.log.length > LOG_MAX) state.log = state.log.slice(-LOG_MAX);
      await env.SCORES.put(KEY, JSON.stringify(state));
      return json({ ok: true, best: mine[level] || 0 });
    }

    return json({ ok: false, error: 'Ikke fundet' }, 404);
  },
};
