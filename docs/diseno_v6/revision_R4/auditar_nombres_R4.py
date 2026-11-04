"""Auditoría de cuerpos/operaciones en los documentos R4 abiertos, sólo lectura."""
from pathlib import Path
import sys,json
R=Path(__file__).parent
sys.path.insert(0,'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
from sw_connect import connect_solidworks,get_com_member as leer

def main():
    sw,_=connect_solidworks(version=2021,wait_seconds=10);datos=[]
    for d in leer(sw,'GetDocuments') or []:
        p=Path(str(leer(d,'GetPathName')))
        if p.parent!=(R/'SOLIDWORKS_R4').resolve() or leer(d,'GetType')!=1:continue
        cuerpos=[str(leer(b,'Name')) for b in leer(d,'GetBodies2',0,False) or []]
        assert len(set(n.casefold() for n in cuerpos))==len(cuerpos),(p.name,'Nombres de cuerpos duplicados')
        nombres=[];visitados=set()
        def cadena(f,siguiente):
            while f is not None:
                n=str(leer(f,'Name'))
                if n not in visitados:
                    visitados.add(n);nombres.append(n)
                    sub=leer(f,'GetFirstSubFeature')
                    if sub is not None:cadena(sub,'GetNextSubFeature')
                f=leer(f,siguiente)
        cadena(leer(d,'FirstFeature'),'GetNextFeature')
        prohibidos=[n for n in cuerpos+nombres if 'Open CASCADE' in n]
        assert not prohibidos,(p.name,prohibidos)
        datos.append({'archivo':p.name,'cuerpos':cuerpos,'operaciones':nombres,'nombres_importados_restantes':prohibidos})
    assert len(datos)==4,f'Se esperaban los cuatro grupos abiertos: {len(datos)}'
    (R/'evidencias/solidworks_R4/nombres_verificados.json').write_text(json.dumps({'grupos':datos,'aprobado':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Cuatro grupos: cuerpos y operaciones sin nombres Open CASCADE',flush=True)

if __name__=='__main__':main()
