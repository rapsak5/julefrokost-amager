#!/usr/bin/env node
/* Automatisk gennemspilning i en hovedløs Chrome.

   En robot spiller alle baner igennem i ét hug (uden at bruge checkpoints) og fortæller,
   hvad den eventuelt dør af. Gemmer skærmbilleder i tools/shots/.
   Testen sender ALDRIG noget til den rigtige topscorerliste: alle kald ud af huset stoppes.
   Banerne startes direkte i spillet, fordi testgenvejene i adressen er fjernet (24/11).

   Kræver:  npm i puppeteer-core   og en Chrome (sti i CHROME, ellers /usr/bin/google-chrome)
   Kør:     node tools/test_play.cjs            (ONLY=8,10 kører kun bane 8 og 10,
                                                RETRIES=8 lader robotten starte ved checkpoints)
   Robotten blev klogere 27/11: den hopper, så toppen af hoppet ligger midt over tingen
   (høje figurer som rockere kræver et tidligere hop end en kegle), og den hopper over
   hullerne på løbebåndet i bosskampen.
*/
const http = require('http');
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.join(__dirname, 'shots');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.xml': 'application/xml', '.webmanifest': 'application/manifest+json' };

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html'));
      if (!p.startsWith(ROOT) || !fs.existsSync(p)) { res.writeHead(404); res.end('404'); return; }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

