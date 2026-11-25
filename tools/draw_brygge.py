#!/usr/bin/env python3
"""Tegner Islands Brygge (25/11): figurer til atlasset, baggrunde og et lille havnebad på kortet.

Kør:  python3 tools/draw_brygge.py <assets-mappe>
Lægger nye frames nederst i assets/atlas.png og atlas.json (frames, der allerede findes, tegnes om).
Alt tegnes i halv opløsning og skaleres 2x, som resten af pladsholdergrafikken.
"""
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

K = (26, 20, 32, 255)          # omrids
CLEAR = (0, 0, 0, 0)


def hx(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def outline(im, col=K):
    """Sort kant rundt om alt, der ikke er gennemsigtigt (som de andre figurer)."""
    w, h = im.size
    src = im.load()
    out = im.copy()
    o = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] and src[nx, ny] != col:
                    o[x, y] = col
                    break
    return out


def x2(im):
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


# ---------------------------------------------------------------------------
# Figurer
# ---------------------------------------------------------------------------
def boombox():
    im = Image.new('RGBA', (24, 18), CLEAR)
    d = ImageDraw.Draw(im)
    d.rectangle((7, 2, 16, 3), fill=hx('#8a92a4'))          # hank
    d.rectangle((7, 2, 7, 5), fill=hx('#8a92a4'))
    d.rectangle((16, 2, 16, 5), fill=hx('#8a92a4'))
    d.rectangle((1, 5, 22, 16), fill=hx('#3a3f4c'))         # kasse
    d.rectangle((1, 5, 22, 6), fill=hx('#5a6070'))
    for cx in (5, 18):                                      # højttalere
        d.ellipse((cx - 3, 8, cx + 3, 14), fill=hx('#8a92a4'))
        d.ellipse((cx - 2, 9, cx + 2, 13), fill=hx('#2a2e38'))
        d.point((cx, 11), fill=hx('#c8d0dc'))
    d.rectangle((9, 8, 14, 12), fill=hx('#9aa4b4'))         # kassettebånd
    d.rectangle((10, 9, 13, 11), fill=hx('#e8d070'))
    d.point((10, 10), fill=K); d.point((13, 10), fill=K)
    for i, c in enumerate(('#d8584a', '#4ac06a', '#f2c418')):   # knapper
        d.point((10 + i * 2, 14), fill=hx(c))
    d.rectangle((0, 0, 2, 0), fill=CLEAR)
    im = outline(im)
    # en tone, der flyver ud af den
    d = ImageDraw.Draw(im)
    d.rectangle((21, 0, 21, 3), fill=hx('#f2c418')); d.rectangle((19, 3, 21, 4), fill=hx('#f2c418'))
    d.point((22, 0), fill=hx('#f2c418'))
    return x2(im)


