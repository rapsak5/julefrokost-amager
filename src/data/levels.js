// Banerne. En bane er en liste af byggeklodser (CHUNKS), som lægges efter hinanden.
//
// Hver byggeklods er fire rækker tegn, hvor ét tegn er én kolonne (48 px):
//   hi   ting i hophøjde
//   mid  ting i hovedhøjde (slide under eller slå)
//   lo   ting på jorden
//   fl   gulvet:  # = jord,  _ = hul
//
// Tegn:
//   .  ingenting          b  bajer            s  shot (valgfrit)   h  hjerte
//   q  quizkasse          d  går på jorden    f  flyver i hovedhøjde
//   k  forhindring, der kan slås væk          x  forhindring, der IKKE kan slås væk (hop)
//   o  bold, der hopper   m  tung maskine (to slag)                l  noget lavt (slide)
//   c  checkpoint         g  mål              B  boss (Kæmpeduen)
// Hvordan d, f, k, x, m og l ser ud på den enkelte bane, står i THEMES i entities.js
// (fx droner i lufthavnen, bolde i idrætsparken og rockere på Jaguaren).
//
// Rækker, der mangler, fyldes ud af sig selv. Mellem klodserne indsættes "gap" tomme kolonner.
// { hint: 'TEKST' } i en bane viser en besked på skærmen på det sted.
// Sværhedsgrad: speed (px/sek.) og gap er de to nemmeste håndtag.
//
// swim: true gør banen til en undervandsbane. Så er hi, mid og lo tre svømmebaner,
// swipe op og ned skifter bane, og der er ingen huller. Brug klodserne, der starter med w.

import { COL, GAME_W, PLAYER_SCREEN_X } from '../config.js';
import { entityDef } from './entities.js';

