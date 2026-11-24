// Tester server/worker.js lokalt med et falsk KV-lager og et falsk ur.  Kør: node tools/test_worker.mjs
import worker from '../server/worker.js';

const store = new Map();
let writes = 0;
const env = {
  ADMIN_TOKEN: 'hemmelig',
  SCORES: {
    get: async (k, t) => (store.has(k) ? (t === 'json' ? JSON.parse(store.get(k)) : store.get(k)) : null),
    put: async (k, v) => { writes++; store.set(k, v); },
  },
};
const realNow = Date.now;
let clock = Date.UTC(2026, 10, 24, 12, 0, 0);
Date.now = () => clock;
const wait = (sec) => { clock += sec * 1000; };
const call = async (method, path, body) => {
  const res = await worker.fetch(new Request(`https://x${path}`, { method, body: body && JSON.stringify(body), headers: { 'Content-Type': 'application/json', 'CF-Connecting-IP': '1.2.3.4' } }), env);
  return { status: res.status, data: await res.json() };
};
const board = async () => (await call('GET', '/scores')).data.players;
let fail = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'ok  ' : 'FEJL'} ${name} ${extra}`); if (!ok) fail++; };

check('tom liste', Object.keys(await board()).length === 0);
check('gemmer point', (await call('POST', '/score', { fisher: 'kasper', level: 'dragoer', score: 5000 })).data.best === 5000);
check('lavere point overskriver ikke', (await call('POST', '/score', { fisher: 'kasper', level: 'dragoer', score: 100 })).data.best === 5000);
wait(80);
check('højere point overskriver', (await call('POST', '/score', { fisher: 'kasper', level: 'dragoer', score: 6000 })).data.best === 6000);
check('ukendt fisker afvises', (await call('POST', '/score', { fisher: 'hacker', level: 'dragoer', score: 1 })).status === 400);
check('ukendt bane afvises', (await call('POST', '/score', { fisher: 'mark', level: 'mars', score: 1 })).status === 400);

// Realismetjek
await call('POST', '/score', { fisher: 'mark', level: 'dragoer', score: 99999 });
check('over loftet tæller ikke', (await board()).mark?.dragoer == null);
await call('POST', '/score', { fisher: 'mark', level: 'jaguaren', score: 5000 });
check('bane uden forrige bane tæller ikke', (await board()).mark?.jaguaren == null);
wait(80);
await call('POST', '/score', { fisher: 'mark', level: 'dragoer', score: 7000 });
await call('POST', '/score', { fisher: 'mark', level: 'lufthavn', score: 8000 });
check('to rekorder på få sekunder: kun den første tæller', (await board()).mark.dragoer === 7000 && (await board()).mark.lufthavn == null);
wait(80);
await call('POST', '/score', { fisher: 'mark', level: 'lufthavn', score: 8000 });
check('efter en banes tid tæller den næste', (await board()).mark.lufthavn === 8000);
const before = writes;
await call('POST', '/score', { fisher: 'mark', level: 'lufthavn', score: 8000 });
check('samme rekord igen koster ingen skrivning', writes === before);

// Log
check('log kræver nøgle', (await call('GET', '/log')).status === 404);
const log = (await call('GET', '/log?key=hemmelig')).data.log;
check('log viser godkendte og afviste', log.some((e) => e.ok) && log.some((e) => !e.ok && e.why === 'over loftet') && log.some((e) => e.why === 'forrige bane mangler'), `(${log.length} linjer)`);
check('log har enhed og tid', !!log[0].enhed && !!log[0].t);

// Spam kan ikke æde gratiskvoten
const w0 = writes;
for (let i = 0; i < 200; i++) await call('POST', '/score', { fisher: 'kenni', level: 'copenhill', score: 1000 + i });
check('spam giver højst 60 skrivninger pr. døgn', writes - w0 <= 60, `(${writes - w0})`);

// Lukning
clock = Date.UTC(2026, 11, 27, 12, 0, 1);
check('lukket efter kl. 13.00 den 27/12', (await call('POST', '/score', { fisher: 'mark', level: 'dr', score: 10 })).status === 403);
check('listen kan stadig ses efter lukning', (await call('GET', '/scores')).data.closed === true);
Date.now = realNow;
console.log(fail ? `\n${fail} FEJL` : '\nALT OK');
process.exit(fail ? 1 : 0);
