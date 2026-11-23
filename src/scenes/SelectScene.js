// Første skærm efter titlen: vælg din fisker. Navnet følger med på topscorerlisten.

import { GAME_W, GAME_H } from '../config.js';
import { FISHERS, DEFAULT_FISHER } from '../data/fishers.js';
import { txt, panel, button, C } from '../game/ui.js';
import * as Save from '../systems/save.js';
import { sfx } from '../systems/audio.js';

export default class SelectScene extends Phaser.Scene {
  constructor() { super('Select'); }

  create() {
    this.add.rectangle(0, 0, GAME_W, GAME_H, C.deep).setOrigin(0);
    txt(this, GAME_W / 2, 34, 'VÆLG DIN FISKER', { font: 'big_o', scale: 2, tint: C.yellow });

    const saved = Save.load().fisher || DEFAULT_FISHER;
    this.index = Math.max(0, FISHERS.findIndex((f) => f.id === saved));
    this.frame = this.add.graphics();
    this.cells = FISHERS.map((f, i) => {
      const x = 59 + i * 87;
      this.add.image(x, 100, 'atlas', `portrait/${f.id}`);
      const name = txt(this, x, 140, f.name, { font: 'ui' });
      this.add.zone(x, 108, 84, 96).setInteractive({ useHandCursor: true }).on('pointerup', () => {
        if (this.index === i) this.confirm();
        else { sfx('click'); this.select(i); }
      });
      return { x, name };
    });

    panel(this, 110, 170, GAME_W - 220, 170);
    this.preview = this.add.sprite(210, 322, 'atlas', `fisher/${saved}/run0`).setOrigin(0.375, 1);
    this.nameTxt = txt(this, 290, 222, '', { font: 'big_o', scale: 2, ox: 0 });
    button(this, 390, 296, 200, 34, 'VÆLG', () => this.confirm());

    this.select(this.index);
    const kb = this.input.keyboard;
    kb?.on('keydown-LEFT', () => this.select((this.index + FISHERS.length - 1) % FISHERS.length));
    kb?.on('keydown-RIGHT', () => this.select((this.index + 1) % FISHERS.length));
    kb?.on('keydown-ENTER', () => this.confirm());
  }

  select(i) {
    this.index = i;
    const f = FISHERS[i];
    const c = this.cells[i];
    this.cells.forEach((cell, k) => cell.name.setTint(k === i ? C.yellow : 0xffffff));
    this.frame.clear().lineStyle(2, C.yellow, 1).strokeRect(c.x - 30, 68, 60, 64);
    this.preview.play(`${f.id}_run`);
    this.nameTxt.setText(f.name.toUpperCase());
  }

  confirm() {
    Save.setFisher(FISHERS[this.index].id);
    sfx('flag');
    // første gang går turen gennem øvebanen
    if (Save.load().tutorialDone) this.scene.start('Map');
    else this.scene.start('Level', { tutorial: true });
  }
}
