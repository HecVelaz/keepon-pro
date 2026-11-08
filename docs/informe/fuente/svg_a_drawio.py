# Convierte los diagramas SVG de la guía (docs/guia/guia_keepon.html) a archivos draw.io editables:
# rectángulos y círculos -> formas, textos -> textos, líneas y caminos abiertos -> conectores con sus flechas,
# figuras rellenas irregulares -> polígonos de draw.io (o imagen SVG si no se pueden aproximar).
# Uso: python svg_a_drawio.py <guia.html> <carpeta_salida>
import base64, html, math, re, sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

GUIA, SALIDA = sys.argv[1], sys.argv[2]
S = 1.5  # escala: draw.io trabaja mejor con letras de 12–15 px

# número de SVG en la guía -> (archivo, título)
FIGURAS = {
    0: ('01_esquema_keepon', 'Esquema de Keepon'),
    3: ('02_cadena_cinematica', 'Cadena cinemática'),
    4: ('03_diagrama_electrico', 'Diagrama eléctrico'),
    9: ('04_sesion_serie', 'Ejemplo de sesión Pi - ESP32'),
    6: ('05_cadena_de_control', 'Cadena de control de un eje'),
    13: ('06_region_torso', 'Región del torso (camisetas)'),
    12: ('07_histeresis_me_mira', 'Histéresis de ME_MIRA'),
    10: ('08_arquitectura', 'Arquitectura del software'),
    15: ('09_mirada_por_objetivo', 'Mirada por objetivo'),
    17: ('10_estados_modos', 'Diagramas de estados de los modos'),
    18: ('11_segmentos_sonido', 'Segmentos de sonido'),
    16: ('12_conflicto_arbitro', 'Ejemplo de conflicto en el árbitro'),
    # también los que están en la guía pero no en el informe v2
    1: ('13_sistema_completo', 'Sistema completo'),
    2: ('14_linea_de_tiempo', 'Línea de tiempo'),
    5: ('15_senal_pwm', 'Señal PWM de un servo'),
    7: ('16_perfil_trapezoidal', 'Perfil de velocidad trapezoidal'),
    8: ('17_estados_firmware', 'Estados del firmware'),
    11: ('18_frecuencias_percepcion', 'Frecuencias de la percepción'),
    14: ('19_pixel_a_angulo', 'Del píxel al ángulo'),
}

guia = open(GUIA, encoding='utf-8').read().replace('&nbsp;', ' ')
svgs = re.findall(r'<svg .*?</svg>', guia, re.S)


def num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def color(c):
    if c is None or c in ('none', 'transparent'):
        return 'none'
    return c


def heredar(el, padre):
    a = dict(padre)
    for k in ('font-family', 'font-size', 'font-weight', 'fill', 'stroke', 'stroke-width', 'text-anchor', 'opacity'):
        if el.get(k) is not None:
            a[k] = el.get(k)
    st = el.get('style')
    if st:
        for par in st.split(';'):
            if ':' in par:
                k, v = par.split(':', 1); a[k.strip()] = v.strip()
    return a


def tokens_path(d):
    return re.findall(r'[MLHVQZAmlhvqza]|-?\d*\.?\d+(?:e-?\d+)?', d)


def puntos_path(d):
    """Lista de subcaminos [(puntos, cerrado)]; curvas Q muestreadas, arcos a su punto final."""
    t = tokens_path(d); i = 0; cmd = None; x = y = 0.0
    subs, pts, cerrado = [], [], False
    def n():
        nonlocal i; i += 1; return float(t[i - 1])
    while i < len(t):
        if re.match(r'[A-Za-z]', t[i]):
            cmd = t[i]; i += 1
            if cmd in 'Zz':
                subs.append((pts, True)); pts = []; continue
        if cmd == 'M':
            if pts: subs.append((pts, False))
            x, y = n(), n(); pts = [(x, y)]; cmd = 'L'
        elif cmd == 'L':
            x, y = n(), n(); pts.append((x, y))
        elif cmd == 'H':
            x = n(); pts.append((x, y))
        elif cmd == 'V':
            y = n(); pts.append((x, y))
        elif cmd == 'Q':
            cx, cy, x2, y2 = n(), n(), n(), n()
            for k in range(1, 9):
                u = k / 8
                pts.append(((1-u)**2*x + 2*(1-u)*u*cx + u*u*x2, (1-u)**2*y + 2*(1-u)*u*cy + u*u*y2))
            x, y = x2, y2
        elif cmd == 'a':
            for _ in range(5): n()
            x, y = x + n(), y + n(); pts.append((x, y))
        elif cmd == 'A':
            for _ in range(5): n()
            x, y = n(), n(); pts.append((x, y))
        else:
            i += 1
    if pts: subs.append((pts, cerrado))
    return subs