export const CHUNKS = {
  r4: { lo: '....' },
  r8: { lo: '........' },
  b3: { lo: 'b.b.b' },
  bhi: { hi: '.bbb.' },
  bwave: { hi: '...b.b...', lo: '.b.....b.' },
  // én ting ad gangen
  k: { hi: '..b..', lo: '..k..' },
  d: { lo: '...d.' },
  f: { mid: '...f.', lo: '...b.' },
  l: { mid: '...l.', lo: '..bbb' },
  x: { hi: '..b..', lo: '..x..' },
  o: { hi: '....o.' },
  m: { lo: '.....m.' },
  p: { hi: '..bb..', fl: '##__##' },
  // to ting i træk
  kk: { hi: '..b....b..', lo: '..k....k..' },
  dd: { lo: '...d....d.' },
  ff: { mid: '...f.....f.' },
  ll: { mid: '...l.....l.', lo: '..bb....bb.' },
  oo: { hi: '....o.....o.' },
  pp: { hi: '..bb......bb..', fl: '##__######__##' },
  kd: { lo: '..k...d.' },
  xd: { hi: '..b.......', lo: '..x......d' },
  df: { mid: '.......f..', lo: '..d.......' },
  kl: { hi: '..b.......', mid: '........l.', lo: '..k.....b.' },
  lk: { mid: '..l........', lo: '..b......k.' },
  pk: { hi: '..bb.....b..', lo: '.........k..', fl: '##__########' },
  pd: { hi: '..bb.....', lo: '.......d.', fl: '##__#####' },
  // tre ting i træk
  dfd: { mid: '......f....', lo: '..d......d.' },
  kfk: { hi: '..b.......b.', mid: '......f.....', lo: '..k.......k.' },
  // svære (afstandene er regnet ud, så de kan klares ved 380 px/sek.)
  xdx: { hi: '..b................', lo: '..x.......d.......x.' },
  lfl: { mid: '..l.......f.......l.', lo: '..bbb...............' },
  pkf: { hi: '..bb..............', mid: '..............f...', lo: '.........k........', fl: '##__##############' },
  ppp: { hi: '..bb......bb......bb..', fl: '##__######__######__##' },
  kfkf: { mid: '......f.......f.', lo: '..k.......k.....' },
  xx: { hi: '..b.......b..', lo: '..x.......x..' },
  dfdf: { mid: '........f.........f.', lo: '..d.........d.......' },
  xlx: { hi: '..b................', mid: '..........l........', lo: '..x...............x.' },
  pdp: { hi: '..bb..........bb..', lo: '.........d........', fl: '##__##########__##' },
  // kun Sundby Idrætspark (bolde)
  ooo: { hi: '....o.....o.....o.' },
  od: { hi: '....o......', lo: '.........d.' },
  // kun baner med tunge maskiner (Fælleden og DR)
  mm: { lo: '.....m.........m.' },
  mx: { hi: '..........b.', lo: '.....m....x.' },
  // under vand (kun til baner med swim: true)
  wb: { mid: 'b.b.b' },
  wb2: { hi: '...bb', lo: 'bb...' },
  wx1: { hi: '..bb.', mid: '...x.' },
  wx2: { hi: '...x.', mid: '..bbb', lo: '...x.' },
  wx3: { hi: '..bbb', mid: '...x.', lo: '...x.' },
  wxx: { hi: '...x......', mid: '...x.....x', lo: '..b......x' },
  wxx2: { hi: '..b......x', mid: '...x.....x', lo: '...x......' },
  wd1: { hi: '....d', mid: '..b..' },
  wd2: { mid: '....d', lo: '..b..' },
  wd3: { hi: '..b..', lo: '....d' },
  wdd: { hi: '....d...', mid: '..b..b..', lo: '.......d' },
  wdx: { hi: '...x.', mid: '....d', lo: '...x.' },
  wk: { mid: '...k.' },
  wkk: { hi: '...k...', mid: '......k', lo: '...b...' },
  wf: { mid: '..b...', lo: '.....f' },
  wf2: { hi: '.....f', mid: '..bb..', lo: '.....f' },
  wzig: { hi: '..x.....x...', mid: '..x.........', lo: '........x...' },
  wsh: { hi: '..x.....', mid: '....d...', lo: '..x.....' },
  wjj: { hi: '....x.....x', mid: '.x.....x...', lo: '....x.....x' },
  wdd2: { hi: '..d.....', mid: '.....x..', lo: '..d.....' },
  // ting at samle op
  q: { mid: '..q..' },
  s: { hi: '.s.' },
  h: { hi: '.h.' },
  c: { lo: '..c..' },
  g: { lo: '......g...' },
  boss: { lo: '....B' },
};

// Øvebanen: tre ting, der hver stopper spillet, indtil man laver den rigtige bevægelse.
export const TUTORIAL = {
  id: 'tutorial', name: 'Øvebane', theme: 'dragoer', speed: 160, gap: 4, tutorial: true,
  layout: ['r8', { lo: '..k..' }, 'r4', { mid: '..l..' }, 'r4', { lo: '..d..' }, 'r4', 'b3', { lo: '...g..' }],
  steps: [
    { type: 'k', expect: 'up', dist: 56, text: 'SWIPE OP FOR AT HOPPE' },
    { type: 'l', expect: 'down', dist: 84, text: 'SWIPE NED FOR AT SLIDE' },
    { type: 'd', expect: 'tap', dist: 52, text: 'TAP FOR AT SLÅ MED POKALEN' },
  ],
};

