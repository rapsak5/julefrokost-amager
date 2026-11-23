// Fælles topscorerliste til Julefrokost på Amager. En lille Cloudflare Worker med ét KV-lager.
//
//   GET  /scores  -> { closesAt, closed, players: { <fisher>: { <bane>: point } } }
//   POST /score   { fisher, level, score }  -> { ok, best }
//
// Der er intet login. Serveren gemmer kun hver fiskers bedste point pr. bane, tjekker at navn,
// bane og point giver mening, og afviser alt efter julefrokostens start (søndag 27/12 kl. 13.00).
// Lister her skal passe med src/data/fishers.js og src/data/levels.js.

const FISHERS = ['andreas', 'anders', 'mark', 'claus', 'theis', 'kenni', 'kasper'];
const LEVELS = ['dragoer', 'lufthavn', 'blaaplanet', 'idraetspark', 'faelled', 'dr', 'campus', 'center', 'jaguaren', 'copenhill'];
const CLOSES_AT = Date.UTC(2026, 11, 27, 12, 0, 0);
const MAX_SCORE = 80000;      // mere end en bane realistisk kan give, også med shots
const KEY = 'board';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const json = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...CORS },
});

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    const closed = Date.now() >= CLOSES_AT;

    if (request.method === 'GET' && pathname === '/scores') {
      const players = (await env.SCORES.get(KEY, 'json')) || {};
      return json({ closesAt: CLOSES_AT, closed, players });
    }

    if (request.method === 'POST' && pathname === '/score') {
      if (closed) return json({ ok: false, error: 'Highscoren er lukket' }, 403);
      let body;
      try { body = await request.json(); } catch (e) { return json({ ok: false, error: 'Ugyldig JSON' }, 400); }
      const { fisher, level } = body || {};
      const score = Math.floor(Number(body?.score));
      if (!FISHERS.includes(fisher) || !LEVELS.includes(level) || !Number.isFinite(score) || score < 0 || score > MAX_SCORE) {
        return json({ ok: false, error: 'Ugyldige data' }, 400);
      }
      const players = (await env.SCORES.get(KEY, 'json')) || {};
      const mine = players[fisher] || (players[fisher] = {});
      if (score > (mine[level] || 0)) {
        mine[level] = score;
        await env.SCORES.put(KEY, JSON.stringify(players));
      }
      return json({ ok: true, best: mine[level] });
    }

    return json({ ok: false, error: 'Ikke fundet' }, 404);
  },
};
