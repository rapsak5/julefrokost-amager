// Kæmpeduen: bossen på sidste bane.
// Mens kampen er i gang, står fiskeren stille på skærmen, og banen kører som et løbebånd.
// Forløb: duen svæver og sender tre små duer afsted, blinker som varsel og dykker så mod fiskeren.
// Den skal slås med pokalen midt i dykket. Fire slag, så er den færdig.

import { GAME_W, GROUND_Y, DEPTH, SCORE } from '../config.js';
import { sfx } from '../systems/audio.js';

const HOVER_Y = GROUND_Y - 190;
const SWOOP_Y = GROUND_Y - 44;

export default class Boss {
  constructor(level) {
    this.L = level;
    this.hp = 4;
    this.arena = false;      // true = løbebånd
    this.state = 'idle';
    this.timer = 0;
    this.minions = 0;
    this.lastSwingId = -1;
    this.sprite = null;
  }

  get homeX() { return this.L.cameras.main.scrollX + GAME_W - 110; }

  start() {
    this.arena = true;
    this.state = 'enter';
    this.sprite = this.L.add.sprite(this.L.cameras.main.scrollX + GAME_W + 120, HOVER_Y, 'atlas', 'boss/0').setDepth(DEPTH.boss);
    this.sprite.play('boss_fly');
    this.L.banner('KÆMPEDUEN!', 1800, 2);
    sfx('boss');
  }

  rect() {
    const s = this.sprite;
    return { x: s.x - 55, y: s.y - 26, w: 110, h: 62 };
  }

  update(now, dt) {
    const s = this.sprite;
    if (!s) return;
    const L = this.L;
    this.timer -= dt * 1000;
    switch (this.state) {
      case 'enter':
        s.x -= 240 * dt;
        s.y += (HOVER_Y - s.y) * Math.min(1, dt * 4);
        if (s.x <= this.homeX) { s.x = this.homeX; this.state = 'hover'; this.timer = 1100; }
        break;
      case 'hover':
        s.y = HOVER_Y + Math.sin(now / 260) * 8;
        if (this.timer <= 0) {
          if (this.minions < 3) {
            L.spawnMinion(this.minions % 2 === 0 ? 'd' : 'f');
            this.minions++;
            this.timer = 1050;
          } else {
            this.minions = 0;
            this.state = 'telegraph';
            this.timer = 700;
            L.banner('TAP, NÅR DEN DYKKER!', 1200);
          }
        }
        break;
      case 'telegraph':
        s.y += (SWOOP_Y - s.y) * Math.min(1, dt * 5);
        s.setTint(Math.floor(now / 90) % 2 ? 0xff6a6a : 0xffffff);
        if (this.timer <= 0) { s.clearTint(); this.state = 'swoop'; sfx('boss'); }
        break;
      case 'swoop':
        s.x -= 540 * dt;
        s.y = SWOOP_Y;
        if (s.x < L.cameras.main.scrollX - 140) {
          s.x = L.cameras.main.scrollX + GAME_W + 120;
          s.y = HOVER_Y;
          this.state = 'enter';
        }
        break;
      case 'recoil':
        s.x += 380 * dt;
        s.y += (HOVER_Y - s.y) * Math.min(1, dt * 6);
        if (this.timer <= 0) { this.state = 'enter'; }
        break;
      case 'dead':
        s.y += 260 * dt;
        s.angle += 300 * dt;
        if (this.timer <= 0) {
          s.destroy();
          this.sprite = null;
          this.arena = false;
          this.state = 'gone';
          L.onBossDefeated();
        }
        break;
      default:
    }
  }

  /** Kaldes fra banen hver frame med fiskerens kasser. */
  collide(now, hurt, swing, swingId, overlap) {
    if (!this.sprite || this.state === 'dead' || this.state === 'gone') return;
    const r = this.rect();
    if (swing && swingId !== this.lastSwingId && overlap(swing, r)) {
      this.lastSwingId = swingId;
      this.hit();
      return;
    }
    if (this.state === 'swoop' && overlap(hurt, r)) this.L.hurt();
  }

  hit() {
    const L = this.L;
    this.hp--;
    sfx('hit');
    L.burst(this.sprite.x, this.sprite.y, 'fx/feather', 14);
    L.cameras.main.shake(140, 0.008);
    this.sprite.clearTint();
    if (this.hp <= 0) {
      this.state = 'dead';
      this.timer = 1100;
      L.addScore(SCORE.boss, this.sprite.x, this.sprite.y - 40);
      L.banner('KÆMPEDUEN ER NEDE!', 1800, 2);
      sfx('win');
    } else {
      this.state = 'recoil';
      this.timer = 550;
      L.addScore(SCORE.bossHit, this.sprite.x, this.sprite.y - 40);
    }
  }
}