// Køres inde på siden: stepper spillet manuelt (hurtigere end realtid) og lader robotten styre.
async function simulate(maxMs) {
  const game = window.__game;
  game.loop.stop();
  let t = game.loop.now || performance.now();
  const log = { frames: 0, hurt: 0, events: [] };
  const step = (render) => { t += 1000 / 60; if (render) game.step(t, 1000 / 60); else game.headlessStep(t, 1000 / 60); };
  const active = (k) => game.scene.isActive(k);
  let lastHearts = null;
  for (let ms = 0; ms < maxMs; ms += 1000 / 60) {
    step(false);
    log.frames++;
    if (active('Quiz')) {
      const q = game.scene.getScene('Quiz');
      if (!q.locked) q.pick(q.q.a[0], q.q.a[0]);
      continue;
    }
    if (active('Result')) {
      const d = game.scene.getScene('Result').sys.settings.data;
      if (d.mode === 'dead' && d.checkpoint && (log.retries || 0) < (+process.env.RETRIES || 0)) {
        log.retries = (log.retries || 0) + 1; log.events.push(`død, starter ved checkpoint x=${Math.round(d.checkpoint.x)}`);
        game.scene.stop('Result'); game.scene.stop('Level'); game.scene.start('Level', { levelIndex: d.levelIndex, checkpoint: d.checkpoint }); lastHearts = null; continue;
      }
      log.result = d; break;
    }
    const L = game.scene.getScene('Level');
    if (!active('Level') || L.ended || !L.player) continue;
    log.cps = Math.max(log.cps || 0, L.ents.filter((e) => e.def.kind === 'checkpoint' && e.done).length + (L.checkpoint ? 0 : 0));
    const p = L.player;
    if (lastHearts == null) lastHearts = L.st.hearts;
    if (L.st.hearts < lastHearts) {
      log.hurt += lastHearts - L.st.hearts;
      const near = L.ents.filter((e) => e.alive && e.def.kind === 'enemy').map((e) => ({ e, r: L.entRect(e) })).filter((o) => Math.abs(o.r.x - p.x) < 90)
        .map((o) => `${o.e.sp.type}:${o.e.def.anim || o.e.def.frame}@${Math.round(o.r.x - p.x)},${Math.round(o.r.y)}+${o.r.h}`).join('|');
      const pit = L.built.pits.some((q) => p.x > q.x0 - 60 && p.x < q.x1 + 80);
      log.causes = log.causes || {}; const key = pit ? 'hul' : (near.split('|')[0] || 'ukendt').replace(/@.*/, ''); log.causes[key] = (log.causes[key] || 0) + 1;
      if (log.events.length < 40) log.events.push(`x=${Math.round(p.x)} v=${Math.round(L.speed)} ${pit ? 'HUL ' : ''}${near} ground=${p.onGround} slide=${p.sliding} y=${Math.round(p.y)}`);
    }
    lastHearts = L.st.hearts;
    const speed = L.speed;
    const lead = speed * 0.12;
    if (L.swim) {
      // under vand: find den bane, hvor den nærmeste fare er længst væk, og svøm derhen
      const lanes = [104, 176, 248];
      const danger = [9999, 9999, 9999];
      for (const e of L.ents) {
        if (!e.alive || e.def.kind !== 'enemy') continue;
        const r = L.entRect(e);
        const dx = r.x - (p.x + 6);
        if (dx < -r.w - 40 || dx > 300) continue;
        const cost = Math.max(dx, 0) + (e.def.hittable ? 200 : 0);   // en haj kan man slås med, en gople ikke
        lanes.forEach((ly, i) => { if (r.y < ly + 16 && r.y + r.h > ly - 16) danger[i] = Math.min(danger[i], cost); });
        if (e.def.hittable && dx < 70 && r.y < p.y + 20 && r.y + r.h > p.y - 20) L.command('tap');
      }
      const best = danger.indexOf(Math.max(...danger));
      if (danger[p.lane] < 260 && danger[best] > danger[p.lane] + 30 && Math.abs(p.y - lanes[p.lane]) < 4) {
        const sw = L.shotActive();
        if (best < p.lane) L.command(sw ? 'down' : 'up'); else if (best > p.lane) L.command(sw ? 'up' : 'down');
      }
      continue;
    }
    // huller
    for (const pit of L.built.pits) { if (p.onGround && p.x > pit.x0 - 34 - lead * 0.2 && p.x < pit.x0 - 4) L.command(L.shotActive() ? 'down' : 'up'); }
    // ting forude
    for (const e of L.ents) {
      if (!e.alive || e.def.kind !== 'enemy') continue;
      const r = L.entRect(e);
      const dx = r.x - (p.x + 11);
      if (dx < -r.w - 20 || dx > 140) continue;
      if (e.def.low && !e.def.hittable) { if (dx < 40 + lead && !p.sliding && p.onGround) L.command(L.shotActive() ? 'up' : 'down'); }
      else if (e.def.hittable) { if (dx < 52 && !p.holdSlide) L.command('tap'); }   // først når pokalen kan nå
      else if (p.onGround && dx > -6) {
        // hop, så toppen af hoppet ligger midt over tingen (høje figurer kræver et tidligere hop end en kegle)
        const rel = speed - (e.def.vx || 0);
        if (dx < 0.4 * rel - (r.w + 22) / 2 + 6) L.command(L.shotActive() ? 'down' : 'up');
      }
    }
    // huller på løbebåndet i bosskampen
    for (const q of (L.arenaPits || [])) { if (p.onGround && q.x0 - p.x < 34 + lead * 0.2 && q.x0 - p.x > 4) L.command(L.shotActive() ? 'down' : 'up'); }
    if (L.boss && L.boss.sprite && L.boss.state === 'swoop') {
      const dx = L.boss.rect().x - (p.x + 11);
      if (dx < 70) L.command('tap');
    }
  }
  step(true);
  const L = game.scene.getScene('Level');
  log.hearts = L.st.hearts; log.score = L.st.score; log.bottles = L.st.bottles; log.x = Math.round(L.player.x); log.width = L.built.width;
  game.loop.start(game.step.bind(game));
  return log;
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME || '/usr/bin/google-chrome', headless: 'new',
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'],
  });
  const errors = [];
  const blocked = [];
  const open = async (query = '') => {
    const page = await browser.newPage();
    await page.setViewport({ width: 844, height: 390, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
    await page.setRequestInterception(true);
    page.on('request', (r) => { if (r.url().startsWith(base) || r.url().startsWith('data:')) r.continue(); else { blocked.push(r.url()); r.respond({ status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*' }, body: '{"ok":true}' }); } });
    page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errors.push(`[${query}] ${m.type()}: ${m.text()}`); });
    page.on('pageerror', (e) => errors.push(`[${query}] pageerror: ${e.message}`));
    await page.goto(base + query, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__game && window.__game.scene.getScenes(true).some((s) => s.sys.settings.key !== 'Boot'), { timeout: 20000 });
    await new Promise((r) => setTimeout(r, 700));
    return page;
  };
  const shot = (page, name) => page.screenshot({ path: path.join(SHOTS, name + '.png') });

  // 1) skærmene
  for (const scene of ['Scores']) {
    const page = await open(`?scene=${scene}`);
    await shot(page, `skaerm_${scene.toLowerCase()}`);
    await page.close();
  }

  // 2) alle baner med robot
  const levels = await (async () => { const page = await open('?scene=Title'); const n = await page.evaluate(async () => (await import('./src/data/levels.js')).LEVELS.length); await page.close(); return n; })();
  let ok = true;
  const only = (process.env.ONLY || '').split(',').filter(Boolean).map(Number);
  for (let i = 1; i <= levels; i++) {
    if (only.length && !only.includes(i)) continue;
    const page = await open('?scene=Title');
    await page.evaluate((li) => { localStorage.setItem('amager-julefrokost-v1', JSON.stringify({ fisher: 'kasper', tutorialDone: true })); const g = window.__game; g.scene.getScenes(true).forEach((sc) => g.scene.stop(sc.sys.settings.key)); g.scene.start('Level', { levelIndex: li }); }, i - 1);
    await new Promise((r) => setTimeout(r, 800));
    await page.evaluate(simulate.toString() + '; window.__sim = simulate;');
    const mid = await page.evaluate(() => window.__sim(12000));
    await new Promise((r) => setTimeout(r, 300));
    await shot(page, `bane${i}_a`);
    const res = await page.evaluate(() => window.__sim(260000));
    await new Promise((r) => setTimeout(r, 400));
    await shot(page, `bane${i}_slut`);
    const mode = res.result ? res.result.mode : 'ikke færdig';
    if (mode !== 'complete') ok = false;
    console.log(`bane ${i}: ${mode}  genstarter=${(mid.retries||0)+(res.retries||0)}  hjerter=${res.hearts}  point=${res.score}  bajere=${res.bottles}  x=${res.x}/${res.width}  tabte liv=${mid.hurt + res.hurt}`, '\n   ' + JSON.stringify({ ...(mid.causes||{}), ...(res.causes||{}) }) + '\n   ' + [...mid.events, ...res.events].slice(0, 12).join('\n   '));
    await page.close();
  }

  console.log('kald til topscorerlisten (stoppet, intet sendt):', [...new Set(blocked)].length);
  await browser.close();
  srv.close();
  if (errors.length) { console.log('\nFEJL I KONSOLLEN:\n' + [...new Set(errors)].join('\n')); ok = false; }
  console.log(ok ? '\nALT OK' : '\nNOGET FEJLEDE');
  process.exit(ok ? 0 : 1);
})();
