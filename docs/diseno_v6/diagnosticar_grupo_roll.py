"""Diagnóstico de volumen del grupo roll convertido por SolidWorks."""
from pathlib import Path
import json
import sys
sys.path.insert(0,'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
from sw_connect import connect_solidworks,open_document,save_document,get_com_member as leer

R=Path(__file__).resolve().parent
sw,_=connect_solidworks(version=2021,wait_seconds=30)
iniciales=list(leer(sw,'GetDocuments') or [])
sw.UserControl=True
m=open_document(sw,str(R/'SOLIDWORKS_V6/v6_grupo_roll.SLDPRT'),raise_on_error=True)
antes=float(leer(leer(m.Extension,'CreateMassProperty'),'Volume'))*1e9
m.ClearSelection2(True)
despues=float(leer(leer(m.Extension,'CreateMassProperty'),'Volume'))*1e9
d={'antes_mm3':antes,'despues_seleccion_limpia_mm3':despues,
   'cuerpos':len(leer(m,'GetBodies2',0,False) or []),'esperado':json.loads((R/'evidencias/volumenes_grupos_v6.json').read_text())['roll']}
refs=[p for p in json.loads((R/'evidencias/cuerpos_v6.json').read_text()) if p['grupo']=='roll']
fuentes=json.loads((R/'evidencias/solidworks_v6/comparacion_roll_por_cuerpo.json').read_text())['cuerpos'] if (R/'evidencias/solidworks_v6/comparacion_roll_por_cuerpo.json').is_file() else []
filas=[]
for b in leer(m,'GetBodies2',0,False) or []:
    caja=[float(x)*1000 for x in leer(b,'GetBodyBox')]
    ref=min(refs,key=lambda p:max(abs(x-y) for x,y in zip(caja,p['caja_mm'])));refs.remove(ref)
    # IBody2.GetMassProperties(density) devuelve volumen en el índice3, SI.
    # Firma contrastada en la documentación oficial de SOLIDWORKS API.
    volumen=list(leer(b,'GetMassProperties',1.0))[3]*1e9
    fuente=next((p['volumen_occt_mm3'] for p in fuentes if p['nombre']==ref['nombre']),None)
    filas.append({'nombre':ref['nombre'],'volumen_sw_mm3':volumen,'volumen_occt_mm3':fuente,
                  'delta_mm3':volumen-fuente if fuente is not None else None})
d['volumenes_por_cuerpo']=filas
assert save_document(m,str(R/'evidencias/solidworks_v6/roll_reexportado.step'))
(R/'evidencias/solidworks_v6/diagnostico_roll.json').write_text(json.dumps(d,indent=2),encoding='utf-8')
print({**{k:v for k,v in d.items() if k!='volumenes_por_cuerpo'},'mayores_diferencias':sorted(filas,key=lambda p:abs(p['delta_mm3'] or 0),reverse=True)[:5]},flush=True)
sw.CloseDoc(leer(m,'GetTitle'))
if not iniciales:sw.ExitApp()
