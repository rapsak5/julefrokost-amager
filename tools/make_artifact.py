#!/usr/bin/env python3
"""Laver en kopi af spillet til Claude-artifact (testversion på telefonen).

Eneste forskel fra den rigtige udgave: Phaser hentes fra et CDN i stedet for vendor/,
fordi en artifact kun må indeholde filer, vi selv har skrevet.
Kør:  python3 tools/make_artifact.py   -> dist-artifact/
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'dist-artifact')
URLS = sys.argv[1:] or ['https://cdn.jsdelivr.net/npm/phaser@4.2.1/dist/phaser.min.js', 'https://unpkg.com/phaser@4.2.1/dist/phaser.min.js']

LOADER = '''<script>
(function load(urls) {
  if (!urls.length) { document.getElementById('rotate').style.display = 'block'; document.getElementById('rotate').textContent = 'Spilmotoren kunne ikke hentes. Tjek forbindelsen og prøv igen.'; return; }
  var s = document.createElement('script');
  s.src = urls[0];
  s.onload = function () { import('./src/main.js'); };
  s.onerror = function () { load(urls.slice(1)); };
  document.head.appendChild(s);
})(%s);
</script>''' % repr(URLS).replace("'", '"')

shutil.rmtree(OUT, ignore_errors=True)
for d in ('src', 'assets'):
    shutil.copytree(os.path.join(ROOT, d), os.path.join(OUT, d))
html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
html, n = re.subn(r'<script src="vendor/phaser\.min\.js"></script>\s*<script type="module" src="src/main\.js"></script>', lambda m: LOADER, html)
assert n == 1, 'fandt ikke script-linjerne i index.html'
html = html.replace('<link rel="manifest" href="manifest.webmanifest">\n', '')
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)
print('dist-artifact klar:', sum(len(f) for _, _, f in os.walk(OUT)), 'filer')
