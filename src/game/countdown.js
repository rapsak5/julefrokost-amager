// Nedtællingen til julefrokosten. Bruges på forsiden og på hemmeligheds-skærmen.

import { EVENT_TIME_UTC } from '../config.js';
import { txt, C } from './ui.js';

export function secondsLeft(now = Date.now()) {
  return Math.max(0, Math.floor((EVENT_TIME_UTC - now) / 1000));
}

export function parts(s) {
  return [Math.floor(s / 86400), Math.floor((s % 86400) / 3600), Math.floor((s % 3600) / 60), s % 60];
}

/** Fire bokse (dage, timer, min, sek) centreret om cx. Returnerer en funktion, der opdaterer dem. */
export function countdownBoxes(scene, cx, cy, onZero = null) {
  const nums = ['DAGE', 'TIMER', 'MIN', 'SEK'].map((label, i) => {
    const x = cx - 82 + i * 55;
    scene.add.rectangle(x, cy, 50, 56, C.deep).setStrokeStyle(2, C.gold);
    txt(scene, x, cy + 18, label, { font: 'small', tint: C.soft });
    return txt(scene, x, cy - 8, '00', { font: 'big_o', scale: 2 });
  });
  let fired = false;
  const update = () => {
    const s = secondsLeft();
    parts(s).forEach((v, i) => nums[i].setText(String(v).padStart(2, '0')));
    if (s === 0 && !fired) { fired = true; if (onZero) onZero(); }
  };
  update();
  scene.time.addEvent({ delay: 250, loop: true, callback: update });
  return update;
}