def bather(frame):
    """En festglad type i badebukser, nissehue og solbriller, med en dåsebajer. To dansetrin."""
    im = Image.new('RGBA', (24, 38), CLEAR)
    d = ImageDraw.Draw(im)
    skin, shade = hx('#f0b48c'), hx('#d08a64')
    # nissehue
    d.polygon([(8, 6), (15, 6), (13, 2), (10, 1)], fill=hx('#d8584a'))
    d.rectangle((14, 1, 16, 3), fill=hx('#d8584a')) if frame == 0 else d.rectangle((6, 2, 8, 4), fill=hx('#d8584a'))
    if frame == 0:
        d.rectangle((17, 2, 18, 3), fill=hx('#f4f1ea'))
    else:
        d.rectangle((4, 3, 5, 4), fill=hx('#f4f1ea'))
    d.rectangle((7, 6, 16, 7), fill=hx('#f4f1ea'))
    # hoved
    d.rectangle((8, 8, 15, 14), fill=skin)
    d.rectangle((8, 10, 15, 10), fill=K)                    # solbriller
    d.rectangle((9, 9, 11, 11), fill=K); d.rectangle((12, 9, 14, 11), fill=K)
    d.point((9, 9), fill=hx('#8ac8f0')); d.point((12, 9), fill=hx('#8ac8f0'))
    d.rectangle((10, 13, 13, 13), fill=hx('#7a2a2a'))       # stort grin
    # krop
    d.rectangle((11, 15, 12, 15), fill=skin)
    d.rectangle((7, 16, 16, 25), fill=skin)
    d.rectangle((14, 17, 15, 25), fill=shade)
    d.point((10, 21), fill=shade)                           # navle
    # badebukser med blomster
    d.rectangle((7, 26, 16, 30), fill=hx('#f08a2a'))
    for p in ((8, 27), (11, 28), (14, 27), (9, 29), (15, 29)):
        d.point(p, fill=hx('#f6e04a'))
    # ben og klipklapper
    if frame == 0:
        d.rectangle((8, 31, 9, 36), fill=skin); d.rectangle((14, 31, 15, 36), fill=skin)
        d.rectangle((7, 37, 10, 37), fill=hx('#3a8ad8')); d.rectangle((13, 37, 16, 37), fill=hx('#3a8ad8'))
    else:
        d.rectangle((7, 31, 8, 34), fill=skin); d.rectangle((5, 34, 7, 35), fill=skin)
        d.rectangle((14, 31, 15, 36), fill=skin)
        d.rectangle((3, 35, 6, 36), fill=hx('#3a8ad8')); d.rectangle((13, 37, 16, 37), fill=hx('#3a8ad8'))
    # arme og dåse
    if frame == 0:
        d.rectangle((5, 10, 6, 17), fill=skin)              # venstre arm op
        d.rectangle((17, 9, 18, 17), fill=skin)             # højre arm op med dåse
        d.rectangle((17, 5, 19, 9), fill=hx('#3aa8d8')); d.rectangle((17, 5, 19, 5), fill=hx('#c8d0dc'))
    else:
        d.rectangle((5, 16, 6, 23), fill=skin)              # venstre arm ned
        d.rectangle((17, 16, 20, 17), fill=skin)            # højre arm ud til siden
        d.rectangle((20, 12, 22, 16), fill=hx('#3aa8d8')); d.rectangle((20, 12, 22, 12), fill=hx('#c8d0dc'))
    return x2(outline(im))


def garland():
    """Flagguirlande mellem to snore fra loftet. Hænger lavt: slide under."""
    w, h = 44, 130
    im = Image.new('RGBA', (w, h), CLEAR)
    d = ImageDraw.Draw(im)
    rope = hx('#e8e0d0')
    d.line((1, 0, 1, h - 14), fill=rope)
    d.line((w - 2, 0, w - 2, h - 14), fill=rope)
    for x in range(1, w - 1):                                # snoren hænger lidt
        y = h - 14 + round(3 * (1 - ((x - w / 2) / (w / 2)) ** 2))
        d.point((x, y), fill=rope)
    cols = ['#d8584a', '#f2c418', '#3a8ad8', '#4ac06a', '#e86ab0', '#f08a2a']
    for i, x0 in enumerate(range(3, w - 5, 6)):
        y0 = h - 14 + round(3 * (1 - ((x0 + 2 - w / 2) / (w / 2)) ** 2)) + 1
        c = hx(cols[i % len(cols)])
        d.polygon([(x0, y0), (x0 + 4, y0), (x0 + 2, y0 + 7)], fill=c)
        d.point((x0 + 2, y0 - 1), fill=hx('#fff6b0'))        # små pærer
    return x2(im)


# ---------------------------------------------------------------------------
# Baggrunde (320x180 -> 640x360)
# ---------------------------------------------------------------------------
def dither_band(d, y0, y1, c0, c1, w=320):
    """Lodret overgang fra c0 til c1 med et simpelt ternet mønster, som de andre himle."""
    n = y1 - y0
    for i in range(n):
        t = i / max(1, n - 1)
        for x in range(w):
            pick = c1 if ((x + i) % 2 == 0 and t > 0.33) or ((x % 2 == 0 and i % 2 == 0) and t > 0.66) or t > 0.9 else c0
            d.point((x, y0 + i), fill=pick)


