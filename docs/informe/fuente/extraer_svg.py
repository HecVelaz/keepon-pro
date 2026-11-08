# Extrae los SVG de la guía, les agrega las definiciones de flechas y los convierte a PNG.
import re, sys, cairosvg
html = open(sys.argv[1], encoding='utf-8').read()
markers = ''.join(re.findall(r'<marker .*?</marker>', html, re.S))
svgs = re.findall(r'<svg .*?</svg>', html, re.S)
for i, s in enumerate(svgs):
    s = s.replace("Noto Sans", "DejaVu Sans Condensed")
    s = s.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    s = re.sub(r'(<svg [^>]*>)', r'\1<defs>' + markers + '</defs><rect width="100%" height="100%" fill="white"/>', s, count=1)
    # ancho real desde viewBox para escalar a 2x
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s)
    w = float(vb.group(1))
    s = re.sub(r'(<svg [^>]*?)width="[\d.]+" height="[\d.]+"', r'\1', s, count=1)
    cairosvg.svg2png(bytestring=s.encode(), write_to=f'figs/svg_{i:02d}.png', output_width=int(w * 2))
    txt = re.sub(r'<[^>]+>', ' ', s); txt = re.sub(r'\s+', ' ', txt).strip()
    print(i, int(w), txt[:70])
