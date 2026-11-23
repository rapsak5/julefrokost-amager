#!/usr/bin/env python3
"""Bygger al grafik til spillet: atlas, baggrunde, kort og bitmapfonte.

Kør:  python3 tools/build_assets.py

Alt er PLADSHOLDERGRAFIK tegnet i halv opløsning (320x180) og skaleret 2x til
spillets 640x360. Når grafikken tegnes om i fuld opløsning, sættes ART = 1 og
koordinaterne i tegnefunktionerne fordobles. Framenavnene i atlasset er
kontrakten med spilkoden (se src/data/assets.js). Behold dem.
"""
import os, sys, json, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pixlib
from pixlib import *
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'assets')
ART = 2            # skalering fra tegneopløsning til spilopløsning
BASE_Y = 150       # jordlinje i tegneopløsning (300 i spillet)
os.makedirs(os.path.join(OUT, 'bg'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'fonts'), exist_ok=True)


class TCan(Can):
    """Gennemsigtigt lærred. wrap=True får tegningen til at gå op i sømmen (tile)."""
    def __init__(s, w, h, wrap=False, bg=None):
        super().__init__(w, h, bg or '#000000')
        if not bg:
            s.im.putalpha(0); s.px = s.im.load()
        s.wrap = wrap
    def set(s, x, y, c):
        if s.wrap: x %= s.w
        if 0 <= x < s.w and 0 <= y < s.h:
            s.px[x, y] = hexc(c) if isinstance(c, str) else c
    def up(s, k=ART):
        return s.im.resize((s.w * k, s.h * k), Image.NEAREST)
    def outlined(s, col='#1a1420'):
        """Returnerer en kopi med 1 px mørk kant rundt om alt, der er tegnet."""
        o = TCan(s.w + 2, s.h + 2); oc = hexc(col)
        for y in range(s.h):
            for x in range(s.w):
                if s.px[x, y][3]:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if not (0 <= x + dx < s.w and 0 <= y + dy < s.h) or not s.px[x + dx, y + dy][3]:
                            o.px[x + 1 + dx, y + 1 + dy] = oc
        for y in range(s.h):
            for x in range(s.w):
                if s.px[x, y][3]: o.px[x + 1, y + 1] = s.px[x, y]
        return o


def norm(rows):
    w = max(len(r) for r in rows)
    return [r.ljust(w, '.') for r in rows]


def rot_ccw(rows):
    h = len(rows); w = len(rows[0])
    return [''.join(rows[i][w - 1 - j] for i in range(h)) for j in range(w)]


# =====================================================================
# Atlas
# =====================================================================
ATLAS = []   # (navn, PIL-billede)

def add(name, can_or_im):
    im = can_or_im.up() if isinstance(can_or_im, Can) else can_or_im
    ATLAS.append((name, im))

def rows_frame(rows, pal, pad=0):
    o = outline(rows)
    c = TCan(len(o[0]) + pad * 2, len(o) + pad * 2)
    c.sprite(rows, pad, pad, pal)
    return c

def pack_atlas(path_png, path_json, width=1024, pad=2):
    items = sorted(ATLAS, key=lambda t: -t[1].height)
    x = y = pad; shelf = 0; pos = {}
    for name, im in items:
        if x + im.width + pad > width:
            x = pad; y += shelf + pad; shelf = 0
        pos[name] = (x, y); x += im.width + pad; shelf = max(shelf, im.height)
    height = y + shelf + pad
    sheet = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    frames = {}
    for name, im in items:
        px, py = pos[name]; sheet.paste(im, (px, py))
        frames[name] = {'frame': {'x': px, 'y': py, 'w': im.width, 'h': im.height}, 'rotated': False, 'trimmed': False,
                        'spriteSourceSize': {'x': 0, 'y': 0, 'w': im.width, 'h': im.height},
                        'sourceSize': {'w': im.width, 'h': im.height}}
    sheet.save(path_png)
    json.dump({'frames': frames, 'meta': {'image': os.path.basename(path_png), 'size': {'w': width, 'h': height}, 'scale': '1'}},
              open(path_json, 'w'), indent=0)
    print('atlas', sheet.size, len(frames), 'frames')


# =====================================================================
# Fiskerne
# =====================================================================
#  id, skæg, bryn, sydvest/regntøj, hud, briller, pibe, kun overskæg
FISHERS = [
    ('andreas', '#6a4428', '#4a2e18', '#f2c418', '#f0b48c', False, False, False),
    ('anders',  '#c8642a', '#a84a1a', '#e8862a', '#f2bc96', False, True,  False),
    ('mark',    '#2a2224', '#1a1416', '#f2c418', '#d89a70', True,  False, False),
    ('claus',   '#9aa0a8', '#7a8088', '#3a8ad8', '#f0b48c', True,  True,  False),
    ('theis',   '#e8c860', '#c8a840', '#f2c418', '#f4c4a0', False, False, True),
    ('kenni',   '#b8502a', '#8a3a1a', '#d83a3a', '#f0b48c', False, False, True),
    ('kasper',  '#f4f1ea', '#f4f1ea', '#f2c418', '#f0b48c', False, True,  False),
]
BODY0 = list(pixlib.BODY)
CELL_W, CELL_H = 64, 48      # fast celle pr. fiskerframe (tegneopløsning)

def body_variant(must, pipe):
    rows = [list(r) for r in BODY0]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == 'P' and not pipe: r[i] = '.'
            if ch == 'W' and must:
                if j in (8, 9): r[i] = 'S'
                elif j >= 10: r[i] = 'Y'
    return [''.join(r) for r in rows]

def fisher_frames(fid, beard, brow, coat, skin, glasses, pipe, must):
    pal = dict(P); pal.update(W=beard, Y=coat, y=shade(coat), S=skin)
    pixlib.BODY = body_variant(must, pipe)
    T = trophy()
    def cell(rows, ox, oy):
        c = TCan(CELL_W, CELL_H); c.sprite(rows, ox, oy, pal); return c
    run0 = fisher_big('run'); run1 = fisher_big('idle')
    # hop: samme som løb, men med samlede ben
    g = [list(r) for r in run0]
    for j, legs in enumerate(LEGS_JUMP):
        for i in range(16): g[40 + j][2 + i] = legs[i]
    jump = [''.join(r) for r in g]
    swing = fisher_big('swing')
    # slide: kroppen ligger ned med fødderne forrest og pokalen slæbt bagefter
    b = blank(16, 20); paste(b, pixlib.BODY, 0, 0); paste(b, LEGS_STEP, 0, 17)
    lying = rot_ccw(tostr(b)); tl = rot_ccw(T)
    s = blank(len(tl[0]) + len(lying[0]), 21)
    paste(s, tl, 0, 0); paste(s, lying, len(tl[0]), 21 - len(lying))
    slide = tostr(s)
    add(f'fisher/{fid}/run0', cell(run0, 13, 2))
    add(f'fisher/{fid}/run1', cell(run1, 13, 2))
    add(f'fisher/{fid}/jump', cell(jump, 13, 0))
    add(f'fisher/{fid}/swing', cell(swing, 15, 16))
    add(f'fisher/{fid}/slide', cell(slide, 2, CELL_H - 23))
    # svømning (Den Blå Planet): kroppen vandret med hovedet forrest og pokalen som stødspyd
    tr = pixlib.rot_cw(T)
    for name, legs, push in (('swim0', LEGS_RUN, 0), ('swim1', LEGS_STEP, 0), ('swimhit', LEGS_RUN, 4)):
        b2 = blank(16, 20); paste(b2, pixlib.BODY, 0, 0); paste(b2, legs, 0, 17)
        lying2 = pixlib.rot_cw(tostr(b2))
        w = blank(len(lying2[0]) + len(tr[0]) + push, 20)
        paste(w, lying2, 0, 2); paste(w, tr, len(lying2[0]) + push, 0)
        add(f'fisher/{fid}/{name}', cell(tostr(w), 4, 25))
    pixlib.BODY = BODY0

FACE2 = [
"....YYYYYYYY....", "...YYYYYYYYYY...", "...YYYYYYYYYY...", ".yyyyyyyyyyyyyy.", "..HSSSSSSSSSSH..", "..SEEESSSSEEES..",
"..SSBKSSSSBKSS..", "..SSSSSRRSSSSS..", "..sSSSSRRSSSSs..", "..WWWWWWWWWWWW..", ".WWWWWMMMWWWWPP.", ".WWWWWWWWWWWWPPP",
"..WWWWWWWWWWWPP.", "...WWWWWWWWWW...",
]
PORTRAIT_BG = ['#6ab0e8', '#8ad0a0', '#e8a0a0', '#b0a0e8', '#f0c890', '#90d0e0', '#6ab0e8']

def portrait_rows(beard, brow, coat, skin, glasses, pipe, must):
    pal = dict(FACE_P); pal.update(W=beard, E=brow, Y=coat, y=shade(coat), S=skin, s=shade(skin, .85), H=brow, G='#1a1420')
    rows = [list(r) for r in FACE2]
    if not pipe:
        for r in rows:
            for i, ch in enumerate(r):
                if ch == 'P': r[i] = '.'
    if must:
        rows[10] = list('.WWWWWMMMWWWWPP.' if pipe else '.WWWWWMMMWWWWW..')
        rows[11] = list('..SSSSSSSSSSSS..'); rows[12] = list('...SSSSSSSSSS...'); rows[13] = list('....SSSSSSSS....')
    if glasses:
        for (a, b) in ((3, 6), (9, 12)):
            for i in range(a, b + 1): rows[5][i] = 'G'; rows[7][i] = 'G'
        rows[6][2] = rows[6][13] = rows[6][7] = rows[6][8] = 'G'
    return [''.join(r) for r in rows], pal

def portrait(k, fid, beard, brow, coat, skin, glasses, pipe, must):
    c = TCan(26, 28)
    c.rect(0, 0, 26, 28, '#7a4a18'); c.rect(1, 1, 24, 26, '#e8b040'); c.rect(2, 2, 22, 24, '#a8701e'); c.rect(1, 1, 24, 1, '#ffe08a')
    c.rect(3, 3, 20, 22, PORTRAIT_BG[k])
    rows, pal = portrait_rows(beard, brow, coat, skin, glasses, pipe, must)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.' and ch in pal: c.set(5 + i, 6 + j, pal[ch])
    c.rect(5, 20, 16, 5, coat); c.rect(5, 20, 16, 1, shade(coat))
    add(f'portrait/{fid}', c)

def build_fishers():
    for k, f in enumerate(FISHERS):
        fisher_frames(*f); portrait(k, *f)


# =====================================================================
# Fjender, ting og effekter
# =====================================================================
DUE_W2 = DUE[:-1] + ['....o....o..']
DUE_FLY2 = ['............', '............', '.aa.........', 'aAAaaaaaa...', 'oAeAAAAAAaa.', '.anmAAAAAAAa', '..aaAAAaaaa.', '....aAAa....', '.....aa.....']
CROWN = ['y.y.y', 'yyyyy', 'yyyyy']

def boss_frame(rows):
    big = scaled(rows, 6)
    c = TCan(len(big[0]) + 4, len(big) + 16)
    c.sprite(big, 1, 13, DUE_P)
    c.sprite(scaled(CROWN, 3), 4, 0, dict(K='#1a1420', y='#f6c945'))
    return c

def lowbar():
    c = TCan(44, 130)
    for x in (6, 37):
        for y in range(0, 116): c.set(x, y, '#3a3a44' if y % 3 else '#8a8e9a')
    c.rect(0, 114, 44, 16, '#1a1420'); c.rect(1, 115, 42, 14, '#f2c418')
    for i in range(-16, 44, 8):
        for j in range(14):
            for t in range(4): c.set(i + j + t, 115 + j, '#1a1420') if 1 <= i + j + t <= 42 else None
    c.rect(8, 118, 28, 8, '#f6f2e8'); c.text('PAS PÅ', 11, 120, '#c0302a')
    return c

