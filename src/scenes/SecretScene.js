// Belønningen for at gennemføre spillet: hemmeligheden og nedtællingen til julefrokosten.

import { GAME_W } from '../config.js';
import { txt, panel, button, C } from '../game/ui.js';
import { countdownBoxes } from '../game/countdown.js';
import { sfx } from '../systems/audio.js';

export default class SecretScene extends Phaser.Scene {
  constructor() { super('Secret'); }

  create() {
    this.add.rectangle(0, 0, GAME_W, 360, C.deep).setOrigin(0);
    txt(this, GAME_W / 2, 18, 'SPILLET ER GENNEMFØRT. HER ER HEMMELIGHEDEN:', { font: 'small_o', tint: C.soft });
    const big = txt(this, GAME_W / 2, 54, 'HUSK BADETØJET!', { font: 'big_o', scale: 3, tint: C.yellow });
    this.tweens.add({ targets: big, scale: { from: 0.2, to: 1 }, duration: 500, ease: 'Back.easeOut' });
    this.add.image(8, 90, 'secret').setOrigin(0);

    const x0 = 400;
    panel(this, x0, 90, 232, 216);
    txt(this, x0 + 116, 108, 'NEDTÆLLING TIL', { font: 'small_o', tint: C.soft });
    txt(this, x0 + 116, 124, 'JULEFROKOSTEN', { font: 'small_o', scale: 2, tint: C.yellow });
    const msg = txt(this, x0 + 116, 226, 'Søndag 27. december 2026\nMødetid kl. 13.00', { font: 'ui', center: true });
    countdownBoxes(this, x0 + 116, 172, () => msg.setText('Det er nu. Afsted,\nog husk badetøjet.'));
    button(this, x0 + 116, 276, 190, 32, 'TOPSCORERLISTEN', () => this.scene.start('Scores'));
    this.input.keyboard?.once('keydown-ENTER', () => this.scene.start('Scores'));
    sfx('win');
  }
}