// ---------------------------------------------------------------------------
// Banerne bygges af en kort indledning (intro), bølger og en afslutning (outro).
// Hver bølge trækker n byggeklodser fra en pulje, så banen bliver sværere hen ad vejen.
// Trækningen er fast pr. bane (samme bane hver gang), så man kan lære den.
// Mellem bølgerne kommer et checkpoint. quiz: true og shot: true lægger en quizkasse
// eller et shot midt i bølgen, hint viser en besked lige før bølgen.
// speed: [start, slut] i px/sek. Farten stiger jævnt gennem banen.
// extra: banens egne klodser, der lægges i puljerne (fx bolde på stadion).
// ---------------------------------------------------------------------------
export const POOLS = {
  easy: ['k', 'd', 'f', 'l', 'x', 'p', 'kk', 'dd', 'ff'],
  med: ['kd', 'xd', 'df', 'kl', 'lk', 'pk', 'pd', 'll', 'pp', 'dfd', 'kfk'],
  hard: ['xdx', 'lfl', 'pkf', 'ppp', 'kfkf', 'xx', 'dfdf', 'xlx', 'pdp', 'dfd', 'kfk'],
};
export const SWIM_POOLS = {
  easy: ['wb', 'wb2', 'wx1', 'wx2', 'wk', 'wd1', 'wd2', 'wd3', 'wf'],
  med: ['wx3', 'wxx', 'wxx2', 'wdd', 'wdx', 'wkk', 'wf2'],
  hard: ['wzig', 'wsh', 'wjj', 'wdd2', 'wxx', 'wxx2', 'wdx'],
};
const BALLS = { easy: ['o'], med: ['oo', 'od'], hard: ['ooo', 'od'] };
const MACHINES = { easy: ['m'], med: ['m', 'mx'], hard: ['mm', 'mx'] };

export const LEVELS = [
  {
    id: 'dragoer', name: 'Dragør Havn', theme: 'dragoer', speed: [220, 265], gap: 2,
    intro: ['r8', 'b3', 'k', 'd', 'l', 'p', { hint: 'SLÅ PÅ QUIZKASSEN' }, 'q'],
    waves: [{ n: 8, pool: 'easy' }, { n: 7, pool: 'med', shot: true, hint: 'SHOT ER VALGFRIT: DOBBELT POINT, MEN OP OG NED BYTTER OM' }, { n: 3, pool: 'hard' }],
    outro: ['b3', 'g'],
  },
  {
    id: 'lufthavn', name: 'Lufthavnen', theme: 'lufthavn', speed: [235, 285], gap: 2,
    intro: ['r8', 'b3', { hint: 'DRONER: SLÅ DEM NED ELLER UNDGÅ DEM' }, 'd', 'f'],
    waves: [{ n: 8, pool: 'easy', quiz: true }, { n: 10, pool: 'med', shot: true }, { n: 5, pool: 'hard', quiz: true }],
    outro: ['b3', 'g'],
  },
  {
    id: 'blaaplanet', name: 'Den Blå Planet', theme: 'blaaplanet', speed: [230, 280], gap: 2, swim: true,
    intro: ['r8', { hint: 'SWIPE OP OG NED FOR AT SVØMME OP OG NED' }, 'wb', 'wb2', { hint: 'GOPLER BRÆNDER: SVØM UDENOM' }, 'wx1',
      { hint: 'HAJER: TO SLAG ELLER SVØM UDENOM' }, 'wd2'],
    waves: [{ n: 8, pool: 'easy', quiz: true }, { n: 10, pool: 'med', shot: true }, { n: 6, pool: 'hard', quiz: true }],
    outro: ['wb', 'g'],
  },
  {
    id: 'idraetspark', name: 'Sundby Idrætspark', theme: 'idraetspark', speed: [250, 305], gap: 2, extra: BALLS,
    intro: ['r8', 'b3', { hint: 'BOLDE: SLÅ DEM VÆK ELLER UNDGÅ DEM' }, 'o', { hint: 'HÆKKE SKAL MAN HOPPE OVER' }, 'x'],
    waves: [{ n: 7, pool: 'easy', quiz: true }, { n: 10, pool: 'med', shot: true }, { n: 7, pool: 'hard', quiz: true }],
    outro: ['b3', 'g'],
  },
  {
    id: 'faelled', name: 'Amager Fælled', theme: 'faelled', speed: [260, 315], gap: 2, extra: MACHINES,
    intro: ['r8', 'b3', { hint: 'KØER SLÅR MAN IKKE. HOP!' }, 'x', { hint: 'BULLDOZER: TO SLAG ELLER ET HOP' }, 'm'],
    waves: [{ n: 6, pool: 'easy', quiz: true }, { n: 11, pool: 'med', shot: true }, { n: 8, pool: 'hard', quiz: true }],
    outro: ['b3', 'g'],
  },
  {
    id: 'dr', name: 'DR Byen', theme: 'dr', speed: [270, 330], gap: 2, extra: MACHINES,
    intro: ['r8', 'b3', { hint: 'LEDNINGER: HOP OVER' }, 'x', 'l'],
    waves: [{ n: 6, pool: 'easy', quiz: true }, { n: 12, pool: 'med', shot: true }, { n: 9, pool: 'hard', quiz: true }],
    outro: ['b3', 'g'],
  },
  {
    id: 'campus', name: 'Søndre Campus', theme: 'campus', speed: [280, 340], gap: 1,
    intro: ['r8', 'bwave', 'k', 'f'],
    waves: [{ n: 5, pool: 'easy', quiz: true }, { n: 12, pool: 'med', shot: true }, { n: 11, pool: 'hard', quiz: true }],
    outro: ['b3', 'g'],
  },
  {
    id: 'center', name: 'Amager Centret', theme: 'center', speed: [290, 355], gap: 1,
    intro: ['r8', 'b3', 'k', 'l'],
    waves: [{ n: 4, pool: 'easy' }, { n: 13, pool: 'med', shot: true, quiz: true }, { n: 13, pool: 'hard', quiz: true }],
    outro: ['b3', 'g'],
  },
  {
    id: 'jaguaren', name: 'Jaguaren', theme: 'jaguaren', speed: [300, 370], gap: 1,
    intro: ['r8', 'b3', { hint: 'ROCKERE SLÅR MAN IKKE. HOP!' }, 'x', 'f'],
    waves: [{ n: 13, pool: 'med', quiz: true }, { n: 8, pool: 'hard', shot: true }, { n: 9, pool: 'hard', quiz: true }],
    outro: ['b3', 'g'],
  },
  {
    id: 'copenhill', name: 'CopenHill', theme: 'copenhill', speed: [310, 380], gap: 1,
    intro: ['r8', 'b3', 'k', 'f'],
    waves: [{ n: 12, pool: 'med', quiz: true }, { n: 10, pool: 'hard', shot: true }, { n: 10, pool: 'hard', quiz: true }],
    outro: ['c', 'r4', 'boss'],
  },
];

