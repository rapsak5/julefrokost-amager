"""Pixel-tegnebibliotek til Julefrokost på Amager. Bruges af build_assets.py."""
import sys
from PIL import Image
import random, math

def hexc(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (255,)

# ---------- sprites (fills only; outline added automatically) ----------
BODY = [
"........YYYY....",
".......YYYYYY...",
".......YYYYYY...",
"......yyyyyyyyy.",
".......SSSSSS...",
".......SSSSBSS..",
".......SSSSSSR..",
"......WWWSSWWP..",
"......WWWWWWWPPP",
"......WWWWWWWPP.",
".....YYWWWWWYY..",
"....YYYYWWWYYYY.",
"....YYYYYCCYYYY.",
"....YYyYYYYYYY..",
"....YYyYYYYYYY..",
"....YYyYYYYYYY..",
"....yyyyyyyyyy..",
]
LEGS_RUN = [".....DD...DD....", "....DD.....DD...", "...bbb.....bbb.."]
LEGS_STEP = ["......DDDD......", "......DD.DD.....", ".....bbb.bbb...."]
LEGS_JUMP = [".....DDDDDD.....", "....bbb..bbb....", "................"]

TROPHY = [
".GGGG.",
"GGGGGG",
"gGGGGg",
".gGGg.",
"..Gg..",
".GGGG.",
]

def blank(w, h): return [['.'] * w for _ in range(h)]
def paste(g, src, x, y):
    for j, row in enumerate(src):
        for i, c in enumerate(row):
            if c != '.' and 0 <= y + j < len(g) and 0 <= x + i < len(g[0]):
                g[y + j][x + i] = c

def fisher(pose='run'):
    legs = {'run': LEGS_RUN, 'step': LEGS_STEP, 'jump': LEGS_JUMP, 'swing': LEGS_STEP}[pose]
    if pose == 'swing':
        g = blank(24, 21)
        paste(g, BODY, 0, 1); paste(g, legs, 0, 18)
        # front arm forward
        for x in range(13, 17): g[13][x] = 'Y'; g[14][x] = 'y'
        g[13][17] = 'S'; g[14][17] = 'S'
        paste(g, [r for r in TROPHY], 17, 9)
        return g
    g = blank(16, 26)
    paste(g, TROPHY, 0, 0)
    for y in (6, 7): g[y][2] = g[y][3] = 'S'
    for y in range(8, 16): g[y][2] = g[y][3] = 'Y'
    g[15][4] = 'Y'; g[16][3] = 'Y'
    paste(g, BODY, 0, 6); paste(g, legs, 0, 23)
    return g

PLANE = [
".....................TT.",
"....................TTT.",
"..WWWWWWWWWWWWWWWWWWWTT.",
".WWwWwWwWwWwWwWwWWWWWWW.",
"WWWWWWWWWWWWWWWWWWWWWWWW",
".RRRRRRRRRRRRRRRRRRRRRR.",
"..WWWWWWWWWWWWWWWWWWWW..",
"........WWWWWW..........",
"..........WWW...........",
]
BOTTLE = ["..CC..", "..NN..", "..NN..", ".NNNN.", "NNNNNN", "NLLLLN", "NLLLLN", "NLLLLN", "NNNNNN", "NNNNNN", ".NNNN."]
HEART = [".HH.HH.", "HHHHHHH", "HHHHHHH", ".HHHHH.", "..HHH..", "...H..."]
RAABER = [
"....QQQQ....",
"...QQQQQQ...",
"..qqqqqqqq..",
"...SSSSSS...",
"...SKSSKS...",
"...SSSSSS...",
"...SSMMSS..S",
"....SMMS...S",
"..JJJJJJJJJS",
".JJJJJJJJJJ.",
"SJJJJJJJJ...",
"SJJJJJJJJ...",
".JJJJJJJJ...",
".JJJJJJJJ...",
"..DDD.DDD...",
"..DDD.DDD...",
"..DDD.DDD...",
".bbbb.bbbb..",
]
BOX = ["...hhhh...", "..h....h..", "..h....h..", "AAAAAAAAAA", ".AAAZZAAA.", ".AAZAAZAA.", "..AAZZAA..", "..AAAAAA..", "...AAAA..."]
TAXI = [
"........TTT.........",
"......KKKKKKKK......",
".....KwwwKwwwwK.....",
"....KwwwwKwwwwwK....",
"XXXXXXXXXXXXXXXXXXXX",
"XXXXXXXXXXXXXXXXXXXl",
"XXXXXXXXXXXXXXXXXXXX",
"..OOO........OOO....",
"..OOO........OOO....",
]
CRATE = ["RRRRRRRRRRRR", "R.N.N.N.N..R", "RNNNNNNNNNNR", "RRRRRRRRRRRR", "R..........R", "RRRRRRRRRRRR"]

def bike():
    g = blank(22, 13)
    def circ(cx, cy, r):
        for a in range(0, 360, 6):
            x = round(cx + r * math.cos(math.radians(a))); y = round(cy + r * math.sin(math.radians(a)))
            if 0 <= y < 13 and 0 <= x < 22: g[y][x] = 'O'
    circ(4, 8, 4); circ(17, 8, 4)
    for (x0, y0, x1, y1) in [(4, 8, 9, 3), (9, 3, 15, 3), (9, 3, 11, 8), (11, 8, 15, 3), (11, 8, 4, 8), (15, 3, 17, 8), (15, 3, 15, 1)]:
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            g[round(y0 + (y1 - y0) * t / n)][round(x0 + (x1 - x0) * t / n)] = 'F'
    g[1][14] = g[1][16] = 'F'; g[2][8] = g[2][9] = g[2][10] = 'K'
    return g

def tent():
    w, h = 40, 26; g = blank(w, h)
    for y in range(4, h):
        half = int((y - 4) * 0.9) + 2
        for x in range(20 - half, 20 + half):
            if 0 <= x < w: g[y][x] = 'U' if x < 20 else 'u'
    for y in range(15, h):
        for x in range(17, 24): g[y][x] = 'I'
    for y in range(0, 10): g[y][27] = 'K'
    g[0][26] = g[0][28] = 'K'
    return g

def tostr(g): return [''.join(r) for r in g]

def outline(rows, ocol='K'):
    h = len(rows); w = len(rows[0])
    g = blank(w + 2, h + 2)
    paste(g, rows, 1, 1)
    out = [r[:] for r in g]
    for y in range(h + 2):
        for x in range(w + 2):
            if g[y][x] == '.':
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w + 2 and 0 <= yy < h + 2 and g[yy][xx] not in '.':
                        out[y][x] = '#'; break
    return [''.join(r) for r in out]

# ---------- canvas ----------
class Can:
    def __init__(s, w, h, bg):
        s.w, s.h = w, h; s.im = Image.new('RGBA', (w, h), hexc(bg)); s.px = s.im.load()
    def set(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h: s.px[x, y] = hexc(c) if isinstance(c, str) else c
    def rect(s, x, y, w, h, c):
        for j in range(h):
            for i in range(w): s.set(x + i, y + j, c)
    def sprite(s, rows, x, y, pal, flip=False, ol=True):
        if ol: rows = outline(rows)
        for j, r in enumerate(rows):
            if flip: r = r[::-1]
            for i, ch in enumerate(r):
                if ch == '.': continue
                key = 'K' if ch == '#' else ch
                if key in pal and pal[key]: s.set(x + i, y + j, pal[key])
    def vgrad(s, y0, y1, cols, dither=True):
        n = len(cols) - 1
        for y in range(y0, y1):
            t = (y - y0) / max(1, (y1 - y0 - 1)) * n
            i = min(int(t), n - 1); f = t - i
            for x in range(s.w):
                th = ((x % 2) * 2 + (y % 2)) / 4.0 + 0.125 if dither else 0.5
                s.set(x, y, cols[i + 1] if f > th else cols[i])
    def text(s, txt, x, y, c, scale=1):
        cx = x
        for ch in txt:
            g = FONT.get(ch, FONT[' '])
            for j, r in enumerate(g):
                for i, b in enumerate(r):
                    if b == '1': s.rect(cx + i * scale, y + j * scale, scale, scale, c)
            cx += (len(g[0]) + 1) * scale
    def save(s, path, k):
        s.im.resize((s.w * k, s.h * k), Image.NEAREST).save(path)

FONT = {
' ': ['000', '000', '000', '000', '000'],
'A': ['010', '101', '111', '101', '101'], 'B': ['110', '101', '110', '101', '110'],
'E': ['111', '100', '110', '100', '111'], 'F': ['111', '100', '110', '100', '100'],
'G': ['011', '100', '101', '101', '011'], 'I': ['111', '010', '010', '010', '111'],
'K': ['101', '101', '110', '101', '101'], 'L': ['100', '100', '100', '100', '111'],
'R': ['110', '101', '110', '101', '101'], 'S': ['011', '100', '010', '001', '110'],
'T': ['111', '010', '010', '010', '010'], 'U': ['101', '101', '101', '101', '111'],
'X': ['101', '101', '010', '101', '101'], 'Å': ['010', '010', '101', '111', '101'],
'!': ['1', '1', '1', '0', '1'], 'H': ['101', '101', '111', '101', '101'], 'Ø': ['011', '101', '111', '101', '110'],
}


# ---------- grundpalet ----------
BASE = dict(Y='#f2c418', y='#c98f0c', S='#f0b48c', B='#3a6fd8', R='#d8584a', W='#f4f1ea', P='#6b3f22',
            C='#5b8fd6', D='#2e3b55', b='#1b1b22', G='#f6c945', g='#b8862a', K='#1a1420',
            w='#4a6a9a', T='#c03838', N='#2f8a3a', L='#efe3b0', H='#e83a4a',
            Q='#8a2a2a', q='#5a1a1a', M='#3a0d10', J='#5a6a3a', A='#f5f0e6', Z='#d03030', h='#888888',
            X='#f2d21b', l='#fff6a0', O='#222222', F='#c03030', U='#e9dcc3', u='#c9b89a', I='#ffb347')
BASE['_W'] = '#e8eef5'  # plane white (separate from beard)



W, H = 320, 180

# ---------- full 3x5 font ----------
FONT.update({
 'A': ['010', '101', '111', '101', '101'], 'B': ['110', '101', '110', '101', '110'], 'C': ['011', '100', '100', '100', '011'],
 'D': ['110', '101', '101', '101', '110'], 'E': ['111', '100', '110', '100', '111'], 'F': ['111', '100', '110', '100', '100'],
 'G': ['011', '100', '101', '101', '011'], 'H': ['101', '101', '111', '101', '101'], 'I': ['111', '010', '010', '010', '111'],
 'J': ['001', '001', '001', '101', '010'], 'K': ['101', '101', '110', '101', '101'], 'L': ['100', '100', '100', '100', '111'],
 'M': ['10001', '11011', '10101', '10001', '10001'], 'N': ['1001', '1101', '1011', '1001', '1001'], 'O': ['010', '101', '101', '101', '010'],
 'P': ['110', '101', '110', '100', '100'], 'Q': ['010', '101', '101', '110', '011'], 'R': ['110', '101', '110', '101', '101'],
 'S': ['011', '100', '010', '001', '110'], 'T': ['111', '010', '010', '010', '010'], 'U': ['101', '101', '101', '101', '111'],
 'V': ['101', '101', '101', '101', '010'], 'W': ['10001', '10001', '10101', '11011', '10001'], 'X': ['101', '101', '010', '101', '101'],
 'Y': ['101', '101', '010', '010', '010'], 'Z': ['111', '001', '010', '100', '111'], 'Æ': ['0111', '1010', '1111', '1010', '1011'],
 'Ø': ['011', '101', '111', '101', '110'], 'Å': ['010', '000', '111', '101', '101'], '?': ['110', '001', '010', '000', '010'],
 '!': ['1', '1', '1', '0', '1'], '.': ['0', '0', '0', '0', '1'], ' ': ['00', '00', '00', '00', '00'], '-': ['000', '000', '111', '000', '000'],
 '0': ['111', '101', '101', '101', '111'], '1': ['010', '110', '010', '010', '111'], '2': ['110', '001', '010', '100', '111'],
 '3': ['110', '001', '010', '001', '110'], '4': ['101', '101', '111', '001', '001'], '5': ['111', '100', '110', '001', '110'],
 '6': ['011', '100', '111', '101', '111'], '7': ['111', '001', '010', '010', '010'], '8': ['111', '101', '111', '101', '111'], '9': ['111', '101', '111', '001', '110'],
})

def text_w(t, scale=1):
    return sum((len(FONT.get(ch, FONT[' '])[0]) + 1) * scale for ch in t) - scale

def otext(c, t, x, y, col='#ffffff', oc='#1d2a44', scale=1):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy: c.text(t, x + dx, y + dy, oc, scale)
    c.text(t, x, y, col, scale)

# ---------- palette ----------
P = dict(BASE)
P.update(K='#1a1420', h='#fff2b0', E='#f6d37a', D='#5a3420', r='#d82a2a', v='#ffffff',
         a='#8a8e9a', n='#3aa86a', m='#8a4ab0', e='#d83030', o='#e87a6a', A2='#b8bcc8')
DUE_P = dict(K='#1a1420', A='#b4b8c4', a='#7a7e8c', n='#3aa86a', m='#8a4ab0', e='#ff3030', o='#e8806a')

# ---------- giant trophy ----------
TROPHY_BIG = [
"....hGGGGGGGGGGg....",
"...hhGGGGGGGGGGgg...",
"GGG.hGGGGGGGGGGg.GGG",
"G...hGGGGGGGGGGg...G",
"G...hGGGGGGGGGGg...G",
"G...hGGGGGGGGGgg...G",
".G...hGGGGGGGGg...G.",
"..GG.hGGGGGGGGg.GG..",
"....GhGGGGGGGgg.....",
".....hGGGGGGGg......",
"......hGGGGGg.......",
".......hGGGg........",
"........GGg.........",
"........GGg.........",
".......GGGgg........",
"........GGg.........",
".....hGGGGGGGg......",
"....DDDDDDDDDDD.....",
"....DDDEEEEEDDD.....",
"....DDDEEEEEDDD.....",
"...DDDDDDDDDDDDD....",
]
def trophy():
    g = [list(r) for r in TROPHY_BIG]
    # ribbon from right handle
    for y in range(7, 16):
        g[y][17] = 'r' if (y // 2) % 2 == 0 else 'v'
        if y > 9: g[y][18] = 'r' if (y // 2) % 2 else 'v'
    return [''.join(r) for r in g]

def rot_cw(rows):
    h = len(rows); w = len(rows[0])
    return [''.join(rows[h - 1 - j][i] for j in range(h)) for i in range(w)]

def fisher_big(pose='run'):
    T = trophy()
    if pose in ('run', 'idle'):
        g = blank(22, 44)
        paste(g, T, 1, 0)
        for y in range(21, 34):
            g[y][5] = g[y][6] = 'Y'; g[y][15] = g[y][16] = 'Y'
        for y in (21, 22):
            g[y][5] = g[y][6] = 'S'; g[y][15] = g[y][16] = 'S'
        g[33][7] = 'Y'; g[34][7] = 'Y'
        paste(g, BODY, 2, 23)
        paste(g, LEGS_RUN if pose == 'run' else LEGS_STEP, 2, 40)
        return tostr(g)
    if pose == 'pogo':
        g = blank(24, 44)
        paste(g, BODY, 3, 0)
        for x in range(1, 6): g[12][x] = 'Y'
        g[11][0] = g[12][0] = 'S'
        for x in range(17, 22): g[12][x] = 'Y'
        g[11][22] = g[12][22] = 'S'
        paste(g, LEGS_JUMP, 3, 17)
        paste(g, T, 2, 22)
        return tostr(g)
    if pose == 'swing':
        R = rot_cw(T)
        g = blank(16 + len(R[0]) + 1, 30)
        paste(g, BODY, 0, 8)
        for x in range(13, 17): g[21][x] = 'Y'; g[22][x] = 'y'
        g[21][17] = g[22][17] = 'S'
        paste(g, R, 18, 12 - 0)
        paste(g, LEGS_STEP, 0, 25)
        return tostr(g)

FACE = [
"....YYYYYYYY....",
"...YYYYYYYYYY...",
"...YYYYYYYYYY...",
".yyyyyyyyyyyyyy.",
"..SSSSSSSSSSSS..",
"..SWWWSSSSWWWS..",
"..SSBKSSSSBKSS..",
"..SSSSSRRSSSSS..",
"..sSSSSRRSSSSs..",
"..WWWWWWWWWWWW..",
".WWWWWMMMWWWWPP.",
".WWWWWWWWWWWWPPP",
"..WWWWWWWWWWWPP.",
"...WWWWWWWWWW...",
]
FACE_P = dict(P, s='#d89070', M='#7a2a2a')

DUE = [
"..aa........",
".aAAa.......",
"oAeAa.......",
".anmAaaaa...",
"..nmAAAAAaa.",
"..aAAAAAAAAa",
"...aAAAAaaaa",
"....aaaaa.aa",
".....o..o...",
]
DUE_FLY = [
"......aa....",
".....aAAa...",
"..aa.aAAa...",
".aAAaAAAa...",
"oAeAAAAAAaa.",
".anmAAAAAAAa",
"..aaaaaaaaa.",
]
SHOT = ["hwwwwwh", "wRRRRRw", "wRRRRRw", ".wRRRw.", ".wRRRw.", "..www..", ".wwwww."]
SHOT_P = dict(K='#1a1420', w='#bfe0f4', h='#ffffff', R='#c8282a')
QUIZ = [
"QQQQQQQQQQQQ",
"QqQQQQQQQQqQ",
"QQQQ!!!!QQQQ",
"QQQ!!QQ!!QQQ",
"QQQQQQQ!!QQQ",
"QQQQQ!!!QQQQ",
"QQQQQ!!QQQQQ",
"QQQQQQQQQQQQ",
"QQQQQ!!QQQQQ",
"QqQQQQQQQQqQ",
"qqqqqqqqqqqq",
]
QUIZ_P = dict(K='#5a3410', Q='#f6b830', q='#c0801a', **{'!': '#fff6d0'})
KUFFERT = ["....KKKK....", "...K....K...", "RRRRRRRRRRRR", "RrRRRRRRRRrR", "RRRRRRRRRRRR", "RRwwwwwwwwRR", "RRRRRRRRRRRR", "RrRRRRRRRRrR", "RRRRRRRRRRRR", ".O........O."]
KUF_P = dict(K='#1a1420', R='#3a6ad8', r='#2a4aa8', w='#f6d37a', O='#222222')
BIBLIO = [
"....HHH.....",
"...HHHHH....",
"...HHHHH....",
"...SSSSS....",
"..SgSSgSS...",
"...SSSSS....",
"...SSSSSS...",
"....SSS..S..",
"..JJJJJJJS..",
".JJJJJJJJ...",
".JJJJJJJJ...",
".JJJJJJJJ...",
"..JJJJJJ....",
"..DDDDDD....",
"..DDDDDD....",
"..DD..DD....",
"..bb..bb....",
]
BIB_P = dict(P, H='#6a4a3a', g='#1a1420', J='#8a2a4a', D='#2a2a3a', b='#1a1420')
SKI = [
"....RRR.......",
"...RRRRR......",
"...SSSS.......",
"..SSSSS..k....",
"..JJJJJJJk....",
".JJJJJJJ.k....",
"JJJJJJJ..k....",
".JJJJJ...k....",
"..DDDDD..k....",
"..DD.DD.......",
".DD...DD......",
"kkkkkkkkkkkkk.",
]
SKI_P = dict(P, R='#e83a3a', J='#2aa8d8', D='#2a2a3a', k='#3a3a44')
BOOK = ["a....a", "aa..aa", ".BWWB.", "BWWWWB", ".BBBB."]
BOOK_P = dict(K='#1a1420', a='#ffffff', B='#a83a2a', W='#f6f0e0')
CART = ["K..........", "KKKKKKKKKKK", ".KgKgKgKgK.", ".KKKKKKKKK.", "..KgKgKgK..", "..KKKKKKK..", "...K...K...", "..OO...OO.."]
CART_P = dict(K='#8a9aaa', g='#c8d4e0', O='#1a1420')
HEART9 = [".HHH.HHH.", "HhhHHHHHH", "HhHHHHHHH", "HHHHHHHHH", ".HHHHHHH.", "..HHHHH..", "...HHH...", "....H...."]
BOT_P = dict(K='#1a1420', C='#f6c945', N='#2f8a3a', L='#efe3b0')

def scaled(rows, k):
    return [''.join(ch * k for ch in r) for r in rows for _ in range(k)]

# ---------- shared drawing ----------
def shade(hx, f=0.8):
    t = hexc(hx); return '#%02x%02x%02x' % tuple(int(v * f) for v in t[:3])
def light(hx):
    t = hexc(hx); return '#%02x%02x%02x' % tuple(min(255, int(v * 1.12 + 10)) for v in t[:3])

def cloud(c, x, y, s=1.0, col='#ffffff', sh='#d6e8f8'):
    for (dx, dy, rad) in [(0, 4, 7), (8, 0, 9), (18, 3, 8), (26, 6, 6), (-6, 8, 5)]:
        rad = int(rad * s)
        for j in range(-rad, rad + 1):
            for i in range(-rad, rad + 1):
                if i * i + j * j <= rad * rad:
                    c.set(x + int(dx * s) + i, y + int(dy * s) + j, col if j < rad * 0.3 else sh)
    c.rect(x - int(10 * s), y + int(11 * s), int(44 * s), int(3 * s), sh)

def window(c, x, y, star=False, lit=False, frame='#f6f2e8', glass='#3a5a7a'):
    c.rect(x - 1, y - 1, 12, 15, frame); c.rect(x, y, 10, 13, '#ffcf6a' if lit else glass)
    c.rect(x + 4, y, 2, 13, frame); c.rect(x, y + 6, 10, 1, frame)
    c.set(x + 1, y + 1, '#a8d0f0'); c.set(x + 7, y + 1, '#a8d0f0')
    c.rect(x - 2, y + 13, 14, 2, '#d8d0c0')
    if star:
        for (dx, dy) in [(2, 2), (1, 3), (2, 3), (3, 3), (2, 4), (0, 3), (4, 3), (2, 1), (2, 5)]: c.set(x + dx, y + dy, '#fff6b0')

def door(c, x, y, col, h=20, wreath=True):
    c.rect(x - 1, y - 1, 12, h + 1, '#f6f2e8'); c.rect(x, y, 10, h, col)
    c.rect(x + 2, y + 2, 2, 6, shade(col)); c.rect(x + 6, y + 2, 2, 6, shade(col)); c.rect(x + 2, y + 11, 6, 6, shade(col))
    c.set(x + 8, y + 10, '#e8c050')
    if wreath:
        for a in range(0, 360, 30):
            c.set(x + 5 + round(3 * math.cos(math.radians(a))), y - 6 + round(3 * math.sin(math.radians(a))), '#2f7a3a')
        c.set(x + 5, y - 3, '#d83030'); c.set(x + 4, y - 2, '#d83030'); c.set(x + 6, y - 2, '#d83030')

def house(c, x, w, top, wall, roof, base, roofh=26, chimney=True, rnd=None):
    rnd = rnd or random.Random(1)
    c.rect(x, top, w, base - top, wall)
    c.rect(x, top, 2, base - top, light(wall)); c.rect(x + w - 2, top, 2, base - top, shade(wall))
    for yy in range(top + 6, base, 6):
        for xx in range(x + 3, x + w - 3):
            if (xx + yy) % 9 == 0: c.set(xx, yy, shade(wall))
    for j in range(roofh):
        inset = int((roofh - j) * 0.55); y = top - roofh + j
        c.rect(x - 3 + inset, y, w + 6 - 2 * inset, 1, roof if j % 4 else shade(roof))
        if j % 4 == 2:
            for xx in range(x - 3 + inset, x + w + 3 - inset, 5): c.set(xx + (j // 4) % 2 * 2, y, shade(roof))
    c.rect(x - 4, top - 1, w + 8, 2, shade(roof))
    rid = top - roofh; inset = int(roofh * 0.55)
    c.rect(x - 3 + inset, rid - 1, w + 6 - 2 * inset, 3, '#ffffff')
    c.rect(x - 4, top - 3, w + 8, 2, '#ffffff')
    for xx in range(x - 4, x + w + 4, 3): c.set(xx, top - 1 + (xx % 2), '#e6eef8')
    if chimney:
        cx = x + w - 16
        c.rect(cx, rid - 10, 8, 14, '#c0563a'); c.rect(cx, rid - 10, 8, 1, '#8a3a26')
        for yy in range(rid - 8, rid + 4, 3): c.rect(cx, yy, 8, 1, '#a84a30')
        c.rect(cx - 1, rid - 13, 10, 3, '#ffffff')
    return rid

def lights_string(c, x0, x1, y0, sag=6):
    cols = ['#ff3a3a', '#ffd23f', '#3ad46a', '#3ab4ff']
    for x in range(x0, x1 + 1):
        t = (x - x0) / max(1, (x1 - x0)); y = int(y0 + sag * math.sin(t * math.pi))
        c.set(x, y, '#2a3a2a')
        if (x - x0) % 4 == 2: c.rect(x, y + 1, 2, 2, cols[(x // 4) % 4])

def snowfall(c, n, seed=3, ymax=180, col='#ffffff'):
    r = random.Random(seed)
    for _ in range(n):
        x, y = r.randrange(W), r.randrange(ymax)
        c.set(x, y, col)
        if r.random() < 0.3: c.set(x + 1, y, col)

def puff(c, x, y, rad, col='#f4f7fb', sh='#c8d4e0'):
    for j in range(-rad, rad + 1):
        for i in range(-rad, rad + 1):
            if i * i + j * j <= rad * rad: c.set(x + i, y + j, col if j < rad * 0.2 else sh)

# ---------- HUD ----------
def hud(c, label, beer=0.6, count='000'):
    def frame(x, y, w, h):
        c.rect(x, y, w, h, '#7a4a18'); c.rect(x + 1, y + 1, w - 2, h - 2, '#e8b040'); c.rect(x + 2, y + 2, w - 4, h - 4, '#a8701e')
        c.rect(x + 1, y + 1, w - 2, 1, '#ffe08a')
    c.rect(24, 6, 60, 13, '#7a4a18'); c.rect(25, 7, 58, 11, '#c0563a'); c.rect(25, 7, 58, 1, '#e88a5a')
    for n in range(5):
        for j, row in enumerate(HEART9):
            for i, ch in enumerate(row):
                if ch != '.': c.set(28 + n * 11 + i, 8 + j, {'H': '#e8283a', 'h': '#ff9aa0'}[ch])
    frame(4, 4, 24, 24); c.rect(7, 7, 18, 18, '#6ab0e8')
    for j, row in enumerate(FACE):
        for i, ch in enumerate(row):
            if ch != '.': c.set(8 + i, 8 + j, FACE_P[ch])
    c.rect(8, 22, 16, 3, '#f2c418')
    # trophy badge
    for j in range(-6, 7):
        for i in range(-6, 7):
            d = i * i + j * j
            if d <= 36: c.set(22 + i, 34 + j, '#7a4a18' if d > 25 else ('#c0563a' if d > 16 else '#e8b040'))
    for j, row in enumerate(["GGGGGG", "gGGGGg", ".gGGg.", "..Gg..", ".GGGG."]):
        for i, ch in enumerate(row):
            if ch != '.': c.set(19 + i, 32 + j, {'G': '#fff2b0', 'g': '#7a4a18'}[ch])
    # beer meter
    mx, my = 9, 34
    c.rect(mx - 2, my - 4, 12, 4, '#e8b040'); c.rect(mx - 1, my - 6, 10, 2, '#7a4a18')
    c.rect(mx - 2, my, 12, 40, '#7a4a18'); c.rect(mx - 1, my + 1, 10, 38, '#e8b040'); c.rect(mx, my + 2, 8, 36, '#cfe6f4')
    fill = int(36 * beer); top = my + 38 - fill
    c.rect(mx, top, 8, fill, '#f0a020'); c.rect(mx, top - 2, 8, 3, '#ffffff'); c.rect(mx, top + 1, 1, fill - 1, '#ffc860')
    for k in range(0, 36, 9): c.rect(mx + 6, my + 2 + k, 2, 1, '#7a4a18')
    c.rect(mx - 3, my + 40, 14, 4, '#e8b040'); c.rect(mx - 2, my + 44, 12, 3, '#7a4a18')
    # counter
    c.rect(258, 5, 50, 16, '#7a4a18'); c.rect(259, 6, 48, 14, '#c0563a'); c.rect(261, 7, 28, 12, '#ffffff')
    cx = 264
    for d in count:
        for j, row in enumerate(FONT[d]):
            for i, b in enumerate(row):
                if b == '1': c.rect(cx + i * 2, 8 + j * 2, 2, 2, '#c0302a')
        cx += 8
    c.sprite(BOTTLE, 292, 3, BOT_P)
    # level banner
    if label:
        tw = text_w(label)
        bx = 160 - tw // 2 - 6
        c.rect(bx, 5, tw + 12, 11, '#1d2a44'); c.rect(bx + 1, 6, tw + 10, 9, '#2f4a7a'); c.rect(bx + 1, 6, tw + 10, 1, '#4a6aa8')
        c.text(label, bx + 6, 8, '#ffffff')
