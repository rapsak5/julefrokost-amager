// Titelskærmen.

import { GAME_W, GAME_H, GROUND_Y, VERSION } from '../config.js';
import { DEFAULT_FISHER } from '../data/fishers.js';
import { txt, panel, C } from '../game/ui.js';
import { countdownBoxes } from '../game/countdown.js';
import * as Scores from '../systems/scores.js';
import * as Save from '../systems/save.js';
import { unlock, sfx } from '../systems/audio.js';

export default class TitleScene extends Phaser.Scene {
  constructor() { super('Title'); }

  create() {
    const t = 'dragoer';
    this.add.image(0, 0, `${t}_sky`).setOrigin(0);
    this.far = this.add.tileSprite(0, 0, GAME_W, GAME_H, `${t}_far`).setOrigin(0);
    this.mid = this.add.tileSprite(0, 0, GAME_W, GAME_H, `${t}_mid`).setOrigin(0);
    this.ground = this.add.tileSprite(0, GROUND_Y, GAME_W, GAME_H - GROUND_Y, `${t}_ground`).setOrigin(0);
    this.snow = this.add.tileSprite(0, 0, GAME_W, GAME_H, 'snow').setOrigin(0).setAlpha(0.8);

    const id = Save.load().fisher || DEFAULT_FISHER;
    this.add.sprite(150, GROUND_Y, 'atlas', `fisher/${id}/run0`).setOrigin(0.375, 1).play(`${id}_run`);
    this.add.sprite(540, GROUND_Y, 'atlas', 'enemy/cat0').setOrigin(0.5, 1).play('cat_walk');
    this.add.sprite(520, GROUND_Y - 150, 'atlas', 'enemy/gull0').play('gull_fly');

    txt(this, GAME_W / 2, 20, 'Gutterne præsenterer', { font: 'ui_o' });
    txt(this, GAME_W / 2, 56, 'JULEFROKOST', { font: 'big_o', scale: 3 });
    txt(this, GAME_W / 2, 102, 'PÅ AMAGER', { font: 'big_o', scale: 3, tint: C.yellow });

    // nedtællingen til julefrokosten. Samtidig lukker highscoren.
    panel(this, GAME_W / 2 - 126, 132, 252, 128, { alpha: 0.92 });
    const head = txt(this, GAME_W / 2, 148, 'NEDTÆLLING TIL JULEFROKOSTEN', { font: 'small_o', tint: C.yellow });
    const foot = txt(this, GAME_W / 2, 244, 'HIGHSCOREN LUKKER SØNDAG 27/12 KL. 13.00', { font: 'small', tint: C.soft });
    const closed = () => {
      head.setText('JULEFROKOSTEN ER I GANG');
      foot.setText('HIGHSCOREN ER LUKKET').setTint(C.yellow);
      if (Scores.isShared()) {
        Scores.fetchBoard().then((b) => {
          const top = b && b.rows[0];
          if (top && top.score > 0 && this.sys.isActive()) foot.setText(`HIGHSCOREN ER LUKKET. VINDER: ${top.name.toUpperCase()}`);
        });
      }
    };
    countdownBoxes(this, GAME_W / 2, 196, closed);
    if (Scores.isClosed()) closed();

    this.add.rectangle(GAME_W / 2, 277, 200, 24, C.night, 0.8);
    const start = txt(this, GAME_W / 2, 276, 'TRYK FOR AT SPILLE', { font: 'ui' });
    this.tweens.add({ targets: start, alpha: 0.2, duration: 600, yoyo: true, repeat: -1 });
    txt(this, GAME_W - 6, GAME_H - 6, `v${VERSION} pladsholdergrafik`, { font: 'small_o', ox: 1, oy: 1 });

    const go = () => {
      unlock();
      sfx('click');
      // På Android kan spillet gå i fuldskærm og låse til bredformat. iPhone understøtter det ikke i Safari.
      const dev = this.sys.game.device;
      if (!dev.os.desktop && this.scale.fullscreen.available && !this.scale.isFullscreen) {
        try {
          this.scale.startFullscreen();
          window.screen.orientation?.lock?.('landscape').catch(() => {});
        } catch (e) { /* ikke muligt her */ }
      }
      this.scene.start('Select');
    };
    this.input.once('pointerup', go);
    this.input.keyboard?.once('keydown', go);
  }

  update(time) {
    const scroll = time * 0.05;
    this.far.tilePositionX = Math.floor(scroll * 0.15);
    this.mid.tilePositionX = Math.floor(scroll * 0.45);
    this.ground.tilePositionX = Math.floor(scroll);
    this.snow.tilePositionX = Math.floor(scroll * 0.7);
    this.snow.tilePositionY = -Math.floor(time * 0.03);
  }
}