class Dibujo:
    def __init__(self):
        self.celdas = []; self.n = 2

    def id(self):
        self.n += 1; return f'c{self.n}'

    def vertice(self, valor, estilo, x, y, w, h, texto=None):
        # Se guarda como objeto: al final los textos se meten dentro de la caja que los contiene.
        self.celdas.append({'valor': valor, 'estilo': estilo, 'x': x, 'y': y, 'w': w, 'h': h, 'texto': texto})

    def _vxml(self, v):
        return (f'<mxCell id="{self.id()}" value={quoteattr(v["valor"])} style={quoteattr(v["estilo"])} vertex="1" parent="1">'
                f'<mxGeometry x="{v["x"]*S:.1f}" y="{v["y"]*S:.1f}" width="{max(v["w"],1)*S:.1f}" height="{max(v["h"],1)*S:.1f}" as="geometry"/></mxCell>')

    def fusionar_textos(self):
        """Cada texto que cae dentro de una caja (rectángulo o elipse sin otras formas adentro) pasa a ser su etiqueta."""
        formas = [v for v in self.celdas if isinstance(v, dict) and v['texto'] is None and not v['estilo'].startswith('shape=image')]
        textos = [v for v in self.celdas if isinstance(v, dict) and v['texto'] is not None and not v['texto'].get('rot')]
        def dentro(t, f):
            cx, cy = t['texto']['cx'], t['texto']['cy']
            return f['x'] <= cx <= f['x'] + f['w'] and f['y'] <= cy <= f['y'] + f['h']
        def contiene_forma(f):
            return any(g is not f and g['w'] * g['h'] < f['w'] * f['h'] * 0.9 and f['x'] <= g['x'] and g['x'] + g['w'] <= f['x'] + f['w'] + 0.5
                       and f['y'] <= g['y'] and g['y'] + g['h'] <= f['y'] + f['h'] + 0.5 for g in formas)
        hojas = [f for f in formas if f['w'] > 12 and f['h'] > 10 and not contiene_forma(f)]
        asignado = {}
        for t in textos:
            cand = [f for f in hojas if dentro(t, f) and t['texto']['ancho'] <= f['w'] + 8]
            if cand:
                f = min(cand, key=lambda f: f['w'] * f['h']); asignado.setdefault(id(f), (f, []))[1].append(t)
        quitar = set()
        for f, ts in asignado.values():
            ts.sort(key=lambda t: t['texto']['cy'])
            anclas = {t['texto']['al'] for t in ts}
            al = 'center' if anclas == {'center'} else 'left'
            lineas = [f'<font style="font-size:{t["texto"]["fs"]*S:.0f}px" color="{t["texto"]["color"]}">'
                      + (f'<b>{t["valor"]}</b>' if t['texto']['negrita'] else t['valor']) + '</font>' for t in ts]
            f['valor'] = '<br>'.join(lineas)
            extra = f'align={al};verticalAlign=middle;html=1;whiteSpace=wrap;'
            if al == 'left':
                extra += f'spacingLeft={max(0, (min(t["x"] for t in ts) - f["x"]) * S):.0f};'
            if ts[0]['texto'].get('mono'): extra += 'fontFamily=Courier New;'
            f['estilo'] += extra
            quitar.update(id(t) for t in ts)
        self.celdas = [v for v in self.celdas if not (isinstance(v, dict) and id(v) in quitar)]

    def arista(self, pts, estilo):
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        medio = ''.join(f'<mxPoint x="{px*S:.1f}" y="{py*S:.1f}"/>' for px, py in pts[1:-1])
        arr = f'<Array as="points">{medio}</Array>' if medio else ''
        self.celdas.append(f'<mxCell id="{self.id()}" value="" style={quoteattr(estilo)} edge="1" parent="1">'
                           f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x0*S:.1f}" y="{y0*S:.1f}" as="sourcePoint"/>'
                           f'<mxPoint x="{x1*S:.1f}" y="{y1*S:.1f}" as="targetPoint"/>{arr}</mxGeometry></mxCell>')

    def xml(self, titulo, w, h, fondo=None):
        self.fusionar_textos()
        fondo_attr = f'background="{fondo}" ' if fondo else ''
        cuerpo = ''.join(self._vxml(v) if isinstance(v, dict) else v for v in self.celdas)
        return (f'<mxfile host="Electron" type="device"><diagram name={quoteattr(titulo)} id="d1">'
                f'<mxGraphModel dx="{int(w*S)}" dy="{int(h*S)}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
                f'fold="1" page="1" pageScale="1" {fondo_attr}pageWidth="{int(w*S)+40}" pageHeight="{int(h*S)+40}" math="0" shadow="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{cuerpo}</root></mxGraphModel></diagram></mxfile>')