function rng(seedText) {
  let a = 0;
  for (const ch of seedText) a = (Math.imul(a ^ ch.charCodeAt(0), 2654435761) + 0x6d2b79f5) | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Banens fulde rækkefølge af klodser. Baner uden bølger bruger bare layout. */
export function expandLayout(level) {
  if (level.layout) return level.layout;
  const pools = level.swim ? SWIM_POOLS : POOLS;
  const rand = rng(level.id);
  const out = [...level.intro];
  level.waves.forEach((w, wi) => {
    if (wi > 0) out.push('c');
    if (w.hint) out.push({ hint: w.hint });
    const pool = [...pools[w.pool], ...((level.extra && level.extra[w.pool]) || [])];
    let last = null;
    for (let i = 0; i < w.n; i++) {
      if (i === Math.floor(w.n / 2)) { if (w.quiz) out.push('q'); if (w.shot) out.push('s'); }
      let pick;
      do { pick = pool[Math.floor(rand() * pool.length)]; } while (pick === last && pool.length > 1);
      out.push(pick);
      last = pick;
      if (i % 4 === 3) out.push(level.swim ? 'wb' : 'b3');
    }
  });
  return [...out, ...level.outro];
}

// Hvor lang tid (sekunder) man skal have efter en ting, før den næste må komme.
// Afstanden regnes om til kolonner ud fra banens topfart, så banerne altid kan klares,
// uanset hvor hurtigt det går. Er to ting for tæt, indsættes der tomme kolonner.
const KIND = { x: 'jump', k: 'tap', d: 'tap', f: 'tap', o: 'tap', m: 'heavy', l: 'slide' };
const NEED = { jump: 1.12, tap: 0.42, slide: 0.55, heavy: 1.0, swim: 0.75 };

function spaceOut(rows, level) {
  const v = Array.isArray(level.speed) ? level.speed[1] : level.speed;
  const ahead = GAME_W + 120 - PLAYER_SCREEN_X;   // hvor langt foran fiskeren ting dukker op
  const n = rows.lo.length;
  const cols = [];
  const map = [];
  let lastKind = null;
  let lastEff = -99;
  let walkers = 0;   // tæller d'erne, så hver får samme figur her som i buildLevel
  for (let i = 0; i < n; i++) {
    const cell = { hi: rows.hi[i], mid: rows.mid[i], lo: rows.lo[i], fl: rows.fl[i] };
    let kind = null;
    let drift = 0;   // ting, der selv bevæger sig mod fiskeren, når frem tidligere end deres kolonne
    for (const r of ['hi', 'mid', 'lo']) {
      const t = cell[r];
      if (!KIND[t]) continue;
      if (!kind || KIND[t] === 'jump') kind = KIND[t];
      const def = entityDef(t, level.theme);
      const vx = Math.abs((t === 'd' && def.variants ? def.variants[walkers++ % def.variants.length] : def).vx || 0);
      drift = Math.max(drift, (vx * (ahead / v)) / COL);
    }
    if (cell.fl === '_' && rows.fl[i - 1] !== '_') kind = 'jump';
    if (level.swim && kind) kind = 'swim';
    if (kind) {
      let eff = cols.length - drift;
      if (lastKind) {
        const need = (NEED[lastKind] * (v + 40)) / COL;
        const pad = Math.ceil(need - (eff - lastEff));
        for (let k = 0; k < pad; k++) cols.push({ hi: '.', mid: '.', lo: '.', fl: '#' });
        if (pad > 0) eff += pad;
      }
      lastKind = kind;
      lastEff = Math.max(lastEff, eff);
    }
    map[i] = cols.length;
    cols.push(cell);
  }
  map[n] = cols.length;
  const out = { hi: '', mid: '', lo: '', fl: '' };
  for (const c of cols) for (const r of ['hi', 'mid', 'lo', 'fl']) out[r] += c[r];
  return { rows: out, map };
}

/** Omsætter en banes layout til spawns, huller og hints i verdenskoordinater. */
export function buildLevel(level) {
  let rows = { hi: '', mid: '', lo: '', fl: '' };
  const hints = [];
  const push = (ch) => {
    const n = Math.max(...['hi', 'mid', 'lo', 'fl'].map((k) => (ch[k] || '').length));
    for (const k of ['hi', 'mid', 'lo']) rows[k] += (ch[k] || '').padEnd(n, '.');
    rows.fl += (ch.fl || '').padEnd(n, '#');
  };
  for (const item of expandLayout(level)) {
    if (typeof item === 'object' && item.hint) { hints.push({ col: rows.lo.length, text: item.hint }); continue; }
    const ch = typeof item === 'string' ? CHUNKS[item] : item;
    if (!ch) throw new Error(`Ukendt byggeklods "${item}" i banen ${level.id}`);
    push(ch);
    push({ lo: '.'.repeat(level.gap) });
  }
  let map = null;
  if (!level.tutorial) ({ rows, map } = spaceOut(rows, level));
  for (const h of hints) h.x = (map ? map[h.col] : h.col) * COL;
  const spawns = [];
  for (const row of ['hi', 'mid', 'lo']) {
    [...rows[row]].forEach((type, i) => { if (type !== '.') spawns.push({ type, row, x: i * COL + COL / 2 }); });
  }
  spawns.sort((a, b) => a.x - b.x);
  let walkers = 0;
  for (const s of spawns) if (s.type === 'd') s.v = walkers++;   // hvilken figur d bliver (se WALKERS i entities.js)
  const pits = [];
  let start = -1;
  [...rows.fl, '#'].forEach((c, i) => {
    if (c === '_' && start < 0) start = i;
    if (c !== '_' && start >= 0) { pits.push({ x0: start * COL, x1: i * COL }); start = -1; }
  });
  return { rows, spawns, pits, hints, width: rows.lo.length * COL };
}
