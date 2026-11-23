// Topscorerlisten med alle syv fiskere. Viser telefonens egne point med det samme
// og skifter til den fælles liste, når den er hentet.

import { GAME_W, GAME_H } from '../config.js';
import { LEVELS } from '../data/levels.js';
import { txt, button, pad, C } from '../game/ui.js';
import * as Save from '../systems/save.js';
import * as Scores from '../systems/scores.js';

export default class ScoresScene extends Phaser.Scene {
  constructor() { super('Scores'); }

  create() {
    this.add.rectangle(0, 0, GAME_W, GAME_H, C.navy).setOrigin(0);
    txt(this, GAME_W / 2, 26, 'TOPSCORERLISTEN', { font: 'big_o', scale: 2, tint: C.yellow });
    const head = (x, s, ox = 0) => txt(this, x, 56, s, { font: 'small', ox, tint: C.yellow });
    head(96, 'PLADS'); head(180, 'FISKER'); head(400, 'POINT', 1); head(430, 'NÅET TIL');
    this.rowObjs = [];
    this.status = txt(this, GAME_W / 2, 304, '', { font: 'small', tint: C.soft });
    this.draw(Scores.localBoard());
    if (Scores.isShared()) {
      this.status.setText('HENTER DEN FÆLLES LISTE ...');
      Scores.fetchBoard().then((b) => {
        if (!this.sys.isActive()) return;
        if (b) { this.draw(b.rows); this.setStatus(true); } else this.status.setText('KUNNE IKKE HENTE DEN FÆLLES LISTE. VISER DENNE TELEFON');
      });
    } else this.setStatus(false);
    button(this, GAME_W / 2 - 90, 334, 160, 30, 'KORTET', () => this.scene.start('Map'));
    button(this, GAME_W / 2 + 90, 334, 160, 30, 'FORSIDEN', () => this.scene.start('Title'), { color: C.panel });
    this.input.keyboard?.once('keydown-ENTER', () => this.scene.start('Map'));
  }

  setStatus(shared) {
    if (Scores.isClosed()) this.status.setText('HIGHSCOREN LUKKEDE SØNDAG 27/12 KL. 13.00').setTint(C.yellow);
    else this.status.setText(shared ? 'FÆLLES LISTE. LUKKER SØNDAG 27/12 KL. 13.00' : 'LISTEN GEMMES KUN PÅ DENNE TELEFON');
  }

  draw(list) {
    this.rowObjs.forEach((o) => o.destroy());
    this.rowObjs = [];
    const me = Save.load().fisher;
    const keep = (o) => { this.rowObjs.push(o); return o; };
    list.forEach((r, i) => {
      const y = 82 + i * 31;
      if (r.id === me) keep(this.add.rectangle(GAME_W / 2, y, 470, 29, C.panel));
      keep(txt(this, 104, y, String(i + 1), { font: 'ui', ox: 0 }));
      keep(this.add.image(152, y, 'atlas', `portrait/${r.id}`).setScale(0.5));
      keep(txt(this, 180, y, r.name, { font: 'ui', ox: 0, tint: i === 0 && r.score > 0 ? C.yellow : 0xffffff }));
      keep(txt(this, 400, y, pad(r.score), { font: 'ui', ox: 1 }));
      const reached = r.reached === 0 ? 'Ikke startet' : r.reached >= LEVELS.length ? 'Byen' : LEVELS[r.reached - 1].name;
      keep(txt(this, 430, y, reached, { font: 'ui', ox: 0, tint: C.soft }));
    });
  }
}