def sky():
    im = Image.new('RGBA', (320, 180), hx('#2a3f7a'))
    d = ImageDraw.Draw(im)
    bands = ['#2a3f7a', '#3a4f92', '#5a5aa0', '#8a64a4', '#c07a98', '#e8987a', '#f6b878', '#f8d090']
    y = 0
    hgt = [22, 18, 16, 14, 12, 10, 10, 78]
    for i, c in enumerate(bands):
        d.rectangle((0, y, 319, y + hgt[i]), fill=hx(c))
        if i + 1 < len(bands):
            dither_band(d, y + hgt[i] - 4, y + hgt[i], hx(c), hx(bands[i + 1]))
        y += hgt[i]
    # vintersol, der går ned bag byen
    d.ellipse((222, 86, 250, 114), fill=hx('#fde4a0'))
    d.ellipse((226, 90, 246, 110), fill=hx('#fff2c8'))
    rnd = random.Random(7)
    for _ in range(4):                                       # lyserøde skyer
        cx, cy = rnd.randrange(10, 300), rnd.randrange(14, 70)
        for k in range(5):
            r = rnd.randrange(4, 8)
            d.ellipse((cx + k * 6 - r, cy - r // 2, cx + k * 6 + r, cy + r // 2), fill=hx('#f6c6c0'))
        d.rectangle((cx - 4, cy + 1, cx + 30, cy + 2), fill=hx('#d89aa8'))
    for _ in range(40):                                      # et par tidlige stjerner
        x, yy = rnd.randrange(0, 320), rnd.randrange(0, 34)
        d.point((x, yy), fill=hx('#f4f1ea'))
    return x2(im)


def far():
    """Byen på den anden side af havnen (Kalvebod Brygge og indre by) og Langebro."""
    im = Image.new('RGBA', (320, 180), CLEAR)
    d = ImageDraw.Draw(im)
    rnd = random.Random(11)
    x = 0
    while x < 320:
        bw = rnd.randrange(12, 30)
        top = rnd.randrange(78, 100)
        col = rnd.choice(['#4a4a78', '#55558a', '#5e5a8e', '#46507a'])
        d.rectangle((x, top, min(319, x + bw), 116), fill=hx(col))
        d.rectangle((x, top, min(319, x + bw), top), fill=hx('#f4f7fb'))   # sne på taget
        for wy in range(top + 4, 112, 5):
            for wx in range(x + 2, min(318, x + bw - 1), 4):
                if rnd.random() < 0.35:
                    d.point((wx, wy), fill=hx('#f6d37a'))
        x += bw + rnd.randrange(0, 3)
    # et kobbergrønt tårn og en kirkespir
    d.rectangle((120, 60, 128, 100), fill=hx('#4a8a7a')); d.polygon([(118, 60), (130, 60), (124, 44)], fill=hx('#4a8a7a'))
    d.rectangle((123, 36, 125, 44), fill=hx('#f2c418'))
    d.rectangle((262, 70, 266, 100), fill=hx('#3e6e6a')); d.polygon([(260, 70), (268, 70), (264, 52)], fill=hx('#3e6e6a'))
    # vandet
    d.rectangle((0, 116, 319, 179), fill=hx('#2a5a9a'))
    for i in range(60):
        wx, wy = rnd.randrange(0, 318), rnd.randrange(118, 150)
        d.rectangle((wx, wy, wx + rnd.randrange(2, 7), wy), fill=hx('#f0a878' if wx > 200 and wx < 270 else '#4a7ab8'))
    # Langebro: lav bro med lygter og de to klapfag i midten
    d.rectangle((0, 108, 319, 111), fill=hx('#c8ccd4'))
    d.rectangle((0, 112, 319, 112), fill=hx('#8a8e9a'))
    for px in range(8, 320, 26):
        d.rectangle((px, 112, px + 3, 118), fill=hx('#8a8e9a'))
    for lx in range(4, 320, 13):
        d.rectangle((lx, 102, lx, 107), fill=hx('#3a3a4a'))
        d.point((lx, 101), fill=hx('#fff2a0'))
    d.rectangle((150, 104, 152, 111), fill=hx('#e8e8ee')); d.rectangle((170, 104, 172, 111), fill=hx('#e8e8ee'))
    return x2(im)


def mid(frame):
    """Havnebadet: trædæk på vandet, udspringstårn, livreddertårn og folk, der fester. 640x180 -> 1280x360."""
    W = 640
    im = Image.new('RGBA', (W, 180), CLEAR)
    d = ImageDraw.Draw(im)
    wood, dark, snow = hx('#a8783c'), hx('#6a4a26'), hx('#f4f7fb')
    water = hx('#2e6aaa')
    d.rectangle((0, 132, W - 1, 150), fill=water)
    rnd = random.Random(5)
    for i in range(90):
        x, y = rnd.randrange(0, W - 6), rnd.randrange(134, 150)
        d.rectangle((x, y, x + rnd.randrange(2, 6), y), fill=hx('#5a9ad8'))

    def deck(x0, x1, y):
        d.rectangle((x0, y, x1, y + 4), fill=wood)
        d.rectangle((x0, y, x1, y), fill=snow)
        d.rectangle((x0, y + 4, x1, y + 4), fill=dark)
        for px in range(x0 + 2, x1, 10):
            d.rectangle((px, y + 5, px + 1, 150), fill=dark)
        for rx in range(x0, x1 + 1, 6):                     # rækværk
            d.rectangle((rx, y - 6, rx, y - 1), fill=hx('#d8dce4'))
        d.rectangle((x0, y - 6, x1, y - 6), fill=hx('#d8dce4'))

    def pool(x0, x1):
        d.rectangle((x0, 128, x1, 136), fill=hx('#4aa0d8'))
        d.rectangle((x0, 128, x1, 128), fill=hx('#8ad0f0'))

    for base in (0, 320):                                    # to ens halvdele, så laget kan gentages
        deck(base + 10, base + 140, 124)
        pool(base + 30, base + 120)
        deck(base + 30, base + 120, 136)
        # udspringstårn som en skibsstævn
        tx = base + 150
        d.polygon([(tx, 140), (tx + 26, 140), (tx + 20, 70), (tx + 6, 70)], fill=hx('#6a7890'))
        d.rectangle((tx + 4, 70, tx + 30, 73), fill=wood); d.rectangle((tx + 4, 70, tx + 30, 70), fill=snow)
        d.rectangle((tx + 2, 98, tx + 34, 101), fill=wood); d.rectangle((tx + 2, 98, tx + 34, 98), fill=snow)
        for ly in range(76, 138, 4):
            d.rectangle((tx + 9, ly, tx + 17, ly), fill=hx('#c8ccd4'))
        d.rectangle((tx + 30, 64, tx + 32, 69), fill=hx('#d8584a'))   # flag
        # livreddertårn som en skorsten
        lx = base + 220
        d.rectangle((lx, 96, lx + 16, 124), fill=hx('#e8e4dc'))
        d.rectangle((lx, 104, lx + 16, 108), fill=hx('#d8584a'))
        d.rectangle((lx - 2, 94, lx + 18, 96), fill=hx('#3a3f4c'))
        d.rectangle((lx + 4, 98, lx + 12, 102), fill=hx('#3a5a7a'))
        deck(base + 196, base + 300, 124)
        # redningskrans
        d.ellipse((base + 260, 112, base + 268, 120), fill=hx('#f08a2a'))
        d.ellipse((base + 262, 114, base + 266, 118), fill=CLEAR)
        # kulørte lamper hen over dækket
        for x in range(base + 10, base + 300, 4):
            y = 104 + round(5 * abs(((x - base) % 60) - 30) / 30)
            d.point((x, y), fill=hx('#3a3a4a'))
            if x % 8 == 2:
                d.point((x, y + 1), fill=hx(['#f2c418', '#d8584a', '#4ac06a', '#3a8ad8'][(x // 8) % 4]))
        # små festaber på dækket: armene skifter mellem op og ned (to billeder)
        for i, px in enumerate(range(base + 40, base + 130, 16)):
            body = ['#f0b48c', '#d89a70', '#c8805a'][i % 3]
            d.rectangle((px, 116, px + 2, 123), fill=hx(body))
            d.rectangle((px, 113, px + 2, 115), fill=hx(body))
            d.rectangle((px, 120, px + 2, 121), fill=hx(['#f08a2a', '#3a8ad8', '#e86ab0'][i % 3]))
            up = (i + frame) % 2 == 0
            if up:
                d.point((px - 1, 112), fill=hx(body)); d.point((px + 3, 112), fill=hx(body))
                d.point((px - 1, 113), fill=hx(body)); d.point((px + 3, 113), fill=hx(body))
            else:
                d.point((px - 1, 117), fill=hx(body)); d.point((px + 3, 117), fill=hx(body))
        # en boomblaster på dækket og toner i luften
        d.rectangle((base + 250, 119, base + 258, 123), fill=hx('#3a3f4c'))
        nx = base + 254 + (4 if frame else 0)
        d.rectangle((nx, 108 - frame * 2, nx, 112 - frame * 2), fill=hx('#f2c418'))
        d.point((nx + 1, 108 - frame * 2), fill=hx('#f2c418'))
    return x2(im)


def ground():
    """Kajkant af granit med sne og en bred træbrygge nedenunder. 24x30 -> 48x60."""
    im = Image.new('RGBA', (24, 30), hx('#a8783c'))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 23, 1), fill=hx('#f4f7fb'))
    d.rectangle((0, 2, 23, 5), fill=hx('#a8acb6'))
    d.rectangle((0, 5, 23, 5), fill=hx('#7a7e8a'))
    d.rectangle((11, 2, 11, 4), fill=hx('#7a7e8a'))
    for y in (11, 17, 23, 29):
        d.rectangle((0, y, 23, y), fill=hx('#7a5428'))
    for (x, y) in ((6, 6), (18, 12), (3, 18), (14, 24)):
        d.rectangle((x, y, x, y + 4), fill=hx('#7a5428'))
    for (x, y) in ((9, 8), (20, 20), (4, 26)):
        d.point((x, y), fill=hx('#8a6030'))
    d.point((15, 14), fill=hx('#c8945a')); d.point((2, 9), fill=hx('#c8945a'))
    return x2(im)


def pit():
    """Havnevand under kajen. 24x30 -> 48x60."""
    im = Image.new('RGBA', (24, 30), hx('#2e6aaa'))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 23, 4), fill=hx('#1a3a6a'))
    d.rectangle((0, 5, 23, 5), fill=hx('#6aaae0'))
    for (x, y, w) in ((3, 10, 6), (14, 14, 5), (6, 20, 4), (16, 24, 6), (2, 27, 5)):
        d.rectangle((x, y, x + w, y), fill=hx('#4a8ad0'))
    return x2(im)


# ---------------------------------------------------------------------------
# Kortet: et lille havnebad ved vestkysten (spilpixels)
# ---------------------------------------------------------------------------
def draw_map(path):
    m = Image.open(path).convert('RGBA')
    d = ImageDraw.Draw(m)
    # trædæk ude i vandet nordvest for Søndre Campus
    x0, y0 = 160, 74
    d.rectangle((x0, y0, x0 + 18, y0 + 10), fill=hx('#a8783c'))
    d.rectangle((x0 + 2, y0 + 2, x0 + 16, y0 + 8), fill=hx('#5ab0e8'))
    d.rectangle((x0 + 8, y0 + 2, x0 + 9, y0 + 8), fill=hx('#a8783c'))
    d.rectangle((x0 + 18, y0 + 4, x0 + 24, y0 + 6), fill=hx('#a8783c'))   # gangbro ind til land
    d.rectangle((x0 + 14, y0 - 8, x0 + 17, y0), fill=hx('#e8e4dc'))         # udspringstårn
    d.rectangle((x0 + 14, y0 - 8, x0 + 19, y0 - 7), fill=hx('#d8584a'))
    m.save(path)


def main():
    assets = Path(sys.argv[1] if len(sys.argv) > 1 else 'assets')
    frames = {
        'obst/boombox': boombox(),
        'enemy/bather0': bather(0),
        'enemy/bather1': bather(1),
        'obst/garland': garland(),
    }
    atlas_png, atlas_json = assets / 'atlas.png', assets / 'atlas.json'
    atlas = Image.open(atlas_png).convert('RGBA')
    meta = json.loads(atlas_json.read_text())
    for k in frames:
        meta['frames'].pop(k, None)
    # læg de nye figurer på en ny række nederst
    pad = 2
    y = atlas.height + pad
    rowh = max(f.height for f in frames.values())
    width = max(atlas.width, pad + sum(f.width + pad for f in frames.values()))
    out = Image.new('RGBA', (width, y + rowh + pad), CLEAR)
    out.paste(atlas, (0, 0))
    x = pad
    for k, f in frames.items():
        out.paste(f, (x, y))
        meta['frames'][k] = {
            'frame': {'x': x, 'y': y, 'w': f.width, 'h': f.height}, 'rotated': False, 'trimmed': False,
            'spriteSourceSize': {'x': 0, 'y': 0, 'w': f.width, 'h': f.height}, 'sourceSize': {'w': f.width, 'h': f.height},
        }
        x += f.width + pad
    meta['meta']['size'] = {'w': out.width, 'h': out.height}
    out.save(atlas_png, optimize=True)
    atlas_json.write_text(json.dumps(meta, indent=1, ensure_ascii=False))

    bg = assets / 'bg'
    sky().save(bg / 'brygge_sky.png', optimize=True)
    far().save(bg / 'brygge_far.png', optimize=True)
    mid(0).save(bg / 'brygge_mid.png', optimize=True)
    mid(1).save(bg / 'brygge_mid2.png', optimize=True)
    ground().save(bg / 'brygge_ground.png', optimize=True)
    pit().save(bg / 'brygge_pit.png', optimize=True)
    if '--map' in sys.argv:
        draw_map(bg / 'map.png')
    print('Islands Brygge tegnet i', assets)


if __name__ == '__main__':
    main()
