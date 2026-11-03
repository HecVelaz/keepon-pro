"""Comparación geométrica de la revisión USB solicitada en las capturas."""
from pathlib import Path
import importlib.util
import json
import zipfile

R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('vistas_usb',R.parent/'diseno_v3_simple/render_v3.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.OUT=R/'vistas'
actual=json.loads((R/'mallas_v6.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(R/'HISTORIAL/Keepon_V6_antes_USB_R1.zip') as z:
    anterior=json.loads(z.read('diseno_v6/mallas_v6.json'))

def cabeza(datos):
    return [m for m in datos if m['group'] in ('pitch','roll')]

fig=r.page('V6 · paso USB y soporte de roll corregidos',
    'Abertura en el lado marcado · Dos alivios semicirculares · Material adicional por arriba',size=(15,11))
encuadre=((-105,-100,103),(76,100,216))
for x,titulo,datos in [(.04,'ANTES',anterior),(.52,'REVISIÓN USB R1',actual)]:
    ax=fig.add_axes([x,.54,.43,.30])
    r.render(ax,cabeza(datos),elev=0,azim=180,framing=encuadre)
    fig.text(x+.01,.85,titulo,fontsize=15,weight='bold',color=r.INK)
ax=fig.add_axes([.04,.12,.43,.31])
r.render(ax,[m for m in actual if m['name']=='03_cuna_pitch'],elev=8,azim=180)
fig.text(.05,.45,'Cuna 03: recortes R26/R20 y +26 mm arriba',fontsize=14,weight='bold',color=r.INK)
ax=fig.add_axes([.52,.12,.43,.31])
r.render(ax,[m for m in actual if m['name']=='04_cuba_cabeza'],elev=0,azim=180)
fig.text(.53,.45,'Cuba 04: paso 36 × 26 mm, esquinas R3',fontsize=14,weight='bold',color=r.INK)
fig.text(.53,.093,'Marco interior de refuerzo; abertura inferior a la derecha en esta vista.',fontsize=10,color=r.MUTED)
r.save(fig,'05_USB_R1_comparacion.png',
    'Cotas de diseño configurables. Falta medir el enchufe USB y su cable; no se certifica aún el ajuste físico ni la resistencia.')