def estilo_trazo(a):
    s = f"strokeColor={color(a.get('stroke'))};strokeWidth={num(a.get('stroke-width'), 1)*S:.1f};"
    if a.get('stroke-dasharray'): s += 'dashed=1;'
    if a.get('opacity'): s += f"opacity={int(num(a.get('opacity'),1)*100)};"
    return s


def flechas(el, a):
    s = 'endArrow=' + ('block;endFill=1;endSize=5;' if el.get('marker-end') else 'none;')
    s += 'startArrow=' + ('block;startFill=1;startSize=5;' if el.get('marker-start') else 'none;')
    return s


def ancho_texto(t, fs):
    return sum(0.62 if c.isupper() or c.isdigit() else 0.5 for c in t) * fs + 2


def convertir(svg_txt, titulo, fondo=None):
    svg_txt = re.sub(r'<defs>.*?</defs>', '', svg_txt, flags=re.S)
    raiz = ET.fromstring(svg_txt)
    vb = [float(v) for v in raiz.get('viewBox').split()]
    dib = Dibujo()
    base = heredar(raiz, {'font-size': '10', 'fill': '#1f2a27'})

    def recorrer(el, a):
        for h in el:
            tag = h.tag.split('}')[-1]
            ah = heredar(h, a)
            if tag == 'g':
                recorrer(h, ah); continue
            if tag == 'rect':
                w, hh = num(h.get('width')), num(h.get('height'))
                if h.get('width', '').endswith('%'): continue
                rx = num(h.get('rx'))
                st = (f"rounded={1 if rx else 0};absoluteArcSize=1;arcSize={rx*2*S:.0f};whiteSpace=wrap;html=1;"
                      f"fillColor={color(ah.get('fill'))};" + (estilo_trazo(ah) if ah.get('stroke') else 'strokeColor=none;'))
                dib.vertice('', st, num(h.get('x')), num(h.get('y')), w, hh)
            elif tag in ('circle', 'ellipse'):
                cx, cy = num(h.get('cx')), num(h.get('cy'))
                rx = num(h.get('r') or h.get('rx')); ry = num(h.get('r') or h.get('ry'))
                st = (f"ellipse;whiteSpace=wrap;html=1;fillColor={color(ah.get('fill'))};"
                      + (estilo_trazo(ah) if ah.get('stroke') else 'strokeColor=none;'))
                dib.vertice('', st, cx - rx, cy - ry, 2 * rx, 2 * ry)
            elif tag == 'line':
                pts = [(num(h.get('x1')), num(h.get('y1'))), (num(h.get('x2')), num(h.get('y2')))]
                dib.arista(pts, 'html=1;rounded=0;' + estilo_trazo(ah) + flechas(h, ah))
            elif tag == 'polygon':
                p = [float(v) for v in re.findall(r'-?\d*\.?\d+', h.get('points'))]
                pts = list(zip(p[::2], p[1::2]))
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                x0, y0, w, hh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
                forma = 'rhombus;' if len(pts) == 4 else 'shape=hexagon;'
                st = f"{forma}whiteSpace=wrap;html=1;fillColor={color(ah.get('fill'))};" + estilo_trazo(ah)
                dib.vertice('', st, x0, y0, w, hh)
            elif tag == 'path':
                relleno = color(ah.get('fill'))
                for pts, cerr in puntos_path(h.get('d')):
                    if len(pts) < 2: continue
                    if relleno != 'none' and (cerr or pts[0] == pts[-1]):
                        # Figura rellena: polígono con forma propia de draw.io (shape=stencil no hace falta: se usa un SVG embebido)
                        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                        x0, y0, w, hh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
                        pd = 'M' + ' L'.join(f'{px-x0:.1f} {py-y0:.1f}' for px, py in pts) + ' Z'
                        sv = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.1f}" height="{hh:.1f}" viewBox="0 0 {w:.1f} {hh:.1f}">'
                              f'<path d="{pd}" fill="{relleno}" stroke="{color(ah.get("stroke"))}" stroke-width="{num(ah.get("stroke-width"),1)}"/></svg>')
                        b64 = base64.b64encode(sv.encode()).decode()
                        dib.vertice('', f'shape=image;html=1;imageAspect=0;aspect=fixed;image=data:image/svg+xml,{b64};', x0, y0, w, hh)
                    else:
                        if relleno != 'none' and ah.get('stroke') in (None, 'none'):
                            ah = dict(ah); ah['stroke'] = relleno
                        dib.arista(pts, 'html=1;rounded=0;' + estilo_trazo(ah) + flechas(h, ah))
            elif tag == 'text':
                partes = []
                for nodo in [h] + list(h):
                    t = (nodo.text or '') if nodo is h else (nodo.text or '') + ''
                    if nodo is not h:
                        b = 'bold' in (nodo.get('font-weight') or '') or nodo.get('font-weight') in ('600', '700')
                        partes.append((t, b)); partes.append((nodo.tail or '', False))
                    else:
                        partes.append((t, False))
                texto = ''.join(p for p, _ in partes).strip()
                if not texto: continue
                fs = num(ah.get('font-size'), 10)
                negrita = str(ah.get('font-weight', '')) in ('bold', '600', '650', '700', '800')
                valor = ''.join(f'<b>{html.escape(p)}</b>' if b else html.escape(p) for p, b in partes).strip()
                w = ancho_texto(texto, fs); hh = fs * 1.35
                anc = ah.get('text-anchor', 'start')
                x = num(h.get('x')); y = num(h.get('y'))
                x0 = x if anc == 'start' else x - w / 2 if anc == 'middle' else x - w
                al = {'start': 'left', 'middle': 'center', 'end': 'right'}[anc]
                mono = 'Mono' in (ah.get('font-family') or '')
                st = (f"text;html=1;whiteSpace=nowrap;align={al};verticalAlign=middle;spacing=0;"
                      f"fontSize={fs*S:.1f};fontColor={color(ah.get('fill'))};fontStyle={1 if negrita else 0};"
                      + ('fontFamily=Courier New;' if mono else ''))
                rot = re.search(r'rotate\((-?[\d.]+)', h.get('transform') or '')
                meta = {'cx': x0 + w / 2, 'cy': y - fs * 0.35, 'ancho': w, 'al': al, 'fs': fs, 'negrita': negrita,
                        'color': color(ah.get('fill')), 'mono': mono, 'rot': bool(rot)}
                if rot:
                    st += f'rotation={rot.group(1)};'
                    x0 = x - w / 2  # la caja rota alrededor de su centro
                    dib.vertice(valor, st, x0, y - hh / 2, w, hh, meta)
                else:
                    dib.vertice(valor, st, x0, y - fs * 1.0, w, hh, meta)

    recorrer(raiz, base)
    return dib.xml(titulo, vb[2], vb[3], fondo)


import os
os.makedirs(SALIDA, exist_ok=True)
for i, (nombre, titulo) in FIGURAS.items():
    xml = convertir(svgs[i], titulo, '#1f3b31' if i == 0 else None)  # el esquema de la portada va sobre fondo oscuro
    ET.fromstring(xml)  # valida que el XML esté bien formado
    open(f'{SALIDA}/{nombre}.drawio', 'w', encoding='utf-8').write(xml)
    print(f'{nombre}.drawio', xml.count('<mxCell') - 2, 'celdas')
