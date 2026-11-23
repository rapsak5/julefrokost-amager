// Tester server/worker.js lokalt med et falsk KV-lager.  Kør: node tools/test_worker.mjs
import worker from '../server/worker.js';

const store = new Map();
const env = { SCORES: { get: async (k, t) => (store.has(k) ? (t === 'json' ? JSON.parse(store.get(k)) : store.get(k)) : null), put: async (k, v) => store.set(k, v) } };
const call = async (method, path, body) => {
  const res = await worker.fetch(new Request(`https://x${path}`, { method, body: body && JSON.stringify(body), headers: { 'Content-Type': 'application/json' } }), env);
  return { status: res.status, data: await res.json() };
};
let fail = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'ok  ' : 'FEJL'} ${name} ${extra}`); if (!ok) fail++; };

check('tom liste', (await call('GET', '/scores')).data.players && Object.keys((await call('GET', '/scores')).data.players).length === 0);
check('gemmer point', (await call('POST', '/score', { fisher: 'kasper', level: 'dragoer', score: 5000 })).data.best === 5000);
check('lavere point overskriver ikke', (await call('POST', '/score', { fisher: 'kasper', level: 'dragoer', score: 100 })).data.best === 5000);
check('højere point overskriver', (await call('POST', '/score', { fisher: 'kasper', level: 'dragoer', score: 6000 })).data.best === 6000);
check('ukendt fisker afvises', (await call('POST', '/score', { fisher: 'hacker', level: 'dragoer', score: 1 })).status === 400);
check('ukendt bane afvises', (await call('POST', '/score', { fisher: 'mark', level: 'mars', score: 1 })).status === 400);
check('urealistiske point afvises', (await call('POST', '/score', { fisher: 'mark', level: 'dr', score: 9e9 })).status === 400);
const g = await call('GET', '/scores');
check('listen indeholder rekorden', g.data.players.kasper.dragoer === 6000 && g.data.closed === false);
const realNow = Date.now;
Date.now = () => Date.UTC(2026, 11, 27, 12, 0, 1);
check('lukket efter kl. 13.00 den 27/12', (await call('POST', '/score', { fisher: 'mark', level: 'dr', score: 10 })).status === 403);
check('listen kan stadig ses efter lukning', (await call('GET', '/scores')).data.closed === true);
Date.now = realNow;
console.log(fail ? `\n${fail} FEJL` : '\nALT OK');
process.exit(fail ? 1 : 0);
