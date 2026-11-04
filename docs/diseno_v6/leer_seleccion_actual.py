import sys,json,tempfile
from pathlib import Path
sys.path.insert(0,'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
from sw_connect import connect_solidworks,get_com_member as leer
from PIL import Image
sw,_=connect_solidworks(version=2021,wait_seconds=10)
m=next(d for d in leer(sw,'GetDocuments') if leer(d,'GetTitle')=='Keepon_V6_R4')
sm=leer(m,'SelectionManager');salida=[]
for i in range(1,leer(sm,'GetSelectedObjectCount2',-1)+1):
    ob=leer(sm,'GetSelectedObject6',i,-1);t=leer(sm,'GetSelectedObjectType3',i,-1);a={'indice':i,'tipo':t}
    try:
        cuerpo=leer(ob,'GetBody');a['cuerpo']=str(leer(cuerpo,'Name'))
    except Exception:pass
    try:a['caja_mm']=[x*1000 for x in leer(ob,'GetBox')]
    except Exception:pass
    try:a['punto_mm']=[x*1000 for x in leer(ob,'GetPoint')]
    except Exception:pass
    salida.append(a)
p=Path(tempfile.gettempdir())/'seleccion_trasera_cara_R4.bmp';assert m.SaveBMP(str(p),1600,1000)
Image.open(p).save(p.with_suffix('.png'))
print(json.dumps(salida,ensure_ascii=True,indent=2));print(p.with_suffix('.png'))
