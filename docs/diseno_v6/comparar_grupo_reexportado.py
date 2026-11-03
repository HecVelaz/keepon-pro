"""Localiza la diferencia OCCT/SolidWorks por sólido del grupo roll."""
from pathlib import Path
import json
import cadquery as cq

R=Path(__file__).resolve().parent
fuente=cq.importers.importStep(str(R/'STEP_V6/v6_grupo_roll.step')).val().Solids()
destino=cq.importers.importStep(str(R/'evidencias/solidworks_v6/roll_reexportado.step')).val().Solids()
refs=[p for p in json.loads((R/'evidencias/cuerpos_v6.json').read_text()) if p['grupo']=='roll']
def bb(s):
    b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def dist(a,b):return max(abs(x-y) for x,y in zip(a,b))
filas=[]
for a in fuente:
    ca=bb(a);ref=min(refs,key=lambda p:dist(ca,p['caja_mm']));refs.remove(ref)
    b=min(destino,key=lambda s:dist(ca,bb(s)));destino.remove(b)
    filas.append({'nombre':ref['nombre'],'volumen_occt_mm3':a.Volume(),'volumen_reexportado_mm3':b.Volume(),
                  'delta_mm3':b.Volume()-a.Volume(),'error_caja_mm':dist(ca,bb(b))})
d={'cuerpos':filas,'delta_total_reexportado_mm3':sum(p['delta_mm3'] for p in filas)}
(R/'evidencias/solidworks_v6/comparacion_roll_por_cuerpo.json').write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(sorted(filas,key=lambda p:abs(p['delta_mm3']),reverse=True)[:6],ensure_ascii=False))