def flag(up):
    c = TCan(22, 46)
    c.rect(2, 2, 2, 44, '#5a3a2a'); c.rect(1, 0, 4, 3, '#f6c945'); c.rect(0, 44, 6, 2, '#3a2418')
    y = 4 if up else 28; col = '#3ad46a' if up else '#8a8e9a'
    c.rect(4, y, 14, 9, col); c.rect(4, y, 14, 1, light(col)); c.rect(16, y + 2, 4, 5, col)
    c.rect(3, y - 1, 16, 1, '#1a1420'); c.rect(3, y + 9, 16, 1, '#1a1420')
    return c

def goal():
    c = TCan(34, 50)
    c.rect(15, 14, 3, 36, '#5a3a2a'); c.rect(12, 48, 9, 2, '#3a2418')
    c.rect(0, 0, 34, 16, '#1a1420')
    for j in range(2):
        for i in range(4):
            c.rect(1 + i * 8, 1 + j * 7, 8, 7, '#f6f2e8' if (i + j) % 2 else '#1a1420')
    c.rect(6, 4, 22, 8, '#c0302a'); c.text('MÅL', 11, 6, '#ffffff')
    return c

def crate():
    c = TCan(18, 14)
    c.rect(0, 0, 18, 14, '#1a1420'); c.rect(1, 1, 16, 12, '#3a7ad8'); c.rect(1, 1, 16, 2, '#6aa0f0'); c.rect(1, 11, 16, 2, '#2a5aa8')
    c.rect(4, 5, 8, 3, '#c8d4e0'); c.rect(12, 4, 2, 5, '#c8d4e0'); c.set(5, 6, '#1a1420')
    return c

def books():
    c = TCan(20, 16)
    for k, (col, w, x) in enumerate([('#a83a2a', 18, 1), ('#3a6a8a', 16, 2), ('#c8a040', 18, 1)]):
        y = 11 - k * 5
        c.rect(x - 1, y - 1, w + 2, 6, '#1a1420'); c.rect(x, y, w, 4, col); c.rect(x + w - 3, y, 2, 4, '#f6f0e0'); c.rect(x, y, w, 1, light(col))
    return c

GOOSE = norm([
"..WW", ".oWeW", "..WW", "..WW", "..WW", "..WWW.WWWWW", "..WWWWWWWWWWW", "..WWWWWgggWWWW", "...WWWWWWWWWW", "....WWWWWWW",
".....o...o", ".....o...o", "....oo..oo"])
GOOSE2 = norm(GOOSE[:10] + ["....o.....o", "...o.......o", "..oo......oo"])
GOOSE_P = dict(K='#1a1420', W='#eef0f4', g='#a8b0bc', o='#e8862a', e='#1a1420')
COW = norm([
".h....h", ".WWWWWW", "WWWWKWWW", "WeWWWWWWWKKKWWWWWWKKKWWW", "WWWWWWWWKKKKWWWWWWKKKKWWW", "pppWWWWWWKKKWWWWWWWKKKWWWt",
"ppp.WWWWWWWWWWWKKWWWWWWWWt", "....WWWWWWWWWWKKKKWWWWWW.t", "....WWWWKKWWWWWKKWWWWWWW", "....WWWKKKKWWWWWWWWWWWWW",
".....WWWWWWWWWWWuuuWWWW", ".....WW.WW......uu.WW.WW", ".....WW.WW.........WW.WW", ".....WW.WW.........WW.WW", ".....KK.KK.........KK.KK"])
COW_P = dict(K='#1a1420', W='#f4f1ea', p='#e89aa0', u='#e89aa0', t='#1a1420', e='#1a1420', h='#d8c8a0')

def dozer(frame):
    c = TCan(42, 28)
    c.rect(10, 19, 30, 8, '#2a2a34'); c.rect(11, 20, 28, 6, '#3a3a44')
    for k in range(5): c.rect(12 + k * 6 + frame * 3 % 6, 21, 3, 4, '#6a6e7a')
    c.rect(12, 10, 26, 10, '#f2b418'); c.rect(12, 10, 26, 2, '#ffd65a'); c.rect(12, 18, 26, 2, '#b8860c')
    c.rect(24, 1, 13, 10, '#f2b418'); c.rect(24, 1, 13, 1, '#ffd65a'); c.rect(26, 3, 9, 6, '#9ac8ea')
    c.rect(27, 6, 2, 2, '#1a1420'); c.rect(31, 6, 2, 2, '#1a1420')          # onde øjne
    c.set(27, 4, '#1a1420'); c.set(28, 5, '#1a1420'); c.set(33, 4, '#1a1420'); c.set(32, 5, '#1a1420')
    c.rect(16, 3, 2, 7, '#3a3a44'); puff(c, 17, 1 - frame, 2, '#8a8e9a', '#6a6e7a')
    c.rect(6, 15, 8, 3, '#8a6a10'); c.rect(1, 6, 5, 21, '#c8ccd4'); c.rect(1, 6, 2, 21, '#e8ecf0'); c.rect(0, 25, 7, 2, '#8a8e9a')
    for i in range(14, 36, 6):
        for t in range(3): c.set(i + t, 14 + t, '#1a1420')
    return c.outlined()

# ---------- v0.2: droner, bolde, DR-udstyr og rockere ----------
def circle(c, cx, cy, r, col):
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            if i * i + j * j <= r * r + 1: c.set(cx + i, cy + j, col)

def drone(frame):
    c = TCan(26, 12)
    for x in (1, 17):
        if frame == 0: c.rect(x, 1, 8, 1, '#c8ccd4')
        else: c.rect(x + 2, 1, 4, 1, '#e8ecf0')
        c.rect(x + 3, 2, 2, 2, '#3a3a44')
    c.rect(3, 4, 20, 2, '#3a3a44')
    c.rect(8, 3, 10, 6, '#5a5e6a'); c.rect(8, 3, 10, 1, '#8a8e9a')
    c.rect(10, 9, 6, 2, '#2a2a34'); c.set(11, 10, '#6ab0e8')
    c.set(9, 5, '#ff3030'); c.set(16, 5, '#30ff60')
    c.rect(6, 9, 1, 3, '#3a3a44'); c.rect(19, 9, 1, 3, '#3a3a44')
    return c.outlined()

def ball():
    c = TCan(13, 13); circle(c, 6, 6, 6, '#f4f7fb')
    for (x, y, w, h) in ((5, 5, 3, 3), (1, 3, 2, 2), (10, 3, 2, 2), (2, 9, 2, 2), (9, 9, 2, 2), (6, 0, 2, 1), (6, 11, 2, 2)): c.rect(x, y, w, h, '#1a1420')
    c.set(3, 2, '#ffffff'); c.rect(8, 10, 3, 1, '#c8d0dc')
    return c.outlined()

def hurdle():
    c = TCan(24, 18)
    for x in (2, 20): c.rect(x, 4, 2, 13, '#e8ecf0'); c.rect(x - 2, 16, 6, 2, '#8a8e9a')
    c.rect(0, 0, 24, 5, '#f4f7fb')
    for x in range(0, 24, 8): c.rect(x, 0, 4, 5, '#d02030')
    return c.outlined()

