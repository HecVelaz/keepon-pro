import sys,json
sys.path.insert(0,'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
from sw_connect import connect_solidworks,get_com_member as leer
sw,_=connect_solidworks(version=2021,wait_seconds=10)
docs=leer(sw,'GetDocuments') or []
r=[]
for d in docs:
    dato={'titulo':leer(d,'GetTitle'),'ruta':leer(d,'GetPathName'),'tipo':leer(d,'GetType')}
    try:
        sm=leer(d,'SelectionManager');n=leer(sm,'GetSelectedObjectCount2',-1);dato['seleccion']=[]
        for i in range(1,n+1):
            ob=leer(sm,'GetSelectedObject6',i,-1);x={'tipo':leer(sm,'GetSelectedObjectType3',i,-1)}
            for atr in ('Name','Name2','GetName','GetTypeName2'):
                try:x[atr]=str(leer(ob,atr))
                except Exception:pass
            try:x['caja']=list(leer(ob,'GetBodyBox'))
            except Exception:pass
            dato['seleccion'].append(x)
    except Exception as e:dato['error']=str(e)
    r.append(dato)
print(json.dumps(r,ensure_ascii=True,indent=2))
