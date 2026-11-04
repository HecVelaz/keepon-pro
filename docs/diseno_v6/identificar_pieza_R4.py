import sys,json
sys.path.insert(0,'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
from sw_connect import connect_solidworks,get_com_member as leer
sw,_=connect_solidworks(version=2021,wait_seconds=10)
salida=[]
for d in leer(sw,'GetDocuments') or []:
    if leer(d,'GetType')!=1 or 'v6_grupo_' not in str(leer(d,'GetTitle')):continue
    f=leer(d,'FirstFeature')
    while f is not None:
        nombre=str(leer(f,'Name'))
        if '4.3-1-solid1' in nombre or '4.2-1-solid1' in nombre:
            item={'documento':leer(d,'GetTitle'),'operacion':nombre}
            try:
                caras=leer(f,'GetFaces') or [];item['cuerpos']=[]
                for cara in caras[:1]:
                    b=leer(cara,'GetBody');item['cuerpos'].append({'nombre':leer(b,'Name'),'caja_mm':[x*1000 for x in leer(b,'GetBodyBox')]})
            except Exception as e:item['error']=str(e)
            salida.append(item)
        f=leer(f,'GetNextFeature')
print(json.dumps(salida,ensure_ascii=True,indent=2))