def cone():
    c = TCan(12, 13)
    for j in range(11): c.rect(5 - j // 3, j, 2 + 2 * (j // 3), 1, '#f07820' if j not in (4, 5) else '#f4f7fb')
    c.rect(0, 11, 12, 2, '#c85a10')
    return c.outlined()

def tv_camera():
    c = TCan(20, 26)
    for t in range(14):
        c.set(10 - t * 8 // 13, 12 + t, '#8a8e9a'); c.set(10 + t * 8 // 13, 12 + t, '#8a8e9a'); c.set(10, 12 + t, '#6a6e7a')
    c.rect(8, 10, 5, 3, '#3a3a44')
    c.rect(4, 2, 14, 9, '#3a3e4a'); c.rect(4, 2, 14, 1, '#6a6e7a'); c.rect(14, 0, 4, 3, '#2a2a34')
    c.rect(0, 4, 5, 5, '#1a1420'); c.rect(1, 5, 2, 3, '#6ab0e8'); c.set(7, 4, '#ff3030'); c.rect(9, 6, 6, 3, '#f4f7fb')
    return c.outlined()

def cables():
    c = TCan(36, 7)
    for k, col in enumerate(('#1a1420', '#d02030', '#f2c418', '#2a6ad8')):
        for x in range(36):
            c.set(x, 3 + k % 2 + round(1.6 * math.sin(x / 3.0 + k * 1.7)), col)
    c.rect(0, 3, 3, 4, '#3a3a44'); c.rect(33, 3, 3, 4, '#3a3a44')
    return c.outlined()

def boom_mic():
    c = TCan(44, 130)
    c.rect(21, 0, 2, 114, '#3a3a44'); c.rect(21, 0, 1, 114, '#6a6e7a')
    r = random.Random(4)
    for j in range(16):
        hw = int(17 * math.sqrt(max(0, 1 - ((j - 7.5) / 8.0) ** 2)))
        for i in range(-hw, hw + 1): c.set(22 + i, 114 + j, r.choice(['#8a8e9a', '#6a6e7a', '#a8acb8', '#7a7e8a']))
    return c

def dolly(frame):
    c = TCan(34, 28)
    c.rect(2, 20, 30, 4, '#5a5e6a'); c.rect(2, 20, 30, 1, '#8a8e9a')
    for x in (5, 25): circle(c, x + 1, 25, 2, '#1a1420'); c.set(x + 1 + (frame or -1), 25, '#8a8e9a')
    c.rect(15, 10, 4, 10, '#3a3a44')
    c.rect(8, 2, 18, 9, '#3a3e4a'); c.rect(8, 2, 18, 1, '#6a6e7a'); c.rect(22, 0, 4, 3, '#2a2a34')
    c.rect(3, 4, 6, 5, '#1a1420'); c.rect(4, 5, 2, 3, '#6ab0e8'); c.set(11, 4, '#ff3030'); c.rect(13, 6, 8, 3, '#f4f7fb')
    return c.outlined()

def spotlight():
    c = TCan(14, 16)
    c.rect(6, 10, 2, 5, '#6a6e7a'); c.rect(3, 14, 8, 2, '#3a3a44')
    c.rect(3, 2, 9, 8, '#2a2a34'); c.rect(3, 2, 9, 1, '#5a5e6a'); c.rect(1, 3, 2, 6, '#fff2a0'); c.rect(0, 4, 1, 4, '#ffffff')
    return c.outlined()

ROCKER = norm([
"....HHHHH", "...HHHHHHH", "...SSSSSSS", "...GGGGGGS", "...SSSSSSS", "...BBBBBBB", "....BBBBB",
"..VVVVVVVVV", ".SVVVPPVVVVS", ".SVVVPPVVVVS", ".SSVVVVVVVSS", "..VSSSSSSSV", "..VVVVVVVVV", "...VVVVVVV",
"...DDDDDDD", "...DDD.DDD", "...DDD.DDD", "...DDD.DDD", "..bbbb.bbbb"])
ROCKER2 = norm(ROCKER[:15] + ["...DDD.DDD", "..DDD...DDD", "..DDD...DDD", ".bbbb...bbbb"])
ROCKER_P = dict(K='#0e0c12', H='#b02020', S='#e0a080', G='#0e0c12', B='#5a3a20', V='#26262e', P='#f2c418', D='#3a5a8a', b='#16141a')

def bar_stool():
    c = TCan(12, 16)
    c.rect(1, 0, 10, 3, '#8a2a2a'); c.rect(1, 0, 10, 1, '#b84a4a'); c.rect(5, 3, 2, 11, '#8a8e9a'); c.rect(3, 9, 6, 1, '#8a8e9a'); c.rect(2, 14, 8, 2, '#6a6e7a')
    return c.outlined()

def barrel():
    c = TCan(15, 15); circle(c, 7, 7, 7, '#8a5a2a'); circle(c, 7, 7, 5, '#a8703a')
    c.rect(1, 4, 13, 1, '#3a3a44'); c.rect(1, 10, 13, 1, '#3a3a44'); c.rect(6, 6, 3, 3, '#5a3a1a')
    return c.outlined()

def bar_lamp():
    c = TCan(44, 130)
    c.rect(21, 0, 1, 114, '#1a1420')
    for j in range(10): c.rect(22 - 8 - j, 114 + j, 16 + 2 * j, 1, '#2f7a3a' if j else '#4f9a5a')
    c.rect(4, 124, 36, 2, '#1a1420'); c.rect(10, 126, 24, 4, '#fff2a0')
    return c

def shark(frame):
    c = TCan(46, 22); d = ImageDraw.Draw(c.im)
    body, belly, dark = (106, 126, 150, 255), (232, 238, 244, 255), (74, 92, 116, 255)
    d.polygon([(0, 11), (8, 6), (22, 4), (36, 8), (36, 14), (22, 18), (8, 16)], fill=body)
    d.polygon([(2, 12), (10, 16), (24, 18), (34, 14), (20, 14), (8, 13)], fill=belly)
    d.polygon([(18, 4), (25, 0), (27, 5)], fill=dark)                       # rygfinne
    d.polygon([(18, 16), (22, 21), (25, 16)], fill=dark)                    # brystfinne
    ty = 2 if frame else 0
    d.polygon([(35, 10), (45, 1 + ty), (41, 11), (45, 19 - ty)], fill=body)  # hale
    c.px = c.im.load()
    c.rect(7, 8, 2, 2, '#1a1420'); c.set(7, 8, '#ffffff')
    for x in range(2, 9, 2): c.set(x, 13, '#ffffff'); c.set(x + 1, 12, '#c0302a')
    for x in (13, 15, 17): c.rect(x, 9, 1, 4, '#4a5c74')                    # gæller
    return c.outlined()

def jelly(frame):
    c = TCan(14, 20)
    for j in range(8):
        hw = int(6.5 * math.sqrt(max(0, 1 - ((j - 7) / 8.0) ** 2)))
        c.rect(7 - hw, j, 2 * hw, 1, '#f08ac0' if j > 1 else '#ffc0e0')
    c.rect(3, 2, 2, 2, '#ffd8ec'); c.rect(1, 8, 12, 1, '#c85a98')
    for k, x in enumerate((2, 5, 8, 11)):
        for j in range(10):
            c.set(x + round(1.2 * math.sin((j + k * 2 + frame * 3) / 1.8)), 9 + j, '#f08ac0' if j % 3 else '#c85a98')
    return c.outlined('#7a2a5a')

def puffer():
    c = TCan(16, 16); circle(c, 8, 8, 6, '#e8c050'); circle(c, 8, 10, 4, '#f6ecc0')
    for a in range(0, 360, 30): c.set(8 + round(7.4 * math.cos(math.radians(a))), 8 + round(7.4 * math.sin(math.radians(a))), '#8a6a1a')
    c.rect(4, 6, 2, 2, '#1a1420'); c.set(4, 6, '#ffffff'); c.rect(2, 9, 2, 1, '#c0302a'); c.rect(13, 7, 3, 3, '#c89a30')
    return c.outlined()

def ray():
    c = TCan(30, 13); d = ImageDraw.Draw(c.im)
    d.polygon([(0, 7), (9, 1), (18, 6), (9, 12)], fill=(58, 74, 96, 255)); d.polygon([(2, 7), (9, 9), (16, 7), (9, 11)], fill=(88, 106, 130, 255))
    c.px = c.im.load()
    c.rect(17, 6, 12, 1, '#3a4a60'); c.set(4, 6, '#ffffff'); c.set(6, 5, '#ffffff')
    return c.outlined()

def build_things_v03():
    add('enemy/shark0', shark(0)); add('enemy/shark1', shark(1))
    add('enemy/jelly0', jelly(0)); add('enemy/jelly1', jelly(1))
    add('enemy/puffer', puffer()); add('enemy/ray', ray())


def build_things_v02():
    add('enemy/drone0', drone(0)); add('enemy/drone1', drone(1))
    add('obst/ball', ball()); add('obst/hurdle', hurdle()); add('obst/cone', cone())
    add('obst/camera', tv_camera()); add('obst/cables', cables()); add('obst/boom', boom_mic())
    add('enemy/dolly0', dolly(0)); add('enemy/dolly1', dolly(1)); add('obst/spot', spotlight())
    add('enemy/rocker0', rows_frame(ROCKER, ROCKER_P).up(3)); add('enemy/rocker1', rows_frame(ROCKER2, ROCKER_P).up(3))
    add('obst/stool', bar_stool()); add('obst/barrel', barrel()); add('obst/lamp', bar_lamp())
    add('obst/flaske', rows_frame(BOTTLE, dict(K='#1a1420', C='#c8ccd4', N='#8a4a1a', L='#f6f0e0')))


def build_things():
    add('enemy/goose0', rows_frame(GOOSE, GOOSE_P).up(3)); add('enemy/goose1', rows_frame(GOOSE2, GOOSE_P).up(3))
    add('obst/cow', rows_frame(COW, COW_P).up(3))
    add('enemy/dozer0', dozer(0)); add('enemy/dozer1', dozer(1))
    for name, rows in (('walk0', DUE), ('walk1', DUE_W2), ('fly0', DUE_FLY), ('fly1', DUE_FLY2)):
        add(f'due/{name}', rows_frame(scaled(rows, 2), DUE_P))
    add('boss/0', boss_frame(DUE)); add('boss/1', boss_frame(DUE_FLY2))
    add('obst/crate', crate()); add('obst/books', books())
    add('obst/kuffert', rows_frame(scaled(KUFFERT, 2), KUF_P))
    add('obst/cart', rows_frame(scaled(CART, 2), CART_P))
    add('obst/ski', rows_frame(scaled(SKI, 2), SKI_P))
    add('obst/lowbar', lowbar())
    add('item/beer', rows_frame(BOTTLE, BOT_P))
    add('item/shot', rows_frame(scaled(SHOT, 2), SHOT_P))
    hp = {'H': '#e8283a', 'h': '#ff9aa0', 'K': '#1a1420'}
    add('item/heart', rows_frame(scaled(HEART9, 2), hp))
    add('item/quiz', rows_frame(scaled(QUIZ, 2), QUIZ_P))
    add('obj/flag0', flag(False)); add('obj/flag1', flag(True)); add('obj/goal', goal())
    add('obj/taxi', rows_frame(scaled(TAXI, 2), dict(P, X='#f2d21b', l='#fff6a0', O='#222222', T='#c03838', w='#4a6a9a')))
    add('hud/heart', rows_frame(HEART9, hp))
    add('hud/heart_empty', rows_frame(HEART9, {'H': '#5a2a30', 'h': '#7a3a40', 'K': '#1a1420'}))
    add('hud/beer', rows_frame(BOTTLE, BOT_P))
    add('hud/trophy', rows_frame(['GGGGGG', 'gGGGGg', '.gGGg.', '..Gg..', '.GGGG.'], dict(K='#7a4a18', G='#fff2b0', g='#e8b040')))
    for name, rows, pal in (('feather', ['.aA.', 'aAAA', '.aA.'], dict(a='#8a8e9a', A='#e8ecf0')),
                            ('puff', ['.AA.', 'AAAA', 'AAAA', '.AA.'], dict(A='#f4f7fb')),
                            ('star', ['..y..', '.yyy.', 'yyyyy', '.yyy.', '..y..'], dict(y='#ffe060')),
                            ('foam', ['AA', 'AA'], dict(A='#ffffff'))):
        c = TCan(len(rows[0]), len(rows)); c.sprite(rows, 0, 0, pal, ol=False); add(f'fx/{name}', c)
    px = TCan(2, 2, bg='#ffffff'); add('fx/pixel', px)


# =====================================================================
# Baggrunde pr. bane: sky (fast), far og mid (parallax, går op i sømmen),
# ground og pit (fliser à 24x30 i tegneopløsning)
# =====================================================================
def save_bg(theme, layer, can):
    can.up().save(os.path.join(OUT, 'bg', f'{theme}_{layer}.png'))

def waves(c, y0, y1, hi, mid, seed, n=None):
    r = random.Random(seed)
    for _ in range(n or (y1 - y0) * c.w // 50):
        c.rect(r.randrange(c.w), r.randrange(y0 + 1, y1), r.randint(2, 5), 1, hi if r.random() < .5 else mid)

def auto_house(c, r, x, w, top, wall, roof, doorcol, roofh=24, chimney=True):
    house(c, x, w, top, wall, roof, BASE_Y, roofh=roofh, chimney=chimney, rnd=r)
    for wy in range(top + 8, BASE_Y - 40, 22):
        for wx in range(x + 6, x + w - 14, 18):
            window(c, wx, wy, star=r.random() < .4, lit=r.random() < .2)
    dx = x + w // 2 - 5
    door(c, dx, BASE_Y - 20, doorcol, 20)
    if dx - 18 > x + 3: window(c, dx - 18, BASE_Y - 26)
    if dx + 18 < x + w - 12: window(c, dx + 18, BASE_Y - 26)

def bg_dragoer():
    sky = TCan(320, 180, bg='#7ab4e8')
    sky.vgrad(0, 150, ['#4f9ce8', '#86c2f2', '#b8def8', '#e8f0f8'])
    for (x, y, s) in [(40, 14, 1.0), (150, 30, .7), (236, 10, 1.1), (300, 44, .6)]: cloud(sky, x, y, s)
    sky.rect(0, 150, 320, 30, '#b4b0aa'); save_bg('dragoer', 'sky', sky)
    far = TCan(320, 180, wrap=True)
    far.rect(0, 116, 320, 34, '#3a86c8'); far.rect(0, 116, 320, 1, '#2c6aa8'); waves(far, 117, 150, '#7ab8e8', '#5aa0e0', 3)
    far.rect(0, 108, 320, 1, '#8aa4c0')
    for px in (90, 130):
        far.rect(px, 92, 1, 16, '#8aa4c0'); far.rect(px + 3, 92, 1, 16, '#8aa4c0')
        for k in range(1, 8): far.set(px - k * 3, 92 + k * 2, '#a8bcd4'); far.set(px + 3 + k * 3, 92 + k * 2, '#a8bcd4')
    for x in range(10, 320, 22): far.rect(x, 109, 1, 7, '#8aa4c0')
    for (bx, hull) in ((230, '#c0563a'), (40, '#2a6a4a')):
        far.rect(bx, 124, 26, 3, hull); far.rect(bx + 2, 127, 22, 1, shade(hull)); far.rect(bx + 8, 108, 1, 16, '#5a3a2a')
        far.rect(bx + 14, 118, 8, 6, '#f6f2e8'); far.rect(bx + 9, 110, 6, 8, '#efe3c8')
    save_bg('dragoer', 'far', far)
    mid = TCan(640, 180, wrap=True); r = random.Random(2)
    specs = [(8, 50, 78, '#f2c24a', '#b8452e', '#2a4a8a'), (66, 44, 86, '#efe9dc', '#2e3440', '#b8452e'),
             (182, 56, 74, '#e8a64a', '#b8452e', '#2f5a3a'), (246, 62, 82, '#a6c9a2', '#4a5560', '#2f5a3a'),
             (318, 64, 64, '#f2c24a', '#b8452e', '#2a4a8a'), (392, 60, 78, '#efe9dc', '#2e3440', '#b8452e'),
             (462, 50, 72, '#e8744a', '#b8452e', '#2a4a8a'), (522, 46, 84, '#f2c24a', '#4a5560', '#2f5a3a'), (578, 52, 80, '#efe9dc', '#b8452e', '#2a4a8a')]
    for (x, w, top, wall, roof, dc) in specs: auto_house(mid, r, x, w, top, wall, roof, dc, roofh=20 + r.randint(0, 8))
    # røgeriet med tre skorstene
    mid.rect(116, 100, 58, 50, '#f2f0e8'); mid.rect(116, 100, 58, 2, '#d8d4cc')
    for j in range(12): mid.rect(114 + j // 2, 88 + j, 62 - j, 1, '#2e3440')
    for cx in (124, 142, 160):
        for j in range(26): mid.rect(cx - (26 - j) // 9, 64 + j, 6 + 2 * ((26 - j) // 9), 1, '#f6f2e8' if j > 2 else '#d8d4cc')
        mid.rect(cx - 3, 61, 12, 3, '#ffffff')
        for s, (dx, dy) in enumerate([(2, -4), (4, -9), (1, -14)]): puff(mid, cx + 3 + dx, 58 + dy, 3 - s // 2, '#eef2f6', '#c8d0d8')
    mid.text('RØGERI', 132, 114, '#2e3440'); door(mid, 140, BASE_Y - 20, '#2e3440', 20, wreath=False)
    for (a, b, y) in [(58, 66, 96), (238, 246, 92), (382, 392, 88), (512, 522, 92), (630, 648, 96)]: lights_string(mid, a, b, y, 4)
    save_bg('dragoer', 'mid', mid)
    g = TCan(24, 30, bg='#b4b0aa')
    for y in range(0, 30, 4):
        off = (y // 4) % 2 * 3
        for x in range(-off, 24, 6):
            g.rect(x, y, 5, 3, ['#c4c0b8', '#aca8a0', '#bcb8b0'][(x * 7 + y) % 3]); g.set(x + 1, y, '#d4d0c8')
    g.rect(0, 0, 24, 1, '#e8e4dc'); g.rect(0, 1, 24, 1, '#8a8680')
    save_bg('dragoer', 'ground', g)
    p = TCan(24, 30, bg='#2f7ac8'); p.rect(0, 0, 24, 5, '#1d4a80'); p.rect(0, 5, 24, 1, '#8cc8f5')
    for (x, y) in [(2, 9), (14, 12), (6, 17), (18, 21), (1, 25), (11, 27)]: p.rect(x, y, 4, 1, '#5aa0e0')
    save_bg('dragoer', 'pit', p)

def bg_lufthavn():
    sky = TCan(320, 180, bg='#2a2a5a'); sky.vgrad(0, 150, ['#2a2a5a', '#6a3a6a', '#d8685a', '#f6b86a'])
    r = random.Random(5)
    for _ in range(30): sky.set(r.randrange(320), r.randrange(50), '#ffffff')
    sky.rect(0, 150, 320, 30, '#4a4a56'); save_bg('lufthavn', 'sky', sky)
    far = TCan(320, 180, wrap=True)
    far.rect(0, 128, 320, 22, '#3a3a4a')
    for x in range(0, 320, 8): far.rect(x, 138, 4, 1, '#f6f2e8')
    for x in range(2, 320, 6): far.set(x, 129, '#ffd23f' if x % 12 else '#3ad4ff')
    far.rect(254, 60, 8, 68, '#c8ccd4'); far.rect(256, 60, 2, 68, '#e8ecf0')
    far.rect(244, 48, 28, 4, '#8a8e9a'); far.rect(246, 52, 24, 9, '#3a5a7a'); far.rect(246, 52, 24, 1, '#8ab8e0'); far.rect(242, 46, 32, 2, '#c8ccd4'); far.set(258, 42, '#ff3030')
    far.sprite(scaled(PLANE, 2), 60, 104, dict(K='#1d2a44', W='#f4f7fb', w='#5a7ab0', R='#c8323a', T='#c8323a'))
    save_bg('lufthavn', 'far', far)
    mid = TCan(640, 180, wrap=True)
    mid.rect(0, 80, 400, 70, '#9aa4b4'); mid.rect(0, 76, 402, 5, '#5a6474'); mid.rect(0, 74, 404, 2, '#ffffff')
    for x in range(6, 396, 14):
        mid.rect(x, 86, 11, 36, '#2a6a8a'); mid.rect(x, 86, 11, 2, '#6ab0d0'); mid.set(x + 2, 90, '#a8e0f8')
    for (x, t) in ((30, 'GATE A4'), (130, 'AFGANG'), (240, 'GATE B7'), (330, 'TOLD')):
        w = text_w(t) + 8; mid.rect(x, 128, w, 10, '#1a1a22'); mid.text(t, x + 4, 131, '#ffd23f')
    mid.rect(400, 104, 70, 10, '#c8ccd4'); mid.rect(400, 104, 70, 2, '#e8ecf0'); mid.rect(462, 114, 4, 36, '#6a6e7a')
    mid.rect(500, 118, 56, 32, '#f2f0e8'); mid.rect(498, 114, 60, 5, '#c03030')
    for i in range(0, 60, 6): mid.rect(498 + i, 119, 3, 3, '#c03030')
    mid.rect(506, 126, 26, 14, '#3a5a7a'); mid.rect(507, 127, 24, 2, '#ffcf6a'); mid.rect(502, 102, 52, 11, '#1a1420'); mid.text('FLYVERGRILL', 507, 105, '#ffd23f')
    for x in range(566, 640, 4): mid.rect(x, 132, 1, 18, '#6a6e7a')
    mid.rect(566, 132, 74, 1, '#6a6e7a'); mid.rect(566, 140, 74, 1, '#6a6e7a')
    save_bg('lufthavn', 'mid', mid)
    g = TCan(24, 30, bg='#4a4a56')
    for x in range(0, 24, 3):
        for y in range(1, 30, 3):
            if (x * 7 + y * 3) % 11 == 0: g.set(x, y, '#56566a')
    g.rect(0, 0, 24, 1, '#6a6a7a'); g.rect(0, 12, 24, 2, '#f2c418'); g.rect(0, 22, 12, 1, '#f6f2e8')
    save_bg('lufthavn', 'ground', g)
    p = TCan(24, 30, bg='#14141c')
    for i in range(-8, 24, 8):
        for j in range(5):
            for t in range(4): p.set(i + j + t, j, '#f2c418')
    p.rect(0, 5, 24, 1, '#2a2a34')
    save_bg('lufthavn', 'pit', p)

def bg_faelled():
    sky = TCan(320, 180, bg='#a8c8e8'); sky.vgrad(0, 150, ['#7aa8d8', '#a8c8e8', '#e0dcd8', '#f4dcc0'])
    for (x, y, s_) in [(50, 22, .9), (190, 12, 1.1), (280, 40, .6)]: cloud(sky, x, y, s_)
    sky.rect(0, 150, 320, 30, '#6a9a4a'); save_bg('faelled', 'sky', sky)
    far = TCan(320, 180, wrap=True); r = random.Random(21)
    for (x, w, h) in [(20, 26, 70), (52, 18, 52), (250, 30, 78), (286, 20, 60)]:        # Ørestad i horisonten
        far.rect(x, 150 - h, w, h, '#9aa8c0')
        for y in range(150 - h + 3, 148, 5): far.rect(x + 2, y, w - 4, 2, '#b8c4d8')
    far.rect(140, 60, 2, 90, '#c8a020'); far.rect(110, 62, 70, 2, '#c8a020'); far.rect(170, 64, 1, 18, '#3a3a44'); far.rect(166, 82, 9, 6, '#6a6e7a')   # kranen
    far.rect(112, 64, 8, 5, '#6a6e7a')
    for x in range(0, 320, 5):                                                             # skovbryn
        h = 22 + int(8 * math.sin(x / 13.0)) + r.randint(0, 8)
        far.rect(x, 150 - h, 6, h, '#4a6a3a' if (x // 5) % 2 else '#3f5e34')
        far.rect(x + 1, 150 - h - 2, 3, 2, '#5a7a44')
    save_bg('faelled', 'far', far)
    mid = TCan(640, 180, wrap=True)
    def tree(x, h):
        mid.rect(x, 150 - h, 3, h, '#e8e4dc'); mid.rect(x, 150 - h, 1, h, '#ffffff')
        for yy in range(150 - h + 4, 150, 7): mid.rect(x, yy, 2, 1, '#3a3a34')
        for k in range(5):
            yy = 150 - h + 2 + k * 6; d = 1 if k % 2 else -1
            for t in range(10 - k): mid.set(x + 1 + d * t, yy - t // 2, '#6a5a48')
        for (dx, dy, rr) in ((0, -4, 7), (-8, 2, 5), (8, 3, 5)): puff(mid, x + 1 + dx, 150 - h + dy, rr, '#e8f0f8', '#c0d0dc')
    def bush(x, w, col='#3f7a34'):
        for i in range(0, w, 5): puff(mid, x + i, 144 - (i * 7 % 5), 6, light(col), col)
        for i in range(2, w, 9): mid.rect(x + i, 139 - (i % 4), 2, 2, '#d83030')
        for i in range(0, w, 4): mid.set(x + i, 137 - (i * 3 % 5), '#ffffff')
    for (x, h) in ((30, 70), (96, 56), (262, 76), (430, 62), (590, 72)): tree(x, h)
    for (x, w) in ((46, 34), (120, 50), (300, 44), (470, 60), (606, 28)): bush(x, w)
    mid.rect(214, 118, 2, 32, '#5a3a2a'); mid.rect(246, 118, 2, 32, '#5a3a2a'); mid.rect(206, 104, 50, 16, '#1a1420'); mid.rect(207, 105, 48, 14, '#f2c418')
    mid.text('BYGGEPLADS', 211, 108, '#1a1420')
    for i in range(-14, 48, 8):
        for j in range(3):
            for t in range(4):
                if 207 <= 207 + i + j + t <= 254: mid.set(207 + i + j + t, 116 + j, '#1a1420')
    for x in range(520, 590, 10): mid.rect(x, 138, 2, 12, '#8a6a4a')
    mid.rect(520, 141, 72, 2, '#a88a6a'); mid.rect(520, 146, 72, 1, '#a88a6a')
    for (sx, sy) in ((560, 128),):                                                           # svane ved hegnet
        mid.rect(sx, sy + 8, 14, 6, '#f4f7fb'); mid.rect(sx - 2, sy, 3, 10, '#f4f7fb'); mid.rect(sx - 4, sy, 3, 3, '#f4f7fb'); mid.rect(sx - 6, sy + 1, 2, 1, '#e8862a')
    save_bg('faelled', 'mid', mid)
    g = TCan(24, 30, bg='#6a9a4a')
    for y in range(3, 30, 3):
        for x in range((y // 3 % 2) * 3, 24, 6): g.set(x, y, '#5a8a3e'); g.set(x + 1, y - 1, '#7aac58')
    g.rect(0, 0, 24, 2, '#f4f7fb')
    for x in (1, 6, 12, 17, 22): g.set(x, 2, '#f4f7fb'); g.rect(x, 0, 1, 1, '#c8dcb8')
    g.rect(0, 10, 24, 6, '#b89a6a'); g.rect(0, 10, 24, 1, '#c8aa7a'); g.rect(3, 13, 4, 1, '#a08656'); g.rect(15, 12, 5, 1, '#a08656')
    save_bg('faelled', 'ground', g)
    p = TCan(24, 30, bg='#3a7a8a'); p.rect(0, 0, 24, 5, '#2a5460'); p.rect(0, 5, 24, 1, '#a8d8e0')
    for (x, y) in [(3, 10), (15, 14), (7, 20), (17, 25)]: p.rect(x, y, 4, 1, '#5a9aa8')
    for x in (2, 11, 20): p.rect(x, 0, 1, 7, '#8a7a3a'); p.rect(x, 0, 1, 2, '#5a4a2a')
    save_bg('faelled', 'pit', p)

def bg_idraetspark():
    sky = TCan(320, 180, bg='#9ac0e8'); sky.vgrad(0, 150, ['#4a7ac8', '#86b0e4', '#c8d8ec', '#f0e4d8'])
    for (x, y, s_) in [(70, 18, 1.0), (230, 30, .8)]: cloud(sky, x, y, s_)
    sky.rect(0, 150, 320, 30, '#3f8a3a'); save_bg('idraetspark', 'sky', sky)
    far = TCan(320, 180, wrap=True)
    for mx in (60, 220):                                   # lysmaster
        far.rect(mx, 30, 3, 120, '#8a8e9a'); far.rect(mx - 9, 22, 21, 10, '#3a3a44')
        for j in range(2):
            for i in range(4): far.rect(mx - 7 + i * 5, 24 + j * 4, 3, 2, '#fff6c0')
    far.rect(0, 92, 320, 6, '#3a4a66'); far.rect(0, 98, 320, 52, '#7a8696')      # fjern tribune
    r = random.Random(31)
    for y in range(102, 148, 5):
        for x in range(2, 320, 4): far.set(x + (y // 5) % 2 * 2, y, r.choice(['#2a5ac8', '#f4f7fb', '#5a6270', '#5a6270', '#2a5ac8']))
    save_bg('idraetspark', 'far', far)
    for frame in (0, 1):
        mid = TCan(640, 180, wrap=True); r = random.Random(33)
        # Sunnyside: ståtribunen med de største fans i blå og hvide Fremad Amager-trøjer
        mid.rect(0, 96, 330, 54, '#4a5262'); mid.rect(0, 94, 330, 2, '#2a3040')
        for k in range(3): mid.rect(0, 112 + k * 12, 330, 1, '#3a4252')
        mid.rect(8, 80, 314, 13, '#f4f7fb'); mid.rect(8, 80, 314, 1, '#2a5ac8'); mid.rect(8, 92, 314, 1, '#2a5ac8')
        for bx in (30, 138, 246): mid.text('SUNNYSIDE', bx, 84, '#1d4ea8')
        for bx in (8, 116, 224, 320): mid.rect(bx, 80, 2, 16, '#8a8e9a')
        n = 0
        for row in range(3):
            feet = 118 + row * 12
            for fx in range(6 + (row % 2) * 4, 324, 9):
                n += 1
                shirt = ('#1d4ea8', '#f4f7fb', 'stribet')[r.randrange(3)]
                skin = r.choice(['#f0b48c', '#e0a080', '#f4c4a0', '#c88a60'])
                up = (n + frame) % 2 == 0
                hop = 1 if up else 0
                y0 = feet - 13 - hop
                mid.rect(fx, y0 + 4, 5, 6, '#1d4ea8' if shirt != '#f4f7fb' else '#f4f7fb')
                if shirt == 'stribet':
                    for sx in (1, 3): mid.rect(fx + sx, y0 + 4, 1, 6, '#f4f7fb')
                mid.rect(fx + 1, y0, 3, 3, skin); mid.rect(fx + 1, y0 - 1, 3, 1, r.choice(['#3a2a1a', '#1a1420', '#c8a040', '#1d4ea8']))
                mid.rect(fx, y0 + 10, 2, 3, '#2a3040'); mid.rect(fx + 3, y0 + 10, 2, 3, '#2a3040')
                if up: mid.rect(fx - 1, y0 - 1, 1, 6, skin); mid.rect(fx + 5, y0 - 1, 1, 6, skin)
                else: mid.rect(fx - 1, y0 + 4, 1, 5, skin); mid.rect(fx + 5, y0 + 4, 1, 5, skin)
                if n % 7 == 0: mid.rect(fx, y0 + 3, 5, 1, '#f4f7fb' if shirt != '#f4f7fb' else '#1d4ea8')     # halstørklæde
        for (px, sway) in ((96, 0), (204, 1), (308, 0)):            # flag
            dx = 1 if (frame + sway) % 2 else 0
            mid.rect(px, 86, 1, 30, '#c8ccd4'); mid.rect(px + 1, 86 + dx, 8, 5, '#1d4ea8'); mid.rect(px + 1 + 8, 86 + (1 - dx), 8, 5, '#f4f7fb')
        # mål, måltavle og bander
        mid.rect(360, 104, 2, 46, '#f4f7fb'); mid.rect(420, 104, 2, 46, '#f4f7fb'); mid.rect(360, 104, 62, 2, '#f4f7fb')
        for x in range(364, 420, 4): mid.rect(x, 106, 1, 44, '#c8d4e0')
        for y in range(110, 150, 4): mid.rect(362, y, 58, 1, '#c8d4e0')
        mid.rect(470, 70, 3, 80, '#6a6e7a'); mid.rect(540, 70, 3, 80, '#6a6e7a'); mid.rect(456, 56, 100, 34, '#1a1420'); mid.rect(458, 58, 96, 30, '#22262e')
        mid.text('FREMAD', 462, 62, '#ffd23f'); mid.text('GÆSTER', 520, 62, '#ffd23f'); mid.text('2', 472, 72, '#ff5a3a', 2); mid.text('1', 530, 72, '#ff5a3a', 2)
        mid.rect(330, 138, 310, 12, '#f4f7fb'); mid.rect(330, 138, 310, 1, '#8a8e9a')
        for (tx, t) in ((340, 'FREMAD AMAGER'), (440, 'SUNDBY IDRÆTSPARK'), (560, 'AMAGER'), ): mid.text(t, tx, 142, '#1d4ea8')
        mid.rect(0, 140, 330, 10, '#1d4ea8'); mid.rect(0, 140, 330, 1, '#f4f7fb')
        for tx in (10, 120, 230): mid.text('FREMAD AMAGER', tx, 143, '#f4f7fb')
        save_bg('idraetspark', 'mid' if frame == 0 else 'mid2', mid)
    g = TCan(24, 30, bg='#3f8a3a')
    for y in range(0, 30, 3):
        for x in range((y // 3 % 2) * 2, 24, 4): g.set(x, y, '#4f9e48')
    g.rect(0, 0, 24, 1, '#5aae52'); g.rect(0, 8, 24, 2, '#f4f7fb')
    save_bg('idraetspark', 'ground', g)
    p = TCan(24, 30, bg='#2f7ac8'); p.rect(0, 0, 24, 3, '#f4f7fb'); p.rect(0, 3, 24, 3, '#1d4a80'); p.rect(0, 6, 24, 1, '#8cc8f5')
    for (x, y) in [(3, 11), (15, 15), (7, 21), (17, 26)]: p.rect(x, y, 4, 1, '#5aa0e0')
    save_bg('idraetspark', 'pit', p)

def bg_dr():
    sky = TCan(320, 180, bg='#1a1c28')
    sky.rect(0, 0, 320, 40, '#12141e'); sky.rect(0, 40, 320, 110, '#242838')
    for y in (8, 16): sky.rect(0, y, 320, 1, '#5a5e6a')
    for x in range(0, 320, 8): sky.rect(x, 8, 1, 9, '#5a5e6a'); sky.set(x + 4, 12, '#5a5e6a')
    for lx in range(20, 320, 44):
        sky.rect(lx, 17, 8, 7, '#2a2a34'); sky.rect(lx + 1, 24, 6, 2, '#fff2a0')
        for j in range(0, 70, 2):
            for i in range(-j // 3, j // 3 + 7):
                if (i + j) % 4 == 0: sky.set(lx + i, 26 + j, '#3e4460')
    sky.rect(0, 150, 320, 30, '#3a3c48'); save_bg('dr', 'sky', sky)
    far = TCan(320, 180, wrap=True)
    far.rect(8, 58, 124, 76, '#5a5e6a'); far.rect(10, 60, 120, 72, '#2a9a4a'); far.rect(10, 60, 120, 2, '#4aba6a')       # greenscreen
    far.rect(30, 134, 3, 16, '#5a5e6a'); far.rect(108, 134, 3, 16, '#5a5e6a')
    far.rect(150, 52, 160, 84, '#12141e')                                                                                 # skærmvæg
    cols = ['#2a6ad8', '#c8323a', '#f2c418', '#2a8a4a', '#8a4ab0', '#e8ecf0']
    for j in range(3):
        for i in range(5):
            x, y = 154 + i * 31, 56 + j * 26
            far.rect(x, y, 28, 23, '#1a1c28'); far.rect(x + 1, y + 1, 26, 21, cols[(i * 2 + j * 3) % 6]); far.rect(x + 1, y + 16, 26, 6, '#1a1420')
            far.rect(x + 9, y + 5, 8, 8, '#f0b48c'); far.rect(x + 7, y + 12, 12, 4, '#f4f7fb')
    far.rect(136, 36, 34, 12, '#1a1420'); far.rect(137, 37, 32, 10, '#c8282a'); far.text('ON AIR', 141, 40, '#ffffff')
    save_bg('dr', 'far', far)
    mid = TCan(640, 180, wrap=True)
    mid.rect(30, 124, 110, 26, '#e8ecf0'); mid.rect(30, 124, 110, 3, '#ffffff'); mid.rect(30, 136, 110, 4, '#c8282a'); mid.text('DR BYEN', 68, 129, '#1a1420')
    for (x, y) in ((50, 112), (104, 112)): mid.rect(x, y, 16, 12, '#1a1420'); mid.rect(x + 1, y + 1, 14, 9, '#6ab0e8')
    def case(x, y, w, h):
        mid.rect(x, y, w, h, '#22242e'); mid.rect(x, y, w, 1, '#c8ccd4'); mid.rect(x, y + h - 1, w, 1, '#c8ccd4'); mid.rect(x, y, 1, h, '#c8ccd4'); mid.rect(x + w - 1, y, 1, h, '#c8ccd4')
        mid.rect(x + w // 2 - 2, y + h // 2 - 1, 4, 2, '#c8ccd4')
    case(170, 130, 30, 20); case(176, 114, 22, 16); case(204, 136, 22, 14)
    for (lx, h) in ((250, 70), (420, 64)):                                    # lysstativer
        mid.rect(lx, 150 - h, 2, h, '#6a6e7a'); mid.rect(lx - 6, 148, 14, 2, '#3a3a44'); mid.rect(lx - 6, 150 - h - 8, 14, 9, '#2a2a34'); mid.rect(lx - 5, 150 - h, 12, 2, '#fff2a0')
    mid.rect(290, 96, 64, 30, '#1a1420'); mid.rect(292, 98, 60, 26, '#22364e'); mid.text('TV AVISEN', 300, 104, '#ffffff'); mid.text('KL. 21', 310, 113, '#ffd23f')
    mid.rect(320, 126, 4, 24, '#6a6e7a'); mid.rect(310, 148, 24, 2, '#3a3a44')
    for (dx_, col) in ((450, '#c8282a'), (468, '#2a6ad8')):                    # kabeltromler
        circle(mid, dx_ + 6, 142, 7, '#5a3a2a'); circle(mid, dx_ + 6, 142, 5, col); circle(mid, dx_ + 6, 142, 2, '#1a1420')
    mid.rect(500, 100, 60, 14, '#1a1420'); mid.rect(501, 101, 58, 12, '#c8282a'); mid.text('OPTAGELSE', 508, 104, '#ffffff')
    case(580, 126, 40, 24); case(588, 110, 26, 16)
    for x in range(0, 640, 3): mid.set(x, 149 - (1 if (x // 3) % 5 == 0 else 0), '#1a1420')
    save_bg('dr', 'mid', mid)
    g = TCan(24, 30, bg='#3a3c48')
    g.rect(0, 0, 24, 1, '#5a5e6a'); g.rect(0, 1, 24, 1, '#2a2c38')
    for (x, y) in ((3, 8), (14, 17), (8, 24)): g.rect(x, y, 6, 1, '#44485a')
    g.rect(16, 6, 5, 1, '#f2c418'); g.rect(18, 4, 1, 5, '#f2c418')
    save_bg('dr', 'ground', g)
    p = TCan(24, 30, bg='#12141e'); p.rect(0, 0, 24, 2, '#f2c418')
    for k, col in enumerate(('#d02030', '#2a6ad8', '#f2c418', '#2a8a4a')):
        for x in range(24): p.set(x, 8 + k * 5 + round(1.5 * math.sin(x * math.pi / 6 + k)), col)
    save_bg('dr', 'pit', p)

def bg_jaguaren():
    sky = TCan(320, 180, bg='#4a1a1e')
    for y in range(0, 150, 8):
        for x in range((y // 8 % 2) * 6, 320, 12): sky.rect(x, y + 2, 2, 4, '#5a2226'); sky.set(x, y + 3, '#6a2a2e')
    sky.rect(0, 0, 320, 14, '#2a1810')
    for x in range(0, 320, 40): sky.rect(x, 0, 6, 150, '#3a2216'); sky.rect(x, 0, 1, 150, '#4a2c1c')
    r = random.Random(41)
    for _ in range(500): sky.set(r.randrange(320), r.randrange(14, 90), '#6a4a4a')      # røg
    sky.rect(0, 150, 320, 30, '#5a3a22'); save_bg('jaguaren', 'sky', sky)
    far = TCan(320, 180, wrap=True)
    far.rect(10, 62, 180, 66, '#2a1810'); far.rect(12, 64, 176, 62, '#3a2216')
    for sy in (84, 104, 124): far.rect(12, sy, 176, 2, '#5a3a22')
    for sy in (84, 104, 124):
        for bx in range(16, 184, 6): far.rect(bx, sy - 9 - (bx % 4), 3, 9 + (bx % 4), r.choice(['#2f8a3a', '#8a4a1a', '#c8ccd4', '#c03030', '#e8b040', '#2a5a8a']))
    far.rect(60, 30, 100, 22, '#1a1420'); far.rect(61, 31, 98, 20, '#2a1024')
    far.text('JAGUAREN', 70, 36, '#ff4f9a', 2); far.rect(66, 48, 88, 1, '#ffd23f')
    circle(far, 250, 80, 14, '#1a1420'); circle(far, 250, 80, 12, '#e8e0c8'); circle(far, 250, 80, 8, '#c03030'); circle(far, 250, 80, 5, '#2f7a3a'); circle(far, 250, 80, 2, '#c03030')
    for (px, py) in ((208, 60), (290, 66)): far.rect(px, py, 18, 14, '#c8a040'); far.rect(px + 2, py + 2, 14, 10, '#3a5a7a')
    save_bg('jaguaren', 'far', far)
    mid = TCan(640, 180, wrap=True)
    mid.rect(20, 120, 210, 30, '#6a3a1e'); mid.rect(18, 116, 214, 5, '#8a5a2a'); mid.rect(18, 116, 214, 1, '#b8863a'); mid.rect(20, 140, 210, 2, '#c8a040')
    for x in range(24, 228, 14): mid.rect(x, 124, 1, 26, '#5a2e16')
    for tx in (60, 72, 84): mid.rect(tx, 104, 3, 12, '#c8ccd4'); mid.rect(tx - 2, 104, 7, 2, '#c8a040'); mid.rect(tx - 1, 100, 5, 4, '#1a1420')
    for gx in (120, 132, 170): mid.rect(gx, 108, 6, 8, '#f0a020'); mid.rect(gx, 107, 6, 2, '#ffffff')
    mid.rect(290, 126, 100, 6, '#5a3a1e'); mid.rect(292, 124, 96, 4, '#2f7a3a'); mid.rect(294, 132, 6, 18, '#4a2c16'); mid.rect(380, 132, 6, 18, '#4a2c16')
    for (bx, col) in ((310, '#f4f7fb'), (330, '#c03030'), (340, '#f2c418'), (362, '#1a1420')): mid.rect(bx, 122, 3, 3, col)
    mid.rect(430, 96, 34, 54, '#8a2a2a'); mid.rect(432, 98, 30, 20, '#ffd23f'); mid.rect(434, 100, 26, 16, '#ff9a3a'); mid.rect(432, 122, 30, 20, '#5a1a1a')
    for y in range(124, 140, 4): mid.rect(434, y, 26, 2, '#c8a040')
    for j in range(8): mid.rect(430 + j, 96 - j // 2 - 1, 34 - 2 * j, 1, '#a83a3a')
    mid.rect(500, 104, 24, 46, '#3a3a44'); mid.rect(502, 108, 20, 14, '#1a1420')
    for k in range(3): mid.rect(504 + k * 6, 110, 5, 10, ['#c03030', '#f2c418', '#2f8a3a'][k])
    mid.rect(524, 112, 3, 14, '#c8ccd4'); circle(mid, 525, 110, 2, '#c03030')
    mid.rect(560, 132, 50, 4, '#6a3a1e'); mid.rect(582, 136, 6, 14, '#4a2c16')
    for gx in (568, 590, 600): mid.rect(gx, 124, 6, 8, '#f0a020'); mid.rect(gx, 123, 6, 2, '#ffffff')
    save_bg('jaguaren', 'mid', mid)
    g = TCan(24, 30, bg='#6a4424')
    g.rect(0, 0, 24, 1, '#8a5a30')
    for y in (9, 19, 29): g.rect(0, y, 24, 1, '#4a2c16')
    for (x, y) in ((6, 1), (17, 10), (3, 20), (13, 20)): g.rect(x, y, 1, 9, '#4a2c16')
    for (x, y) in ((10, 4), (20, 14), (8, 24)): g.rect(x, y, 3, 1, '#7a5230')
    save_bg('jaguaren', 'ground', g)
    p = TCan(24, 30, bg='#0e0a08'); p.rect(0, 0, 24, 3, '#c8a040'); p.rect(0, 3, 24, 1, '#4a2c16')
    p.rect(6, 4, 2, 26, '#6a4424'); p.rect(16, 4, 2, 26, '#6a4424')
    for y in range(8, 30, 6): p.rect(6, y, 12, 2, '#6a4424')
    save_bg('jaguaren', 'pit', p)

def bg_blaaplanet():
    sky = TCan(320, 180, bg='#0e5a8a'); sky.vgrad(0, 150, ['#5ac8e0', '#2a9ac8', '#1670a8', '#0e4a80', '#0a3466'])
    for k in range(6):                                           # lysstråler fra overfladen
        x0 = 20 + k * 55
        for y in range(0, 120):
            for i in range(10 - y // 14):
                if (i + y) % 3 == 0: sky.set(x0 + i + y // 3, y, '#7ad8ec' if y < 50 else '#3aa8d0')
    for x in range(0, 320, 3): sky.set(x, 1 + (x // 3) % 2, '#c8f0f8')
    sky.rect(0, 150, 320, 30, '#c8b078'); save_bg('blaaplanet', 'sky', sky)
    far = TCan(320, 180, wrap=True); r = random.Random(51)
    # akvariets store rude med gæster, der kigger ind
    far.rect(30, 40, 150, 78, '#083058'); far.rect(34, 44, 142, 70, '#1a5a90'); far.rect(34, 44, 142, 2, '#3a8ac0')
    for x in (80, 128): far.rect(x, 44, 2, 70, '#083058')
    for (px, h) in ((46, 30), (60, 22), (96, 34), (110, 26), (142, 32), (158, 18)):
        far.rect(px, 114 - h, 8, h, '#0a2a4c'); far.rect(px + 1, 114 - h - 6, 6, 6, '#0a2a4c')
    for (x, w, h) in ((0, 30, 34), (190, 60, 26), (250, 70, 44)):
        for j in range(h):
            hw = int(w / 2 * math.sqrt(max(0, 1 - (1 - j / h) ** 2)))
            far.rect(x + w // 2 - hw, 150 - h + j, 2 * hw, 1, '#0c3c68')
    for _ in range(26):
        fx, fy = r.randrange(320), r.randrange(30, 120)
        far.rect(fx, fy, 3, 1, '#8ad0e8'); far.set(fx + 3, fy - 1, '#8ad0e8'); far.set(fx + 3, fy + 1, '#8ad0e8')
    save_bg('blaaplanet', 'far', far)
    mid = TCan(640, 180, wrap=True)
    def weed(x, h, col):
        for j in range(h):
            mid.rect(x + round(2 * math.sin(j / 5.0 + x)), 150 - j, 2, 1, col if j % 4 else light(col))
    def coral(x, col):
        for (dx, h) in ((0, 18), (5, 26), (10, 14), (-5, 12)):
            mid.rect(x + dx, 150 - h, 3, h, col); mid.rect(x + dx - 2, 150 - h, 7, 3, light(col)); mid.set(x + dx + 1, 150 - h - 1, '#ffffff')
    def rock(x, w, h):
        for j in range(h):
            hw = int(w / 2 * math.sqrt(max(0, 1 - (1 - j / h) ** 2)))
            mid.rect(x + w // 2 - hw, 150 - h + j, 2 * hw, 1, '#3a5a78' if j > 2 else '#5a7a98')
    for (x, h) in ((20, 50), (26, 38), (200, 60), (208, 44), (360, 54), (520, 46), (528, 62), (610, 40)): weed(x, h, '#2a8a5a')
    for (x, col) in ((70, '#e86a8a'), (250, '#f0a040'), (420, '#e86a8a'), (580, '#c85ad0')): coral(x, col)
    rock(110, 60, 24); rock(300, 44, 18); rock(456, 56, 28)
    mid.rect(118, 132, 44, 11, '#f6f2e8'); mid.rect(118, 132, 44, 1, '#8a8e9a'); mid.rect(118, 132, 44, 13, '#f6f2e8'); mid.text('DEN BLÅ', 126, 133, '#1670a8'); mid.text('PLANET', 128, 139, '#1670a8')
    mid.rect(318, 138, 22, 12, '#8a5a2a'); mid.rect(318, 138, 22, 3, '#c8a040'); mid.rect(327, 142, 4, 4, '#f2c418'); mid.rect(316, 134, 26, 5, '#6a4420')   # skattekiste
    mid.rect(486, 110, 2, 30, '#5a6a7a'); mid.rect(480, 112, 14, 2, '#5a6a7a')                                                                          # anker
    for a in range(200, 341, 10): mid.set(487 + round(9 * math.cos(math.radians(a))), 132 - round(9 * math.sin(math.radians(a))), '#5a6a7a')
    for (sx, sy) in ((180, 146), (400, 147), (560, 146)):
        for (dx, dy) in ((0, -2), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-1, 1), (1, 1), (0, -1)): mid.set(sx + dx, sy + dy, '#f07848')
    save_bg('blaaplanet', 'mid', mid)
    g = TCan(24, 30, bg='#c8b078')
    g.rect(0, 0, 24, 1, '#e8d8a8')
    for (x, y, w) in ((2, 5, 8), (14, 9, 7), (5, 15, 9), (16, 21, 6), (1, 25, 7)): g.rect(x, y, w, 1, '#b09a62')
    g.set(10, 3, '#f6f2e8'); g.set(20, 14, '#f6f2e8')
    save_bg('blaaplanet', 'ground', g)
    p = TCan(24, 30, bg='#0a3466'); p.rect(0, 0, 24, 3, '#0e4a80')
    save_bg('blaaplanet', 'pit', p)

def bg_campus():
    sky = TCan(320, 180, bg='#aab8cc'); sky.vgrad(0, 150, ['#8a9ab4', '#aab8cc', '#ccd6e2'])
    for (x, y, s) in [(60, 20, 1.2), (220, 34, 1.0)]: cloud(sky, x, y, s, '#dfe6ee', '#c4cedb')
    sky.rect(0, 150, 320, 30, '#9a9aa2'); save_bg('campus', 'sky', sky)
    far = TCan(320, 180, wrap=True); r = random.Random(11)
    for (x, w, h) in [(4, 60, 60), (76, 44, 76), (130, 70, 52), (212, 50, 70), (270, 44, 58)]:
        far.rect(x, 150 - h, w, h, '#8a92a8')
        for y in range(150 - h + 4, 148, 6): far.rect(x + 2, y, w - 4, 2, '#a8b4c8')
    save_bg('campus', 'far', far)
    mid = TCan(640, 180, wrap=True)
    def library(lx, w, name):
        mid.rect(lx, 76, w, 74, '#8a4a34'); mid.rect(lx, 76, w, 3, '#6a3a26')
        for yy in range(80, 150, 4):
            for xx in range(lx, lx + w, 8): mid.rect(xx + (yy // 4 % 2) * 4, yy, min(7, lx + w - xx - (yy // 4 % 2) * 4), 3, '#9a5a40')
        mid.rect(lx + 4, 82, w - 8, 18, '#2a4a5a')
        for xx in range(lx + 6, lx + w - 8, 6):
            mid.rect(xx, 84, 4, 14, ['#c8a040', '#a83a2a', '#3a6a8a', '#5a8a3a'][(xx // 6) % 4]); mid.rect(xx, 91, 4, 1, '#5a3a20')
        mid.rect(lx + 4, 82, w - 8, 1, '#6ab0d0')
        tw = text_w(name) + 10; mid.rect(lx + w // 2 - tw // 2, 104, tw, 9, '#f6f2e8'); mid.text(name, lx + w // 2 - tw // 2 + 5, 106, '#8a4a34')
        for dx in (12, w - 36):
            mid.rect(lx + dx, 120, 24, 30, '#ffcf6a')
            for k in range(3): mid.rect(lx + dx + 2, 124 + k * 8, 20, 6, ['#a83a2a', '#3a6a8a', '#c8a040'][k]); mid.rect(lx + dx + 2, 130 + k * 8, 20, 1, '#6a3a20')
            mid.rect(lx + dx - 2, 118, 28, 2, '#f6f2e8')
    library(10, 130, 'BIBLIOTEK'); library(410, 150, 'LÆSESAL')
    mid.rect(170, 84, 110, 66, '#5a8a7a')
    for yy in range(88, 146, 10): mid.rect(172, yy, 106, 5, '#2a4a5a'); mid.rect(172, yy, 106, 1, '#8ac0d0')
    mid.rect(178, 140, 94, 9, '#f6f2e8'); mid.text('SØNDRE CAMPUS', 182, 142, '#2a4a5a')
    for bx in range(292, 400, 14):
        for a in range(0, 360, 45):
            for cx0 in (bx + 3, bx + 10): mid.set(cx0 + round(3 * math.cos(math.radians(a))), 146 + round(3 * math.sin(math.radians(a))), '#2a2a34')
        mid.rect(bx + 3, 143, 8, 1, ['#c03030', '#3a6ad8', '#2a8a4a'][(bx // 14) % 3]); mid.rect(bx + 9, 141, 1, 3, '#2a2a34')
    for tx in (580, 612):
        mid.rect(tx, 124, 2, 26, '#5a3a2a')
        for (dx, dy, rr) in ((0, -6, 8), (-6, 0, 6), (7, 1, 6)): puff(mid, tx + 1 + dx, 118 + dy, rr, '#e8f0f8', '#b8c8d8')
    save_bg('campus', 'mid', mid)
    g = TCan(24, 30, bg='#9a9aa2')
    for y in (2, 12, 22):
        off = 0 if y != 12 else 12
        for x in range(-off, 24, 24): g.rect(x + 1, y, 22, 8, '#a8a8b0'); g.rect(x + 1, y, 22, 1, '#bcbcc4'); g.rect(x + 1, y + 7, 22, 1, '#7c7c84')
    g.rect(0, 0, 24, 2, '#f4f7fb')
    for x in (3, 9, 16, 21): g.set(x, 2, '#f4f7fb')
    save_bg('campus', 'ground', g)
    p = TCan(24, 30, bg='#3a6a8a'); p.rect(0, 0, 24, 5, '#24465e'); p.rect(0, 5, 24, 1, '#a8cce0')
    for (x, y) in [(3, 10), (15, 14), (7, 20), (17, 25)]: p.rect(x, y, 4, 1, '#5a8aa8')
    p.rect(8, 7, 9, 2, '#e8f0f8')
    save_bg('campus', 'pit', p)

def bg_center():
    sky = TCan(320, 180, bg='#f2e6d0')
    sky.rect(0, 0, 320, 30, '#d8ccb4')
    for x in range(8, 310, 26):
        sky.rect(x, 2, 22, 22, '#9ac8ea'); sky.rect(x, 2, 22, 1, '#ffffff'); sky.rect(x + 10, 2, 2, 22, '#d8ccb4')
    sky.rect(0, 26, 320, 4, '#b8a888'); sky.rect(0, 30, 320, 120, '#efe2c8')
    sky.rect(0, 150, 320, 30, '#d8c8a8'); save_bg('center', 'sky', sky)
    far = TCan(320, 180, wrap=True)
    shops = [('SKO', '#3a6ad8'), ('TØJ', '#c03030'), ('BØGER', '#2a8a4a'), ('JUL', '#c8282a'), ('IS', '#e87aa8')]
    for k, (name, col) in enumerate(shops):
        x = k * 64 + 1
        far.rect(x, 40, 62, 40, '#3a3a44'); far.rect(x + 2, 50, 58, 30, '#ffe8b0')
        far.rect(x + 4, 54, 10, 20, col); far.rect(x + 18, 60, 14, 14, shade(col)); far.rect(x + 36, 56, 20, 18, light(col))
        far.rect(x, 40, 62, 9, col); far.text(name, x + 31 - text_w(name) // 2, 42, '#ffffff')
    far.rect(0, 80, 320, 5, '#b8a888'); far.rect(0, 85, 320, 2, '#8a7a5a'); far.rect(0, 72, 320, 1, '#8a9aaa')
    for x in range(0, 320, 2): far.set(x, 74 + (x % 4 == 0), '#c8e4f4')
    for (x, l, col) in [(40, 14, '#d82a2a'), (120, 20, '#f6c945'), (200, 12, '#d82a2a'), (280, 18, '#f6c945')]:
        far.rect(x, 30, 1, l, '#8a7a5a'); puff(far, x, 30 + l + 3, 3, col, shade(col)); far.set(x - 1, 30 + l + 2, '#ffffff')
    save_bg('center', 'far', far)
    mid = TCan(640, 180, wrap=True); r = random.Random(3)
    def shop(x, w, name, col, lit='#ffd8a0'):
        mid.rect(x, 96, w, 54, '#3a3a44'); mid.rect(x + 2, 108, w - 4, 42, lit)
        mid.rect(x, 96, w, 11, col); mid.text(name, x + w // 2 - text_w(name) // 2, 99, '#ffffff' if col != '#c8282a' else '#ffd23f')
        for k in range(3): mid.rect(x + 6 + k * (w // 3 - 2), 122 + (k % 2) * 6, w // 3 - 10, 28 - (k % 2) * 6, [shade(col), light(col), col][k])
    shop(8, 90, 'KINA BUFFET', '#c8282a')
    for lx in (16, 40, 64, 88): mid.rect(lx, 108, 4, 6, '#e82a2a'); mid.rect(lx + 1, 107, 2, 1, '#ffd23f'); mid.rect(lx + 1, 114, 2, 2, '#ffd23f')
    shop(110, 70, 'SPORT', '#3a6ad8'); shop(190, 60, 'LEGETØJ', '#2a8a4a')
    tx = 300
    for j in range(64):
        hw = j // 2 + 2
        if j % 14 > 11: hw -= 4
        mid.rect(tx - hw, 82 + j, 2 * hw, 1, '#2f7a3a' if (j % 3) else '#3f9a4a')
    mid.rect(tx - 4, 144, 8, 6, '#6a3a20')
    mid.sprite(['..y..', '.yyy.', 'yyyyy', '.y.y.'], tx - 2, 74, dict(y='#ffe060'), ol=False)
    for _ in range(26):
        j = r.randrange(6, 60); hw = j // 2 + 1
        mid.rect(tx + r.randint(-hw, hw - 2), 82 + j, 2, 2, r.choice(['#ff3a3a', '#ffd23f', '#3ab4ff', '#ffffff']))
    shop(350, 80, 'UDSALG', '#c8282a'); shop(440, 60, 'APOTEK', '#2a8a4a'); shop(510, 70, 'KAFFE', '#6a4a3a')
    for k in range(26):
        mid.rect(590 + k * 2, 146 - k * 2, 5, 3, '#8a9aaa'); mid.rect(590 + k * 2, 146 - k * 2, 4, 1, '#c8d4e0')
        mid.set(588 + k * 2, 138 - k * 2, '#1a1420'); mid.set(589 + k * 2, 138 - k * 2, '#1a1420')
    save_bg('center', 'mid', mid)
    g = TCan(24, 30, bg='#d8c8a8')
    for y in range(0, 30, 12):
        for x in range((y // 12 % 2) * 12, 24, 24): g.rect(x, y, 12, 12, '#e8dcc0')
    g.rect(0, 0, 24, 1, '#a89878'); g.rect(4, 5, 8, 1, '#fff6e0')
    save_bg('center', 'ground', g)
    p = TCan(24, 30, bg='#2a2430'); p.rect(0, 0, 24, 2, '#8a7a5a')
    for y in range(4, 30, 5): p.rect(0, y, 24, 2, '#3a3444'); p.rect(0, y, 24, 1, '#5a5468')
    save_bg('center', 'pit', p)

def bg_copenhill():
    sky = TCan(320, 180, bg='#0e1430'); sky.vgrad(0, 150, ['#0a0e26', '#141a3e', '#2a2a5a', '#4a3a6a'])
    r = random.Random(9)
    for _ in range(110): sky.set(r.randrange(320), r.randrange(110), '#ffffff' if r.random() < .7 else '#ffd23f')
    for j in range(-8, 9):
        for i in range(-8, 9):
            if i * i + j * j <= 64 and (i - 3) ** 2 + (j - 2) ** 2 > 40: sky.set(262 + i, 26 + j, '#fff2c8')
    sky.rect(0, 150, 320, 30, '#1a1e2e'); save_bg('copenhill', 'sky', sky)
    far = TCan(320, 180, wrap=True); x = 0
    while x < 320:
        w = r.randint(8, 18); h = r.randint(14, 46)
        if x + w > 320: w = 320 - x
        far.rect(x, 150 - h, w, h, '#1a1e3a')
        for wy in range(150 - h + 2, 148, 3):
            for wx in range(x + 1, x + w - 1, 3):
                if r.random() < .3: far.set(wx, wy, '#ffc46b')
        x += w + 1
    for (sx, sh) in [(40, 60), (150, 52), (250, 66)]:
        far.rect(sx, 150 - sh, 3, sh, '#1a1e3a'); far.rect(sx + 1, 150 - sh - 8, 1, 8, '#2a6a4a')
    save_bg('copenhill', 'far', far)
    mid = TCan(640, 180, wrap=True)
    for xx in range(640):
        for yy in range(96, 150):
            band = (yy // 5) % 2; col = '#7a828e' if band else '#8e96a2'
            k = (xx + (yy // 5) * 7) % 18
            if k == 0: col = '#2a3040'
            elif k in (1, 2) and (xx * 31 + yy * 17) % 5 < 2: col = '#ffd27a'
            mid.set(xx, yy, col)
        for yy in range(92, 96): mid.set(xx, yy, '#4a8a3a' if (xx + yy) % 5 else '#5aa04a')
    for x in range(20, 640, 80):
        mid.rect(x, 66, 2, 26, '#c8ccd4'); mid.rect(x - 3, 64, 8, 2, '#c8ccd4'); mid.rect(x - 2, 66, 6, 1, '#fff6b0')
        for j in range(8):
            for i in range(-j, j + 1):
                if (i + j) % 2 == 0: mid.set(x + 1 + i, 68 + j * 2, '#fff0c0')
    for _ in range(120):
        xx = r.randrange(640); yy = r.randrange(100, 148)
        mid.rect(xx, yy, 2, 2, r.choice(['#ff3a3a', '#ffd23f', '#3ab4ff', '#3ad46a']))
    mid.rect(470, 20, 14, 72, '#9aa2ae'); mid.rect(470, 20, 14, 2, '#c8ccd4'); mid.rect(474, 20, 2, 72, '#b4bcc8')
    for a in range(0, 360, 6):
        for rr in (10, 11): mid.set(446 + round(rr * 1.4 * math.cos(math.radians(a))), 16 + round(rr * 0.6 * math.sin(math.radians(a))), '#e8eef5')
    save_bg('copenhill', 'mid', mid)
    g = TCan(24, 30, bg='#3f8a3a')
    for y in range(0, 30, 3):
        for x in range((y // 3 % 2) * 2, 24, 4): g.set(x, y, '#4f9e48')
    g.rect(0, 0, 24, 2, '#f4f7fb')
    for x in (2, 7, 13, 19): g.set(x, 2, '#f4f7fb')
    g.rect(0, 14, 24, 16, '#6a727e')
    for y in range(15, 30, 5): g.rect(0, y, 24, 1, '#565e6a')
    save_bg('copenhill', 'ground', g)
    p = TCan(24, 30, bg='#0c1020'); p.rect(0, 0, 24, 3, '#2a3040')
    save_bg('copenhill', 'pit', p)

def build_icons():
    f = [x for x in FISHERS if x[0] == 'kasper'][0]
    rows, pal = portrait_rows(*f[1:])
    c = TCan(32, 32, bg='#14203a'); c.rect(0, 22, 32, 10, '#f2c418'); c.rect(0, 22, 32, 1, shade('#f2c418'))
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.' and ch in pal: c.set(8 + i, 8 + j, pal[ch])
    for size in (192, 512): c.im.resize((size, size), Image.NEAREST).save(os.path.join(OUT, f'icon-{size}.png'))

def build_snow():
    c = TCan(160, 180, wrap=True); r = random.Random(7)
    for _ in range(70):
        x, y = r.randrange(160), r.randrange(180); c.set(x, y, '#ffffff')
        if r.random() < .3: c.set(x + 1, y, '#ffffff')
    c.up().save(os.path.join(OUT, 'bg', 'snow.png'))


# =====================================================================
# Kortet over Amager (uden rute, knuder og navne: dem tegner spillet selv)
# =====================================================================
def build_map():
    W, H = 320, 180
    c = TCan(W, H, bg='#2f7ac8'); r = random.Random(12)
    for _ in range(900): c.rect(r.randrange(W), r.randrange(H), r.randint(2, 4), 1, r.choice(['#4a92d8', '#5aa0e0', '#2a6ab8']))
    def poly(points, col):
        im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon(points, fill=255); m = im.load()
        for y in range(H):
            for x in range(W):
                if m[x, y]: c.set(x, y, col)
        return m
    AM = [(98, 22), (112, 16), (134, 12), (150, 9), (166, 6), (180, 12), (186, 26), (190, 44), (192, 62), (198, 84), (204, 104), (212, 124),
          (222, 146), (226, 160), (214, 170), (190, 172), (160, 168), (132, 160), (110, 148), (98, 128), (92, 104), (90, 80), (94, 58), (92, 40)]
    poly([(x + (1 if x > 150 else -1) * 3, y + (3 if y > 90 else -3)) for (x, y) in AM], '#6ab4e8')
    mask = poly(AM, '#8cc85a')
    for y in range(H):
        for x in range(W):
            if mask[x, y]:
                edge = any(0 <= x + dx < W and 0 <= y + dy < H and not mask[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge: c.set(x, y, '#e8d8a0')
                elif (x * 13 + y * 7) % 23 == 0: c.set(x, y, '#7ab84a')
    for _ in range(260):
        x = r.randint(98, 160); y = r.randint(96, 160)
        if mask[x, y] and mask[min(x + 3, W - 1), y]: c.rect(x, y, 3, 2, r.choice(['#5a9a3a', '#4a8a34', '#6aa848']))
    for (x, y) in [(112, 120), (128, 138), (140, 112), (122, 104)]: c.rect(x, y, 7, 3, '#5aa0e0'); c.rect(x + 1, y - 1, 5, 1, '#5aa0e0')
    for (x, y) in [(118, 112), (134, 128), (150, 146), (108, 132), (144, 100)]: c.rect(x, y, 3, 3, '#2f6a2a'); c.set(x + 1, y - 1, '#2f6a2a')
    c.rect(0, 0, 92, 18, '#c8b898')
    for x in range(0, 92, 6):
        for y in range(0, 16, 5): c.rect(x + 1, y + 1, 4, 3, r.choice(['#c05a3a', '#8a4a34', '#d8c8a8', '#3a5a6a']))
    c.rect(0, 18, 96, 2, '#e8d8a0')
    for (sx, sh) in [(20, 10), (50, 12)]: c.rect(sx, 2, 2, sh, '#2a6a4a')
    c.rect(208, 112, 112, 2, '#e8ecf0')
    for x in range(214, 320, 10): c.rect(x, 114, 1, 3, '#8a8e9a')
    c.rect(250, 104, 2, 8, '#e8ecf0'); c.rect(256, 104, 2, 8, '#e8ecf0')
    for k in range(1, 6): c.set(250 - k * 3, 104 + k, '#c8ccd4'); c.set(257 + k * 3, 104 + k, '#c8ccd4')
    c.rect(158, 82, 38, 46, '#a8a8b0'); c.rect(162, 88, 32, 3, '#5a5a66'); c.rect(166, 96, 3, 30, '#5a5a66'); c.rect(176, 100, 16, 3, '#5a5a66')
    for x in range(163, 194, 4): c.set(x, 89, '#ffffff')
    c.sprite(PLANE, 170, 104, dict(K='#1d2a44', W='#f4f7fb', w='#5a7ab0', R='#c8323a', T='#c8323a'))
    for (x, y) in [(206, 140), (212, 144), (204, 148), (214, 150)]: c.rect(x, y, 6, 4, '#f2c24a'); c.rect(x, y - 2, 6, 2, '#b8452e')
    c.rect(104, 36, 26, 16, '#8a4a34'); c.rect(106, 38, 22, 3, '#2a4a5a'); c.rect(106, 44, 22, 3, '#2a4a5a'); c.rect(100, 54, 40, 2, '#5aa0e0')
    c.rect(142, 34, 22, 14, '#efe2c8'); c.rect(142, 34, 22, 3, '#c8282a'); c.rect(150, 42, 6, 6, '#3a5a7a')
    for x in range(158, 182):
        top = int(30 - (x - 158) * 0.75); c.rect(x, top, 1, 32 - top, '#8e96a2'); c.rect(x, top, 1, 2, '#4a8a3a')
    c.rect(180, 0, 4, 14, '#9aa2ae'); puff(c, 182, 2, 2)
    circle(c, 199, 70, 5, '#e8ecf0'); circle(c, 199, 70, 3, '#1670a8')                                                # Den Blå Planet
    c.rect(142, 80, 16, 11, '#f4f7fb'); c.rect(143, 81, 14, 9, '#3f8a3a'); c.rect(150, 81, 1, 9, '#f4f7fb')           # Sundby Idrætspark
    c.rect(108, 70, 14, 12, '#2a3a5e'); c.rect(110, 72, 10, 3, '#6ab0e8'); c.rect(110, 77, 10, 3, '#6ab0e8')              # DR Byen
    c.rect(60, 4, 22, 9, '#f2d21b'); c.rect(64, 1, 14, 4, '#f2d21b'); c.rect(66, 2, 4, 2, '#3a5a7a'); c.rect(72, 2, 4, 2, '#3a5a7a')
    c.rect(62, 12, 4, 3, '#1a1420'); c.rect(76, 12, 4, 3, '#1a1420')
    cx, cy = 300, 160
    for k in range(-8, 9): c.set(cx, cy + k, '#f6f2e8'); c.set(cx + k, cy, '#f6f2e8')
    c.rect(cx - 1, cy - 9, 3, 4, '#c0302a')
    c.up().save(os.path.join(OUT, 'bg', 'map.png'))


# =====================================================================
# Hemmeligheden: fiskeren i vildmarksbadet
# =====================================================================
def build_secret():
    W2, H2 = 192, 108
    c = TCan(W2, H2, bg='#14203a'); c.vgrad(0, 80, ['#0e1430', '#1d2a44', '#2a3a5e']); r = random.Random(4)
    for _ in range(60): c.set(r.randrange(W2), r.randrange(60), '#ffffff')
    for j in range(-7, 8):
        for i in range(-7, 8):
            if i * i + j * j <= 49 and (i - 3) ** 2 + (j - 2) ** 2 > 30: c.set(160 + i, 18 + j, '#fff2c8')
    for y in range(30, 80):
        half = int((y - 30) * 0.85) + 2
        for x in range(40 - half, 40 + half): c.set(x, y, '#e8dcc6' if x < 40 else '#c9b89a')
    c.rect(35, 62, 10, 18, '#ffb347'); c.rect(46, 22, 2, 14, '#1a1420')
    c.vgrad(80, 108, ['#e6ebf7', '#aab3d0'])
    tx, ty = 92, 66
    c.rect(tx, ty, 64, 28, '#7a4a28')
    for x in range(tx, tx + 64, 6): c.rect(x, ty, 1, 28, '#5a3418')
    for yy in (ty + 6, ty + 20): c.rect(tx, yy, 64, 2, '#3a3a44')
    c.rect(tx - 2, ty - 3, 68, 4, '#9a6a3a'); c.rect(tx, ty - 2, 64, 3, '#5aa0d8')
    c.rect(tx + 66, ty + 18, 10, 10, '#3a3a44'); c.rect(tx + 68, ty + 12, 4, 6, '#3a3a44'); c.rect(tx + 68, ty + 22, 6, 4, '#ff8a3a')
    for k, (dx, dy) in enumerate([(8, -10), (20, -16), (34, -12), (46, -18), (56, -11), (28, -24), (44, -28)]): puff(c, tx + dx, ty + dy, 4 - k // 3, '#e8eef5', '#b8c4d4')
    rows, pal = portrait_rows('#f4f1ea', '#f4f1ea', '#f2c418', '#f0b48c', False, True, False)
    for j, row in enumerate(rows[:12]):
        for i, ch in enumerate(row):
            if ch != '.': c.set(tx + 22 + i, ty - 15 + j, pal[ch])
    c.sprite(trophy(), tx + 40, ty - 38, P)
    c.rect(tx + 38, ty - 18, 3, 16, '#f0b48c'); c.rect(tx + 41, ty - 18, 3, 3, '#f0b48c')
    c.rect(20, 86, 1, 16, '#5a3418'); c.rect(14, 86, 14, 1, '#5a3418'); c.rect(15, 88, 12, 7, '#d82a2a'); c.rect(15, 88, 12, 1, '#ffffff'); c.rect(20, 92, 2, 3, '#14203a')
    c.rect(170, 82, 14, 18, '#3ab4ff')
    for y in range(83, 100, 3): c.rect(170, y, 14, 1, '#ffffff')
    c.up().save(os.path.join(OUT, 'bg', 'secret.png'))


# =====================================================================
# Bitmapfonte (BMFont XML). Hvid skrift, valgfri mørk kant bagt ind.
# =====================================================================
CHARS = [chr(i) for i in range(32, 127)] + list('ÆØÅæøåéÉ')

def build_font(key, ttf, size, outline_col=None):
    font = ImageFont.truetype(os.path.join(HERE, 'fonts', ttf), size)
    asc, desc = font.getmetrics(); lh = asc + desc; pad = 1 if outline_col else 0
    cells = []
    for ch in CHARS:
        adv = max(1, int(round(font.getlength(ch))))
        im = Image.new('L', (adv + 4, lh), 0); d = ImageDraw.Draw(im); d.fontmode = '1'; d.text((1, 0), ch, font=font, fill=255)
        cells.append((ch, adv, im))
    cw = max(im.width for _, _, im in cells) + pad * 2; chh = lh + pad * 2; cols = 16
    sheet = Image.new('RGBA', (cols * cw, ((len(cells) + cols - 1) // cols) * chh), (0, 0, 0, 0)); spx = sheet.load()
    oc = hexc(outline_col) if outline_col else None
    xml = ['<?xml version="1.0"?>', '<font>', f'<info face="{key}" size="{size}"/>',
           f'<common lineHeight="{lh + pad}" base="{asc + pad}" scaleW="{sheet.width}" scaleH="{sheet.height}" pages="1"/>',
           f'<pages><page id="0" file="{key}.png"/></pages>', f'<chars count="{len(cells)}">']
    for n, (ch, adv, im) in enumerate(cells):
        ox, oy = (n % cols) * cw, (n // cols) * chh; m = im.load()
        if oc:
            for y in range(im.height):
                for x in range(im.width):
                    if m[x, y]:
                        for dx in (-1, 0, 1):
                            for dy in (-1, 0, 1): spx[ox + pad + x + dx, oy + pad + y + dy] = oc
        for y in range(im.height):
            for x in range(im.width):
                if m[x, y]: spx[ox + pad + x, oy + pad + y] = (255, 255, 255, 255)
        xml.append(f'<char id="{ord(ch)}" x="{ox}" y="{oy}" width="{im.width + pad * 2}" height="{chh}" xoffset="{-1 - pad}" yoffset="{-pad}" xadvance="{adv}" page="0" chnl="15"/>')
    xml += ['</chars>', '</font>']
    sheet.save(os.path.join(OUT, 'fonts', f'{key}.png'))
    open(os.path.join(OUT, 'fonts', f'{key}.xml'), 'w').write('\n'.join(xml))


if __name__ == '__main__':
    build_fishers(); build_things(); build_things_v02(); build_things_v03()
    pack_atlas(os.path.join(OUT, 'atlas.png'), os.path.join(OUT, 'atlas.json'))
    bg_dragoer(); bg_lufthavn(); bg_blaaplanet(); bg_idraetspark(); bg_faelled(); bg_dr(); bg_campus(); bg_jaguaren(); bg_center(); bg_copenhill(); build_snow()
    build_map(); build_secret(); build_icons()
    build_font('ui', 'vt323.ttf', 20); build_font('ui_o', 'vt323.ttf', 20, '#1d2a44')
    build_font('big_o', 'jersey-10.ttf', 20, '#1d2a44')
    build_font('small', 'silkscreen.ttf', 8); build_font('small_o', 'silkscreen.ttf', 8, '#1d2a44')
    print('færdig')
