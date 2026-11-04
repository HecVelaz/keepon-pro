"""Vistas reales del CAD R2: ojos, dos pasos traseros y fijación del PCB."""
from pathlib import Path
import importlib.util
import json
import zipfile

R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('vistas_r2',R.parent/'diseno_v3_simple/render_v3.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);r.OUT=R/'vistas'
actual=json.loads((R/'mallas_v6.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(R/'HISTORIAL/Keepon_V6_antes_R2.zip') as z:
    previo=json.loads(z.read('diseno_v6/mallas_v6.json'))
fig=r.page('V6 R2 · ojos WALL-E, doble abertura y soporte RLBZ23',
    'Piezas oculares pegables · Retirada la tapa14 · PCB medido de13 ×31,8 ×1,5 mm',size=(15,12))
for x,titulo,datos in [(.04,'OJOS ANTERIORES',previo),(.52,'OJOS R2',actual)]:
    ax=fig.add_axes([x,.51,.43,.33]);grupo=[m for m in datos if m['group']=='roll']
    r.render(ax,grupo,elev=0,azim=0,framing=((-45,-65,105),(78,65,214)))
    fig.text(x+.01,.85,titulo,fontsize=15,weight='bold',color=r.INK)
ax=fig.add_axes([.04,.11,.43,.28])
r.render(ax,[m for m in actual if m['group'] in ('pitch','roll')],elev=0,azim=180)
fig.text(.05,.43,'Dos pasos traseros iguales, sin tapa ni sus M3',fontsize=13,weight='bold',color=r.INK)
ax=fig.add_axes([.52,.11,.43,.28])
seleccion=[m for m in actual if m['name'] in ('15_soporte_RLBZ23','21_arandela_buzzer','REF_RLBZ23_PCB','REF_M3_buzzer_PCB')]
r.render(ax,seleccion,elev=18,azim=30)
fig.text(.53,.43,'Soporte lateral: PCB completo y fijación M3×5',fontsize=13,weight='bold',color=r.INK)
fig.text(.53,.075,'Sólo se representa el PCB: componentes y pines pendientes de medir.',fontsize=10,color=r.MUTED)
r.save(fig,'06_R2_ojos_USB_buzzer.png',
    'Geometría CAD de revisión. La referencia de WALL-E inspira las carcasas; las lentes impresas son decorativas. Ajustes físicos pendientes.')
