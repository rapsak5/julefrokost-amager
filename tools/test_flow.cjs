#!/usr/bin/env node
/* Tester selve betjeningen med rigtige berøringer i en hovedløs Chrome:
   menuerne fra titel til bane, swipe op, swipe ned, tap, pause, død og nyt forsøg,
   og slutningen med hemmelighed og topscorerliste.

   Kør:  node tools/test_flow.cjs   (kræver puppeteer-core, se test_play.cjs)
*/
const http = require('http');
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.join(__dirname, 'shots');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.xml': 'application/xml', '.webmanifest': 'application/manifest+json' };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'ok  ' : 'FEJL'} ${name} ${extra}`); if (!ok) failed++; };

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const srv = http.createServer((req, res) => {
    const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html'));
    if (!p.startsWith(ROOT) || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  });
  await new Promise((r) => srv.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME || '/usr/bin/google-chrome', headless: 'new',
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  const errors = [];
  const newPage = async (query, vp = { width: 844, height: 390 }) => {
    const page = await browser.newPage();
    await page.setViewport({ ...vp, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    await page.goto(base + query, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__game && window.__game.scene.getScenes(true).some((s) => s.sys.settings.key !== 'Boot'), { timeout: 20000 });
    await sleep(500);
    return page;
  };
  // spilkoordinater -> skærmkoordinater
  const pt = async (page, gx, gy) => page.evaluate((x, y) => {
    const r = document.querySelector('#game canvas').getBoundingClientRect();
    return { x: r.left + (x * r.width) / 640, y: r.top + (y * r.height) / 360 };
  }, gx, gy);
  const tap = async (page, gx, gy) => { const p = await pt(page, gx, gy); await page.touchscreen.tap(p.x, p.y); await sleep(350); };
  const swipe = async (page, gx, gy, dy) => {
    const a = await pt(page, gx, gy); const b = await pt(page, gx, gy + dy);
    await page.touchscreen.touchStart(a.x, a.y); await sleep(30);
    await page.touchscreen.touchMove(a.x, (a.y + b.y) / 2); await sleep(20);
    await page.touchscreen.touchMove(b.x, b.y); await sleep(20);
    await page.touchscreen.touchEnd();
  };
  const active = (page, key) => page.evaluate((k) => window.__game.scene.isActive(k), key);
  const lvl = (page, fn) => page.evaluate(`(() => { const L = window.__game.scene.getScene('Level'); const p = L.player; return (${fn}); })()`);

  // ---------- A: menuer og styring ----------
  let page = await newPage('');
  check('titelskærmen vises', await active(page, 'Title'));
  await tap(page, 320, 180);
  check('tryk åbner Vælg din fisker', await active(page, 'Select'));
  await tap(page, 59 + 2 * 87, 100);
  await page.screenshot({ path: path.join(SHOTS, 'flow_select.png') });
  await tap(page, 390, 296);
  check('første gang åbner VÆLG øvebanen', (await active(page, 'Level')) && (await lvl(page, 'L.tutorial')));
  const frozen = () => page.waitForFunction(() => window.__game.scene.getScene('Level').frozen, { timeout: 15000 });
  await frozen();
  await page.screenshot({ path: path.join(SHOTS, 'flow_tutorial.png') });
  await tap(page, 320, 200);
  check('øvebanen venter, hvis man laver den forkerte bevægelse', await lvl(page, '!!L.frozen && L.stepIdx === 0'));
  await swipe(page, 320, 220, -70); await sleep(150);
  check('øvebanen: swipe op godkendes', await lvl(page, '!L.frozen && L.stepIdx === 1'));
  await frozen();
  await swipe(page, 320, 180, 70); await sleep(150);
  check('øvebanen: swipe ned godkendes', await lvl(page, '!L.frozen && L.stepIdx === 2 && p.sliding'));
  await frozen();
  await tap(page, 320, 200);
  check('øvebanen: tap godkendes', await lvl(page, '!L.frozen && L.stepIdx === 3'));
  await page.waitForFunction(() => window.__game.scene.isActive('Map'), { timeout: 20000 });
  check('efter øvebanen åbner kortet', (await page.evaluate(() => JSON.parse(localStorage.getItem('amager-julefrokost-v1')).tutorialDone)) === true);
  await sleep(400);
  check('valgt fisker er gemt (Mark)', (await page.evaluate(() => JSON.parse(localStorage.getItem('amager-julefrokost-v1')).fisher)) === 'mark');
  await page.screenshot({ path: path.join(SHOTS, 'flow_map.png') });
  await tap(page, 553, 104);
  check('SPIL starter bane 1', await active(page, 'Level') && await active(page, 'Hud'));
  await sleep(600);

  await swipe(page, 320, 220, -70); await sleep(120);
  check('swipe op: fiskeren hopper', await lvl(page, 'p.body.velocity.y < 0 || !p.onGround'));
  await page.waitForFunction(() => window.__game.scene.getScene('Level').player.onGround, { timeout: 3000 });
  await swipe(page, 320, 180, 70); await sleep(60);
  check('swipe ned: fiskeren slider', await lvl(page, 'p.sliding'));
  await page.screenshot({ path: path.join(SHOTS, 'flow_slide.png') });
  await sleep(700);
  const before = await lvl(page, 'p.swingId');
  await tap(page, 320, 200);
  check('tap: fiskeren slår', (await lvl(page, 'p.swingId')) === before + 1);

  await tap(page, 640 - 22, 20);
  check('pauseknappen sætter banen på pause', await active(page, 'Result') && await page.evaluate(() => window.__game.scene.isPaused('Level')));
  await page.screenshot({ path: path.join(SHOTS, 'flow_pause.png') });
  await tap(page, 320, 156);
  check('FORTSÆT genoptager banen', await active(page, 'Level') && !(await active(page, 'Result')));

  // lad fiskeren løbe uden hjælp, til alle liv er brugt
  for (let i = 0; i < 400 && !(await active(page, 'Result')); i++) {
    if (await active(page, 'Quiz')) await tap(page, 320, 152);   // svar et eller andet på quizzen
    await sleep(300);
  }
  const data = await page.evaluate(() => window.__game.scene.getScene('Result').sys.settings.data);
  check('uden styring dør fiskeren', data.mode === 'dead', `(checkpoint: ${data.checkpoint ? 'ja' : 'nej'})`);
  await page.screenshot({ path: path.join(SHOTS, 'flow_dead.png') });
  await tap(page, 320, 220);
  await sleep(500);
  check('PRØV IGEN starter banen med 4 liv', await active(page, 'Level') && (await lvl(page, 'L.st.hearts')) === 4);
  await page.close();

  // ---------- B: quiz og slutning ----------
  page = await newPage('?level=1&fisher=kasper');
  await page.evaluate(() => { const L = window.__game.scene.getScene('Level'); L.spawn({ type: 'q', row: 'mid', x: L.player.x + 120 }); });
  await page.waitForFunction(() => window.__game.scene.isActive('Quiz'), { timeout: 5000 });
  await sleep(300);
  await page.screenshot({ path: path.join(SHOTS, 'flow_quiz.png') });
  check('quizkassen åbner et spørgsmål og sætter banen på pause', await page.evaluate(() => window.__game.scene.isPaused('Level')));
  await page.evaluate(() => { const q = window.__game.scene.getScene('Quiz'); const b = q.buttons.find((x) => x.label.text === q.q.a[0]); window.__btn = { x: b.zone.x, y: b.zone.y }; });
  const b = await page.evaluate(() => window.__btn);
  const scoreBefore = await lvl(page, 'L.st.score');
  await tap(page, b.x, b.y);
  await sleep(1300);
  check('rigtigt svar giver point og genoptager banen', (await active(page, 'Level')) && (await lvl(page, 'L.st.score')) >= scoreBefore + 500);

  const shot = await lvl(page, `(() => { L.shotUntil = L.clock + 5000; const a = L.st.score; L.addScore(100); const dbl = L.st.score - a; p.invulnUntil = 0; const h = L.st.hearts; L.hurt(); return { dbl, lost: h - L.st.hearts }; })()`);
  check('shot giver dobbelt point og gør ikke usårlig', shot.dbl === 200 && shot.lost === 1, JSON.stringify(shot));
  await page.close();

  // svømning på Den Blå Planet
  page = await newPage('?level=3&fisher=kasper');
  check('Den Blå Planet er en svømmebane', await lvl(page, 'L.swim && p.swim && p.lane === 1'));
  await swipe(page, 320, 220, -70); await sleep(500);
  check('swipe op: svømmer en bane op', await lvl(page, 'p.lane === 0 && Math.abs(p.y - 104) < 4'));
  await swipe(page, 320, 150, 70); await sleep(350); await swipe(page, 320, 150, 70); await sleep(500);
  check('swipe ned to gange: nederste bane', await lvl(page, 'p.lane === 2 && Math.abs(p.y - 248) < 4'));
  await page.screenshot({ path: path.join(SHOTS, 'flow_swim.png') });
  const closedOk = await page.evaluate(async () => { const S = await import('./src/systems/scores.js'); return S.isClosed(Date.UTC(2026, 11, 27, 12, 0, 1)) && !S.isClosed(Date.UTC(2026, 11, 27, 11, 59, 59)); });
  check('highscoren lukker søndag 27/12 kl. 13.00', closedOk);
  await page.close();

  page = await newPage('?level=10&fisher=kasper');
  // snyd til testen: slå bossen ihjel og løb i mål
  await page.evaluate(() => { const L = window.__game.scene.getScene('Level'); L.player.invulnUntil = 1e9; L.player.body.reset(L.bossTriggerX ?? L.built.width - 400, 300); });
  await page.waitForFunction(() => { const L = window.__game.scene.getScene('Level'); return L.boss && L.boss.sprite; }, { timeout: 30000 });
  await sleep(1500);
  await page.screenshot({ path: path.join(SHOTS, 'flow_boss.png') });
  await page.evaluate(() => { const B = window.__game.scene.getScene('Level').boss; B.hit(); B.hit(); B.hit(); B.hit(); });
  await page.waitForFunction(() => window.__game.scene.isActive('Result'), { timeout: 30000 });
  const end = await page.evaluate(() => window.__game.scene.getScene('Result').sys.settings.data);
  check('sidste bane kan klares', end.mode === 'complete' && end.last === true);
  await page.screenshot({ path: path.join(SHOTS, 'flow_complete.png') });
  await tap(page, 320, 280);
  await sleep(700);
  check('HEMMELIGHEDEN åbner slutskærmen', await active(page, 'Secret'));
  await page.screenshot({ path: path.join(SHOTS, 'flow_secret.png') });
  const days = await page.evaluate(() => window.__game.scene.getScene('Secret').children.list.filter((o) => o.type === 'BitmapText' && /^\d\d$/.test(o.text)).map((t) => t.text).join(':'));
  const expect = await page.evaluate(() => Math.floor((Date.UTC(2026, 11, 27, 12, 0, 0) - Date.now()) / 86400000));
  check('nedtællingen viser rigtige dage', Number(days.split(':')[0]) === Math.max(0, expect), `(${days})`);
  await tap(page, 516, 276);
  check('TOPSCORERLISTEN åbner listen', await active(page, 'Scores'));
  await page.screenshot({ path: path.join(SHOTS, 'flow_scores.png') });
  await page.close();

  // ---------- C: telefon på højkant ----------
  page = await newPage('', { width: 390, height: 844 });
  await page.screenshot({ path: path.join(SHOTS, 'flow_portrait.png') });
  check('på højkant vises spillet stadig', await page.evaluate(() => document.querySelector('#game canvas').getBoundingClientRect().width > 300));
  await page.close();

  await browser.close();
  srv.close();
  if (errors.length) { console.log('\nFEJL I KONSOLLEN:\n' + [...new Set(errors)].join('\n')); failed++; }
  console.log(failed ? `\n${failed} TJEK FEJLEDE` : '\nALT OK');
  process.exit(failed ? 1 : 0);
})();
